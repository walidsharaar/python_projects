"""Step 4.1: channel quality. Which channels bring sellers who actually sell?

The script only collects EVIDENCE. The recommendation is written by a
person, after looking at the evidence (README, section 9).

Funnel per channel, three stages:
    Stage 1  lead  -> won deal       (do the leads close?)
    Stage 2  won   -> activated      (do the sellers start selling?)
    Stage 3  activated -> GMV        (how much do they sell in 90 days?)
    Combined: activated sellers per 1,000 leads

Fair comparison rules (from the KPI layer):
    - Stage 1 uses only lead cohorts with complete deal tracking (2018),
      because deals before 5 Dec 2017 were not recorded.
    - Stages 2 and 3 use only sellers with a full 90-day window.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportion_confint, proportions_ztest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "01_channel_quality.md"

MIN_LEADS = 100      # below this, a channel's win rate is too uncertain to rank
MIN_SELLERS = 30     # below this, activation and GMV are too uncertain to rank
RNG = np.random.default_rng(42)   # fixed seed: same bootstrap result every run


def load(con) -> tuple[pd.DataFrame, pd.DataFrame]:
    leads = con.execute("""
        SELECT l.origin, l.is_won_within_60d
        FROM fct_leads AS l
        JOIN mart_gtm_monthly AS m USING (cohort_month)
        WHERE m.deal_tracking_complete            -- fair cohorts only
    """).df()
    sellers = con.execute("""
        SELECT origin, is_activated, gmv_90d
        FROM fct_seller_activation
        WHERE has_full_90d_window                 -- fair window only
    """).df()
    return leads, sellers


def wilson(successes: int, n: int) -> tuple[float, float]:
    low, high = proportion_confint(successes, n, alpha=0.05, method="wilson")
    return float(low), float(high)


def bootstrap_mean_ci(values: np.ndarray, n_boot: int = 5_000) -> tuple[float, float]:
    """Resample the sellers many times and see how much the mean moves.

    With very skewed data (one seller = 59 % of a channel's GMV), the
    normal formula for a confidence interval does not work well. The
    bootstrap makes no assumption about the shape of the data.
    """
    samples = RNG.choice(values, size=(n_boot, len(values)), replace=True)
    means = samples.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def stage_1(leads: pd.DataFrame) -> pd.DataFrame:
    g = leads.groupby("origin")["is_won_within_60d"].agg(leads="size", won="sum").reset_index()
    g["win_rate"] = g["won"] / g["leads"]
    g[["win_ci_low", "win_ci_high"]] = [wilson(w, n) for w, n in zip(g["won"], g["leads"])]
    return g


def stage_2_3(sellers: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for origin, grp in sellers.groupby("origin"):
        n, act = len(grp), int(grp["is_activated"].sum())
        gmv = grp["gmv_90d"].to_numpy()
        low, high = wilson(act, n)
        row = {"origin": origin, "sellers": n, "activated": act,
               "activation_rate": act / n, "act_ci_low": low, "act_ci_high": high,
               "gmv_mean": gmv.mean(), "gmv_median": np.median(gmv),
               "top_seller_share": gmv.max() / gmv.sum() if gmv.sum() > 0 else np.nan}
        if n >= MIN_SELLERS:
            row["gmv_ci_low"], row["gmv_ci_high"] = bootstrap_mean_ci(gmv)
        rows.append(row)
    return pd.DataFrame(rows)


def tests(leads: pd.DataFrame, sellers: pd.DataFrame, s1: pd.DataFrame) -> list[str]:
    """A few tests, chosen for the business questions, not for every pair.

    Testing all 55 channel pairs would almost guarantee some 'significant'
    result by chance (multiple testing, see landing pages in part 3).
    """
    out = []

    #  Do the larger channels differ at all? (chi-square test of independence)
    big = s1.loc[s1["leads"] >= MIN_LEADS, "origin"]
    table = pd.crosstab(leads.loc[leads["origin"].isin(big), "origin"],
                        leads.loc[leads["origin"].isin(big), "is_won_within_60d"])
    chi2, p, dof, _ = chi2_contingency(table)
    out.append(f"Win rate differs between the {len(big)} larger channels: "
               f"chi2 = {chi2:.1f}, df = {dof}, p = {p:.2g}")

    # Pairwise questions that a stakeholder would really ask
    for a, b in [("paid_search", "organic_search"), ("unknown", "organic_search")]:
        x = leads[leads["origin"].isin([a, b])].groupby("origin")["is_won_within_60d"].agg(["sum", "size"]).loc[[a, b]]
        _, p = proportions_ztest(x["sum"].to_numpy(), x["size"].to_numpy())
        r = x["sum"] / x["size"]
        out.append(f"Win rate     {a:<15} {r[a]:.1%} vs {b:<15} {r[b]:.1%}   p = {p:.3f}")

    x = sellers[sellers["origin"].isin(["paid_search", "organic_search"])] \
        .groupby("origin")["is_activated"].agg(["sum", "size"]).loc[["paid_search", "organic_search"]]
    _, p = proportions_ztest(x["sum"].to_numpy(), x["size"].to_numpy())
    r = x["sum"] / x["size"]
    out.append(f"Activation   {'paid_search':<15} {r['paid_search']:.1%} vs "
               f"{'organic_search':<15} {r['organic_search']:.1%}   p = {p:.3f}")
    return out


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        leads, sellers = load(con)

    s1 = stage_1(leads)
    s23 = stage_2_3(sellers)
    df = s1.merge(s23, on="origin", how="left")

    # Combined funnel metric: robust, because it does not depend on GMV outliers
    df["activated_per_1000_leads"] = 1000 * df["win_rate"] * df["activation_rate"]
    df["rankable"] = (df["leads"] >= MIN_LEADS) & (df["sellers"] >= MIN_SELLERS)
    df = df.sort_values("activated_per_1000_leads", ascending=False)

    pct = lambda v: "-" if pd.isna(v) else f"{v:.0%}"
    num = lambda v: "-" if pd.isna(v) else f"{v:,.0f}"
    lines = []
    header = (f"{'origin':<18}{'leads':>6}{'win 60d':>9}{'95% CI':>13}"
              f"{'sellers':>8}{'activ.':>7}{'95% CI':>11}"
              f"{'GMV mean':>9}{'95% CI (bootstrap)':>20}{'median':>7}{'top 1':>6}{'act./1000':>10}")
    lines.append(header)
    for r in df.itertuples():
        ci_win = f"{r.win_ci_low:.0%}-{r.win_ci_high:.0%}"
        ci_act = "-" if pd.isna(r.act_ci_low) else f"{r.act_ci_low:.0%}-{r.act_ci_high:.0%}"
        ci_gmv = "-" if pd.isna(getattr(r, "gmv_ci_low", np.nan)) else f"{r.gmv_ci_low:,.0f}-{r.gmv_ci_high:,.0f}"
        mark = "" if r.rankable else "  (too small to rank)"
        lines.append(f"{r.origin:<18}{r.leads:>6,}{r.win_rate:>9.1%}{ci_win:>13}"
                     f"{num(r.sellers):>8}{pct(r.activation_rate):>7}{ci_act:>11}"
                     f"{num(r.gmv_mean):>9}{ci_gmv:>20}{num(r.gmv_median):>7}"
                     f"{pct(r.top_seller_share):>6}{num(r.activated_per_1000_leads):>10}{mark}")

    test_lines = tests(leads, sellers, s1)

    # Share of the funnel we cannot attribute (tracking question, H2)
    untracked = df[df["origin"].isin(["unknown", "not_tracked"])]
    lines_extra = [
        f"Leads without a usable channel (2018 cohorts): {untracked['leads'].sum():,} "
        f"of {df['leads'].sum():,} ({untracked['leads'].sum() / df['leads'].sum():.1%})",
        f"Their share of 60-day wins: {untracked['won'].sum():,} of {df['won'].sum():,} "
        f"({untracked['won'].sum() / df['won'].sum():.1%})",
    ]

    print("\nChannel funnel (2018 lead cohorts; sellers with full 90-day window)\n")
    print("\n".join(lines))
    print("\nStatistical tests")
    print("\n".join("  " + t for t in test_lines))
    print("\nTracking")
    print("\n".join("  " + t for t in lines_extra))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join([
        "# Evidence: channel quality (Step 4.1)", "",
        "Generated by `analysis/01_channel_quality.py`. Evidence only; "
        "the recommendation is in README section 9.", "",
        "## Channel funnel", "", "```text", *lines, "```", "",
        "## Statistical tests", "", *[f"- {t}" for t in test_lines], "",
        "## Tracking", "", *[f"- {t}" for t in lines_extra], "",
    ]), encoding="utf-8")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
