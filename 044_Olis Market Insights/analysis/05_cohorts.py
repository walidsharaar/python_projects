"""Step 5.1: cohorts. Do buyers come back, and how fast do new sellers start?

Reads the cohort marts; it does not recalculate any KPI itself:
    mart_buyer_retention           buyers by month of first purchase
    mart_seller_activation_curve   won sellers by month won, 30/60/90 days

How to read a cohort table:
    - Each ROW is one group that started in the same month.
    - Each COLUMN is "N months later".
    - Read along a row: how does one group behave over time?
    - Read down a column: do newer groups behave better than older ones?
    - "." means not observable yet. That is NOT 0 %.
"""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"
OUTPUT = ROOT / "reports" / "analysis" / "05_cohorts.md"
MIN_COHORT = 1_000      # smaller cohorts (Sep-Dec 2016) are too noisy to read
SHOW_MONTHS = 7         # month 0 .. 6


def buyer_matrix(con) -> tuple[list[str], pd.DataFrame]:
    df = con.execute("SELECT * FROM mart_buyer_retention").df()
    big = df[df["cohort_customers"] >= MIN_COHORT]
    matrix = big.pivot(index="cohort_month", columns="month_number", values="retention_rate")
    sizes = big.groupby("cohort_month")["cohort_customers"].first()

    cols = list(range(SHOW_MONTHS))
    lines = [f"  {'first purchase':<16}{'buyers':>8}" + "".join(f"{f'M{m}':>8}" for m in cols)]
    for month, row in matrix.iterrows():
        cells = "".join(f"{row[m]:>8.2%}" if m in row and pd.notna(row[m]) else f"{'.':>8}"
                        for m in cols)
        lines.append(f"  {month:%Y-%m}{'':<9}{sizes[month]:>8,}{cells}")

    # Weighted average curve: every buyer counts once, big months weigh more
    curve = (big.assign(active=big["active_customers"])
                .groupby("month_number")[["active", "cohort_customers"]].sum())
    curve["rate"] = curve["active"] / curve["cohort_customers"]
    lines.append(f"  {'weighted avg':<16}{'':>8}" + "".join(
        f"{curve.loc[m, 'rate']:>8.2%}" if m in curve.index else f"{'.':>8}" for m in cols))
    return lines, curve


def buyer_summary(con, curve: pd.DataFrame) -> list[str]:
    total, repeat = con.execute("""
        SELECT denominator, numerator FROM mart_kpi_summary WHERE kpi_key = 'buyer_repeat_rate'
    """).fetchone()
    # Months to second purchase: when do the few repeat buyers come back?
    gaps = con.execute("""
        WITH p AS (
            SELECT customer_unique_id, purchased_at,
                   ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchased_at) AS n
            FROM fct_orders WHERE NOT is_canceled
        )
        SELECT date_diff('day', a.purchased_at, b.purchased_at) AS days
        FROM p AS a JOIN p AS b
          ON a.customer_unique_id = b.customer_unique_id AND a.n = 1 AND b.n = 2
    """).df()["days"]
    same_day = (gaps == 0).mean()
    m1_to_m6 = curve.loc[1:6, "rate"]
    return [
        f"  Buyers with 2+ purchases: {repeat:,.0f} of {total:,.0f} ({repeat / total:.1%})",
        f"  Retention in months 1-6 (weighted): {m1_to_m6.min():.2%} to {m1_to_m6.max():.2%} per month",
        f"  Time from 1st to 2nd purchase: median {gaps.median():.0f} days; "
        f"{same_day:.0%} on the SAME day (likely one basket split into two orders, not loyalty)",
        f"  Without same-day repeats: {(gaps > 0).sum():,} real returns "
        f"({(gaps > 0).sum() / total:.1%} of buyers)",
    ]


def seller_curve(con) -> list[str]:
    df = con.execute("SELECT * FROM mart_seller_activation_curve").df()
    lines = [f"  {'won month':<11}{'sellers':>8}{'30 days':>10}{'60 days':>10}{'90 days':>10}"]
    for month, grp in df.groupby("won_month"):
        g = grp.set_index("window_days")
        cells = "".join(
            f"{g.loc[w, 'activation_rate']:>10.0%}" if pd.notna(g.loc[w, "activation_rate"])
            and g.loc[w, "observable_sellers"] == g.loc[w, "won_sellers"]
            else (f"{'partly':>10}" if g.loc[w, "observable_sellers"] > 0 else f"{'.':>10}")
            for w in (30, 60, 90))
        lines.append(f"  {month:%Y-%m}{'':<4}{g['won_sellers'].iloc[0]:>8}{cells}")
    lines.append("  'partly' = only some sellers of that month have the full window; '.' = none yet")

    tot = df.groupby("window_days")[["activated_in_window", "observable_sellers"]].sum()
    tot["rate"] = tot["activated_in_window"] / tot["observable_sellers"]
    lines.append("  All observable sellers: " + ", ".join(
        f"{w} days {r.rate:.0%} (n = {r.observable_sellers:.0f})" for w, r in tot.iterrows()))
    return lines


def main() -> None:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        matrix_lines, curve = buyer_matrix(con)
        sections = {
            f"1. Buyer retention by month of first purchase (cohorts with >= {MIN_COHORT:,} buyers)":
                matrix_lines,
            "2. What the buyer cohorts say": buyer_summary(con, curve),
            "3. Seller activation curve: share of won sellers who sold within N days": seller_curve(con),
        }

    for title, lines in sections.items():
        print(f"\n{title}")
        print("\n".join(lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    md = ["# Evidence: cohorts (Step 5.1)", "",
          "Generated by `analysis/05_cohorts.py`. Evidence only.", ""]
    for title, lines in sections.items():
        md += [f"## {title}", "", "```text", *lines, "```", ""]
    OUTPUT.write_text("\n".join(md), encoding="utf-8")
    print(f"\nSaved: {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
