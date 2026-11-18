"""Step 4.4: tracking and data quality. How wrong would a decision be
if someone ignored the gaps we found?


Four gaps, each as a sensitivity analysis (same KPI, different assumptions):
    1. Coverage gap:   deals were only recorded from 5 Dec 2017   (H1)
    2. Attribution:    14 % of leads have no channel               (H2)
    3. Right-censoring: late sellers had less time to activate
    4. Record-level flags from the cleaning step

The scenarios in part 2 are never written back into the data.
They only show how much the channel KPIs COULD move.
"""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "04_tracking_data_quality.md"
UNTRACKED = ["unknown", "not_tracked"]
FOCUS = ["organic_search", "paid_search", "direct_traffic", "social"]


def q(con, sql: str) -> pd.DataFrame:
    return con.execute(sql).df()


def coverage_gap(con) -> list[str]:
    first_won = con.execute("SELECT MIN(won_date) FROM fct_leads").fetchone()[0]
    y = q(con, """
        SELECT year(cohort_month) AS year, COUNT(*) AS leads,
               AVG(is_won_within_60d::INT) AS win_60d,
               AVG(is_won::INT)            AS win_ever
        FROM fct_leads GROUP BY 1 ORDER BY 1
    """)
    late_wins = con.execute("""
        SELECT COUNT(*) FROM fct_leads
        WHERE year(cohort_month) = 2017 AND is_won AND NOT is_won_within_60d
    """).fetchone()[0]
    # A fair before/after: two periods that are both fully tracked
    fair = q(con, """
        SELECT CASE WHEN cohort_month < DATE '2018-03-01' THEN 'Jan-Feb 2018' ELSE 'Mar-Apr 2018' END AS period,
               COUNT(*) AS leads, AVG(is_won_within_60d::INT) AS win_60d
        FROM fct_leads
        WHERE cohort_month BETWEEN DATE '2018-01-01' AND DATE '2018-04-01'
        GROUP BY 1 ORDER BY 1
    """)
    r17, r18 = y.loc[y.year == 2017, "win_60d"].item(), y.loc[y.year == 2018, "win_60d"].item()
    return [
        f"  First recorded won deal: {first_won:%d %b %Y}. Leads start in Jun 2017.",
        f"  Naive before/after (60-day win rate): 2017 {r17:.1%} -> 2018 {r18:.1%} "
        f"= {r18 / r17:.0f}x 'improvement'",
        f"  2017 leads won only after more than 60 days: {late_wins} "
        f"(they closed after tracking started; the rest is simply not recorded)",
        "  Fair before/after, both periods fully tracked:",
        *[f"    {r.period}: {r.win_60d:.1%} ({r.leads:,} leads)" for r in fair.itertuples()],
        "  -> The real change is about +1 point, not 20x.",
    ]


def attribution_scenarios(con) -> list[str]:
    leads = q(con, """
        SELECT l.landing_page_id, l.origin, l.is_won_within_60d::INT AS won
        FROM fct_leads AS l JOIN mart_gtm_monthly AS m USING (cohort_month)
        WHERE m.deal_tracking_complete
    """)
    tracked = leads[~leads["origin"].isin(UNTRACKED)]
    untracked = leads[leads["origin"].isin(UNTRACKED)]

    def rates(assigned: pd.DataFrame) -> pd.Series:
        """Win rate per channel when untracked leads are spread by the weights in `assigned`.

        assigned: one row per (untracked lead, channel) with a weight that sums to 1 per lead.
        """
        both = pd.concat([tracked.assign(weight=1.0), assigned])
        g = both.assign(w_won=both["won"] * both["weight"]).groupby("origin")[["w_won", "weight"]].sum()
        return (g["w_won"] / g["weight"])[FOCUS]

    overall_mix = tracked["origin"].value_counts(normalize=True).rename("weight").rename_axis("origin").reset_index()
    page_mix = tracked.groupby("landing_page_id")["origin"].value_counts(normalize=True) \
        .rename("weight").reset_index()
    # Untracked leads on pages without any tracked lead fall back to the overall mix
    no_page_info = ~untracked["landing_page_id"].isin(page_mix["landing_page_id"])
    by_page = pd.concat([
        untracked[~no_page_info].drop(columns="origin").merge(page_mix, on="landing_page_id"),
        untracked[no_page_info].drop(columns="origin").merge(overall_mix, how="cross"),
    ])

    scenarios = {
        "A  ignore untracked (today)": rates(tracked.iloc[0:0].assign(weight=1.0)),
        "B  all are organic_search": rates(untracked.assign(origin="organic_search", weight=1.0)),
        "C  all are paid_search": rates(untracked.assign(origin="paid_search", weight=1.0)),
        "D  spread like tracked leads": rates(untracked.drop(columns="origin").merge(overall_mix, how="cross")),
        "E  spread like tracked leads ON THE SAME PAGE": rates(by_page),
    }
    table = pd.DataFrame(scenarios).T

    out = [f"  Untracked leads (2018 cohorts): {len(untracked):,} of {len(leads):,} "
           f"({len(untracked) / len(leads):.1%}); their win rate {untracked['won'].mean():.1%} "
           f"vs tracked {tracked['won'].mean():.1%}",
           f"  {'scenario':<48}" + "".join(f"{c:>16}" for c in FOCUS)]
    for name, row in table.iterrows():
        out.append(f"  {name:<48}" + "".join(f"{v:>16.1%}" for v in row))
    swing = table.max() - table.min()
    out.append(f"  {'range (max - min)':<48}" + "".join(f"{v:>+16.1%}" for v in swing))

    best_page = by_page.groupby("origin")["weight"].sum().sort_values(ascending=False)
    out.append("  Best guess (E): the untracked leads are about " +
               ", ".join(f"{o} {w / best_page.sum():.0%}" for o, w in best_page.iloc[:3].items()))
    return out


def censoring(con) -> list[str]:
    m = q(con, """
        SELECT CAST(date_trunc('month', won_date) AS DATE) AS won_month,
               COUNT(*) AS sellers, AVG(is_activated::INT) AS activation,
               BOOL_AND(has_full_90d_window) AS full_window
        FROM fct_seller_activation GROUP BY 1 ORDER BY 1
    """)
    last_order, last_item = con.execute("""
        SELECT (SELECT MAX(purchased_at) FROM fct_orders),
               (SELECT MAX(purchased_at) FROM fct_order_items)
    """).fetchone()
    out = [f"  Last order in the data: {last_order:%d %b %Y}, but last order WITH items: "
           f"{last_item:%d %b %Y}.",
           "  The effective data end is the second date. The 90-day window uses it.",
           f"  {'won month':<12}{'sellers':>8}{'activation':>12}  window"]
    for r in m.itertuples():
        out.append(f"  {r.won_month:%Y-%m}{'':<5}{r.sellers:>8}{r.activation:>12.0%}  "
                   f"{'full' if r.full_window else 'CUT OFF by end of data'}")
    naive, fair = con.execute("""
        SELECT AVG(is_activated::INT), AVG(is_activated::INT) FILTER (WHERE has_full_90d_window)
        FROM fct_seller_activation
    """).fetchone()
    out.append(f"  Activation, all sellers: {naive:.1%}  |  full window only: {fair:.1%}  "
               f"-> mixing them understates activation by {(fair - naive) * 100:.1f} points")
    return out


def record_flags(con) -> list[str]:
    rows = [
        ("orders", "dq_impossible_dates", "SELECT COUNT(*) FROM fct_orders WHERE dq_impossible_dates",
         "delivery-time KPIs (not GMV)"),
        ("orders", "dq_delivered_without_date", "SELECT COUNT(*) FROM fct_orders WHERE dq_delivered_without_date",
         "delivery-time KPIs"),
        ("orders", "no items at all", "SELECT COUNT(*) FROM fct_orders WHERE n_items = 0",
         "order counts, average order value"),
        ("deals", "dq_negative_sales_cycle", "SELECT COUNT(*) FROM fct_leads WHERE dq_negative_sales_cycle",
         "sales cycle"),
        ("deals", "declared_monthly_revenue missing", "SELECT COUNT(*) FROM stg_deals WHERE declared_monthly_revenue IS NULL",
         "any revenue-based lead scoring"),
        ("deals", "lead_behaviour_profile missing", "SELECT COUNT(*) FROM fct_leads WHERE is_won AND lead_behaviour_profile IS NULL",
         "behaviour analysis (no effect found anyway)"),
    ]
    out = [f"  {'table':<8}{'issue':<36}{'records':>8}  affects"]
    for table, issue, sql, affects in rows:
        out.append(f"  {table:<8}{issue:<36}{con.execute(sql).fetchone()[0]:>8,}  {affects}")
    return out


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        sections = {
            "1. Coverage gap: the fake 2017 -> 2018 improvement (H1)": coverage_gap(con),
            "2. Attribution gap: how much could the channel win rates move? (H2)": attribution_scenarios(con),
            "3. Right-censoring: activation by month won": censoring(con),
            "4. Record-level flags (from src/clean.py)": record_flags(con),
        }

    for title, lines in sections.items():
        print(f"\n{title}")
        print("\n".join(lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Evidence: tracking and data quality (Step 4.4)", "",
          "Generated by `analysis/04_tracking_data_quality.py`. Evidence only; "
          "the recommendation is in README section 9.", ""]
    for title, lines in sections.items():
        md += [f"## {title}", "", "```text", *lines, "```", ""]
    OUTPUT.write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
