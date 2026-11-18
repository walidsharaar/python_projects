"""Step 4.2: won is not activated. Which signed sellers actually start selling?

Run from the project root (after src\\warehouse.py):
    python analysis\\02_win_vs_activation.py

Population: won sellers with a full 90-day window (fair comparison).

Questions for Sales enablement:
    1. Which deal attributes go together with activation?   (one at a time)
    2. Which of them still matter when we look at all together? (logistic regression)
    3. Where does the GMV come from?                         (value, not just yes/no)
    4. Do sales reps differ, once we account for their lead mix? (observed vs expected)

Caveat: lead_type and business_type are recorded by Sales during the deal.
We assume they are known before the contract is signed, so they can be used
for qualification. That should be confirmed with the Sales team.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from stats_utils import bootstrap_mean_ci, chi_square, rate_table, wilson

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "02_win_vs_activation.md"
# Result table for the dashboard (the statistics are done here, not in the dashboard)
RESULT = ROOT / "data" / "results" / "lead_types.parquet"
MIN_N = 30


def load() -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = con.execute("""
            SELECT s.seller_id, s.sr_id, s.lead_type, s.business_type,
                   l.lead_behaviour_profile, l.sales_cycle_days,
                   s.is_activated, s.days_to_first_sale, s.gmv_90d
            FROM fct_seller_activation AS s
            JOIN fct_leads AS l USING (mql_id)          -- one seller : one lead
            WHERE s.has_full_90d_window
              AND NOT l.dq_negative_sales_cycle
        """).df()

    # Small or missing groups are merged, so the model has enough data per group.
    small = df["lead_type"].value_counts()
    small = small[small < MIN_N].index
    df["lead_group"] = df["lead_type"].where(~df["lead_type"].isin(small) & df["lead_type"].notna(),
                                             "other_or_missing")
    df["business_type"] = df["business_type"].fillna("missing")
    df["cycle_bucket"] = pd.cut(df["sales_cycle_days"], [-1, 7, 30, 10_000],
                                labels=["0-7 days", "8-30 days", "over 30 days"]).astype(str)
    df["activated"] = df["is_activated"].astype(int)
    return df


def fmt_rates(t: pd.DataFrame, group: str) -> list[str]:
    lines = [f"  {group:<20}{'n':>5}{'activation':>12}{'95% CI':>13}"]
    for r in t.itertuples():
        mark = "  (small)" if r.small else ""
        lines.append(f"  {str(getattr(r, group)):<20}{r.n:>5}{r.rate:>12.0%}"
                     f"{f'{r.ci_low:.0%}-{r.ci_high:.0%}':>13}{mark}")
    return lines


def one_at_a_time(df: pd.DataFrame) -> list[str]:
    out = []
    for group in ["lead_group", "business_type", "cycle_bucket", "lead_behaviour_profile"]:
        chi2, dof, p = chi_square(df.fillna({group: "missing"}), group, "activated")
        out.append(f"\n{group}: chi2 = {chi2:.1f}, df = {dof}, p = {p:.2g}")
        out += fmt_rates(rate_table(df.fillna({group: "missing"}), group, "activated", MIN_N), group)
    return out


def all_together(df: pd.DataFrame) -> list[str]:
    """Logistic regression: each attribute's effect, holding the others equal.

    Odds ratio (OR) = how the odds of activating change compared with the
    reference group. OR 2.0 = twice the odds. OR 0.5 = half the odds.
    If the 95 % interval includes 1.0, we cannot tell it apart from no effect.
    """
    model = smf.logit(
        "activated ~ C(lead_group, Treatment('online_medium'))"
        " + C(business_type, Treatment('reseller'))"
        " + C(cycle_bucket, Treatment('0-7 days'))",
        data=df,
    ).fit(disp=False)

    ci = np.exp(model.conf_int())
    out = [f"  Reference: online_medium, reseller, closed in 0-7 days. n = {int(model.nobs)}, "
           f"pseudo R2 = {model.prsquared:.3f}",
           f"  {'attribute':<38}{'odds ratio':>11}{'95% CI':>15}{'p':>8}"]
    for name in model.params.index.drop("Intercept"):
        label = name.split("[T.")[1].rstrip("]")
        clean = ("lead_type = " if "lead_group" in name else
                 "business_type = " if "business_type" in name else "sales cycle = ") + label
        out.append(f"  {clean:<38}{np.exp(model.params[name]):>11.2f}"
                   f"{f'{ci.loc[name, 0]:.2f}-{ci.loc[name, 1]:.2f}':>15}{model.pvalues[name]:>8.3f}")
    return out


def value(df: pd.DataFrame) -> list[str]:
    total = df["gmv_90d"].sum()
    out = [f"  {'lead_type':<20}{'sellers':>8}{'% sellers':>10}{'% GMV':>8}"
           f"{'GMV mean':>10}{'95% CI (bootstrap)':>20}"]
    g = df.groupby("lead_group")
    for name, grp in sorted(g, key=lambda x: -x[1]["gmv_90d"].sum()):
        low, high = bootstrap_mean_ci(grp["gmv_90d"].to_numpy())
        out.append(f"  {name:<20}{len(grp):>8}{len(grp) / len(df):>10.0%}"
                   f"{grp['gmv_90d'].sum() / total:>8.0%}{grp['gmv_90d'].mean():>10,.0f}"
                   f"{f'{low:,.0f}-{high:,.0f}':>20}")
    return out


def sales_reps(df: pd.DataFrame) -> list[str]:
    """Observed vs expected activation per sales rep (SR).

    Expected = what the rep would reach if each of their sellers activated
    at the average rate of its lead_type. A rep with many 'offline' leads
    gets a lower expectation. That makes the comparison fair.
    """
    avg_by_type = df.groupby("lead_group")["activated"].mean()
    df = df.assign(expected=df["lead_group"].map(avg_by_type))
    reps = df.groupby("sr_id").agg(n=("activated", "size"), observed=("activated", "mean"),
                                   expected=("expected", "mean"), yes=("activated", "sum"))
    reps = reps[reps["n"] >= 20].sort_values("observed")
    chi2, dof, p = chi_square(df[df["sr_id"].isin(reps.index)], "sr_id", "activated")

    out = [f"  Reps with >= 20 sellers: {len(reps)}. Do they differ? chi2 = {chi2:.1f}, "
           f"df = {dof}, p = {p:.2f}",
           f"  {'rep (shortened id)':<20}{'n':>5}{'observed':>10}{'expected':>10}{'diff':>7}{'95% CI':>13}"]
    for rep, r in reps.iterrows():
        low, high = wilson(int(r["yes"]), int(r["n"]))
        inside = "" if low <= r["expected"] <= high else "  <- outside CI"
        out.append(f"  {rep[:8]:<20}{int(r['n']):>5}{r['observed']:>10.0%}{r['expected']:>10.0%}"
                   f"{r['observed'] - r['expected']:>+7.0%}{f'{low:.0%}-{high:.0%}':>13}{inside}")
    return out


def lead_type_results(df: pd.DataFrame) -> pd.DataFrame:
    """One row per lead type: activation with Wilson interval, share of sellers and of GMV.

    Only exact calculations, no bootstrap, so the evidence report is not affected.
    """
    g = df.groupby("lead_group").agg(sellers=("activated", "size"), activated=("activated", "sum"),
                                     gmv=("gmv_90d", "sum")).reset_index()
    g["activation_rate"] = g["activated"] / g["sellers"]
    g[["ci_low", "ci_high"]] = [wilson(a, n) for a, n in zip(g["activated"], g["sellers"])]
    g["seller_share"] = g["sellers"] / g["sellers"].sum()
    g["gmv_share"] = g["gmv"] / g["gmv"].sum()
    g["is_small"] = g["sellers"] < MIN_N
    return g


def main() -> None:
    df = load()
    low, high = wilson(int(df["activated"].sum()), len(df))
    sections = {
        "Population": [f"  {len(df)} won sellers with a full 90-day window, "
                       f"{df['activated'].mean():.1%} activated (95% CI {low:.0%}-{high:.0%})"],
        "1. One attribute at a time": one_at_a_time(df),
        "2. All attributes together (logistic regression)": all_together(df),
        "3. Where the 90-day GMV comes from": value(df),
        "4. Sales reps: observed vs expected activation": sales_reps(df),
    }

    for title, lines in sections.items():
        print(f"\n{title}")
        print("\n".join(lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Evidence: won vs activated (Step 4.2)", "",
          "Generated by `analysis/02_win_vs_activation.py`. Evidence only; "
          "the recommendation is in README section 9.", ""]
    for title, lines in sections.items():
        md += [f"## {title}", "", "```text", *lines, "```", ""]
    OUTPUT.write_text("\n".join(md), encoding="utf-8")
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    lead_type_results(df).to_parquet(RESULT, index=False)
    print(f"Saved: {RESULT.relative_to(ROOT)}")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
