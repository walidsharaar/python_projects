"""Step 4.3: landing pages. Which pages really convert better or worse?



Population: leads from 2018 cohorts (complete deal tracking).

Two traps this script protects against:
    1. Confounding: most pages get their traffic from one channel.
       A "bad" page may just be a social page, and social leads close
       less everywhere. So each page is compared with what its CHANNEL
       MIX predicts, not with the overall average.
    2. Multiple testing: with 18 tests at the 5 % level, about one
       false "significant" result is expected by chance alone. The
       Benjamini-Hochberg correction keeps the share of false
       discoveries among the results at about 5 %.
"""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import binomtest
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest

from stats_utils import chi_square, wilson

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "03_landing_pages.md"
# Result table for the dashboard (the statistics are done here, not in the dashboard)
RESULT = ROOT / "data" / "results" / "landing_pages.parquet"
MIN_LEADS = 50
UNTRACKED = ["unknown", "not_tracked"]


def load() -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = con.execute("""
            SELECT l.landing_page_id, l.origin, l.is_won_within_60d
            FROM fct_leads AS l
            JOIN mart_gtm_monthly AS m USING (cohort_month)
            WHERE m.deal_tracking_complete
        """).df()
    df["won"] = df["is_won_within_60d"].astype(int)
    df["page"] = df["landing_page_id"].str[:8]        # shortened id for reading
    # Expected chance to close, based only on the lead's channel
    df["expected"] = df["origin"].map(df.groupby("origin")["won"].mean())
    return df


def concentration(df: pd.DataFrame) -> list[str]:
    per_page = df.groupby("page").size().sort_values(ascending=False)
    big = per_page[per_page >= MIN_LEADS]
    return [
        f"  Pages with at least one lead:      {len(per_page):,}",
        f"  Pages with only one lead:          {(per_page == 1).sum():,}",
        f"  Pages with >= {MIN_LEADS} leads:            {len(big)} "
        f"({big.sum() / per_page.sum():.0%} of all leads)",
        f"  Top 2 pages:                       {per_page.iloc[:2].sum() / per_page.sum():.0%} of all leads",
    ]


def page_tests(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    big = df.groupby("page").filter(lambda g: len(g) >= MIN_LEADS)
    for page, grp in big.groupby("page"):
        rest = df[df["page"] != page]
        n, won = len(grp), int(grp["won"].sum())
        expected_rate = grp["expected"].mean()

        # Naive: page vs all other pages (ignores the channel)
        _, p_naive = proportions_ztest([won, rest["won"].sum()], [n, len(rest)])
        # Fair: page vs what its channel mix predicts.
        # Approximation: one expected rate for the whole page.
        p_fair = binomtest(won, n, expected_rate).pvalue

        low, high = wilson(won, n)
        top_channel = grp["origin"].value_counts(normalize=True)
        rows.append({
            "page": page, "leads": n, "won": won, "rate": won / n,
            "ci_low": low, "ci_high": high, "expected": expected_rate,
            "main_channel": f"{top_channel.index[0]} {top_channel.iloc[0]:.0%}",
            "main_origin": top_channel.index[0],          # separate columns, so the
            "main_origin_share": top_channel.iloc[0],     # dashboard can translate them
            "untracked_share": grp["origin"].isin(UNTRACKED).mean(),
            "untracked_leads": int(grp["origin"].isin(UNTRACKED).sum()),
            "p_naive": p_naive, "p_fair": p_fair,
        })
    t = pd.DataFrame(rows).sort_values("leads", ascending=False)

    # Multiple testing corrections across all pages tested
    t["p_naive_bh"] = multipletests(t["p_naive"], method="fdr_bh")[1]
    t["p_fair_bh"] = multipletests(t["p_fair"], method="fdr_bh")[1]
    t["p_fair_bonf"] = multipletests(t["p_fair"], method="bonferroni")[1]
    # Upper bound of wins lost against the channel expectation (only if below it)
    t["wins_below_expected"] = np.maximum(0, t["expected"] * t["leads"] - t["won"])
    return t


def fmt(t: pd.DataFrame) -> list[str]:
    out = [f"  {'page':<9}{'leads':>6}{'win 60d':>9}{'95% CI':>12}{'expected':>10}"
           f"{'diff':>7}{'p naive':>9}{'p fair':>8}{'fair, BH':>10}  main channel"]
    for r in t.itertuples():
        flag = "  <- below" if r.p_fair_bh < 0.05 and r.rate < r.expected else \
               "  <- above" if r.p_fair_bh < 0.05 else ""
        out.append(f"  {r.page:<9}{r.leads:>6}{r.rate:>9.1%}"
                   f"{f'{r.ci_low:.0%}-{r.ci_high:.0%}':>12}{r.expected:>10.1%}"
                   f"{r.rate - r.expected:>+7.1%}{r.p_naive:>9.3f}{r.p_fair:>8.3f}"
                   f"{r.p_fair_bh:>10.3f}  {r.main_channel}{flag}")
    return out


def multiple_testing_summary(t: pd.DataFrame) -> list[str]:
    count = lambda col: int((t[col] < 0.05).sum())
    return [
        f"  Pages tested: {len(t)}. Expected false alarms at 5 % without correction: "
        f"about {0.05 * len(t):.1f}",
        f"  'Significant' (p < 0.05)                naive    fair",
        f"    no correction                         {count('p_naive'):>5}   {count('p_fair'):>5}",
        f"    Benjamini-Hochberg                    {count('p_naive_bh'):>5}   {count('p_fair_bh'):>5}",
        f"    Bonferroni (strictest)                    -   {count('p_fair_bonf'):>5}",
    ]


def tracking(df: pd.DataFrame, t: pd.DataFrame) -> list[str]:
    untracked = df[df["origin"].isin(UNTRACKED)]
    by_page = untracked.groupby("page").size().sort_values(ascending=False)
    top = by_page.index[0]
    return [
        f"  Untracked leads (unknown + not_tracked): {len(untracked):,}",
        f"  Of these, on page {top}: {by_page.iloc[0]:,} ({by_page.iloc[0] / len(untracked):.0%})",
        f"  Next pages: " + ", ".join(f"{p} {n}" for p, n in by_page.iloc[1:4].items()),
    ]


def main() -> None:
    df = load()
    t = page_tests(df)
    chi2, dof, p = chi_square(df[df["page"].isin(t["page"])], "page", "won")

    sections = {
        "1. How leads are spread over the pages": concentration(df),
        f"2. Pages with >= {MIN_LEADS} leads (do they differ at all? chi2 = {chi2:.0f}, "
        f"df = {dof}, p = {p:.1g})": fmt(t),
        "3. Multiple testing: how many pages look 'significant'?": multiple_testing_summary(t),
        "4. Where the untracked leads come from": tracking(df, t),
        "5. Wins below channel expectation (upper bound, pages flagged below)": [
            f"  {r.page}: about {r.wins_below_expected:.0f} wins in 2018 "
            f"({r.leads} leads, {r.rate:.1%} vs {r.expected:.1%} expected)"
            for r in t[(t["p_fair_bh"] < 0.05) & (t["rate"] < t["expected"])].itertuples()
        ] or ["  none"],
    }

    for title, lines in sections.items():
        print(f"\n{title}")
        print("\n".join(lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Evidence: landing pages (Step 4.3)", "",
          "Generated by `analysis/03_landing_pages.py`. Evidence only; "
          "the recommendation is in README section 9.", ""]
    for title, lines in sections.items():
        md += [f"## {title}", "", "```text", *lines, "```", ""]
    OUTPUT.write_text("\n".join(md), encoding="utf-8")
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    t.to_parquet(RESULT, index=False)
    print(f"Saved: {RESULT.relative_to(ROOT)}")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
