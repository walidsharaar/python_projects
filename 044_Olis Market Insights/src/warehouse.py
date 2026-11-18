"""Step 3: build the DuckDB warehouse from the cleaned Parquet files.

Run from the project root (after src\\clean.py):
    python src\\warehouse.py

What happens:
    1. Staging:   every Parquet file becomes a table stg_<name>.
    2. Model:     the SQL files in sql/warehouse run in name order
                  (10_ dimensions first, then 20_ facts).
    3. Validate:  grain checks and money reconciliation. If one fails,
                  the script stops, so nobody uses wrong numbers.

The database file is rebuilt with CREATE OR REPLACE on every run,
so the script is idempotent, like clean.py.
"""

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
# Run in this order: the marts are built on top of the facts.
SQL_DIRS = [ROOT / "sql" / "warehouse", ROOT / "sql" / "marts"]
DB_PATH = ROOT / "database" / "warehouse.duckdb"

# fact/dim table -> columns that together must be unique (the grain)
GRAIN = {
    "dim_customer": ["customer_id"],
    "dim_product": ["product_id"],
    "fct_leads": ["mql_id"],
    "fct_order_items": ["order_id", "order_item_id"],
    "fct_orders": ["order_id"],
    "fct_seller_activation": ["seller_id"],
    "mart_kpi_summary": ["kpi_key"],
    "mart_gtm_monthly": ["cohort_month"],
    "mart_channel_performance": ["origin"],
    "mart_buyer_retention": ["cohort_month", "month_number"],
    "mart_seller_activation_curve": ["won_month", "window_days"],
}


def scalar(con, sql: str):
    """Run a query that returns one value."""
    return con.execute(sql).fetchone()[0]


def load_staging(con) -> None:
    for path in sorted(PROCESSED.glob("*.parquet")):
        table = f"stg_{path.stem}"
        con.execute(f"CREATE OR REPLACE TABLE {table} AS "
                    f"SELECT * FROM read_parquet('{path.as_posix()}')")
        print(f"  {table:<26} {scalar(con, f'SELECT COUNT(*) FROM {table}'):>9,} rows")


def build_model(con) -> None:
    sql_files = [f for folder in SQL_DIRS for f in sorted(folder.glob("*.sql"))]
    for sql_file in sql_files:
        con.execute(sql_file.read_text(encoding="utf-8"))
        table = sql_file.stem.split("_", 1)[1]          # 20_fct_leads -> fct_leads
        print(f"  {sql_file.name:<30} -> {scalar(con, f'SELECT COUNT(*) FROM {table}'):>9,} rows")


def validate(con) -> None:
    problems = []

    def check(ok: bool, message: str) -> None:
        print(f"  [{'OK' if ok else 'FAIL'}] {message}")
        if not ok:
            problems.append(message)

    # 1. Grain: rows = distinct keys. If not, a join has duplicated rows.
    for table, keys in GRAIN.items():
        rows = scalar(con, f"SELECT COUNT(*) FROM {table}")
        distinct = scalar(con, f"SELECT COUNT(*) FROM (SELECT DISTINCT {', '.join(keys)} FROM {table})")
        check(rows == distinct, f"{table}: one row per {' + '.join(keys)} ({rows:,} rows)")

    # 2. No rows lost or added compared to staging
    check(scalar(con, "SELECT COUNT(*) FROM fct_leads") == scalar(con, "SELECT COUNT(*) FROM stg_leads"),
          "fct_leads has every lead (won and not won)")
    check(scalar(con, "SELECT COUNT(*) FROM fct_order_items") == scalar(con, "SELECT COUNT(*) FROM stg_order_items"),
          "fct_order_items has every item")
    check(scalar(con, "SELECT COUNT(*) FROM fct_seller_activation") == scalar(con, "SELECT COUNT(*) FROM stg_deals"),
          "fct_seller_activation has every won seller")

    # 3. Money reconciliation: the same GMV, however we get to it
    gmv_staging = scalar(con, "SELECT SUM(price) FROM stg_order_items")
    gmv_items = scalar(con, "SELECT SUM(price) FROM fct_order_items")
    gmv_orders = scalar(con, "SELECT SUM(items_value) FROM fct_orders")
    check(round(gmv_staging, 2) == round(gmv_items, 2) == round(gmv_orders, 2),
          f"GMV reconciles: staging = items = orders = {gmv_staging:,.2f} BRL")

    # 4. Lead-to-deal consistency
    check(scalar(con, "SELECT COUNT(*) FROM fct_leads WHERE is_won") == 842,
          "842 won leads in fct_leads")

    # 5. Marts must add up to the facts they come from (reconciliation)
    check(scalar(con, "SELECT SUM(leads) FROM mart_gtm_monthly") == 8_000
          and scalar(con, "SELECT SUM(leads) FROM mart_channel_performance") == 8_000,
          "monthly and channel marts both add up to 8,000 leads")
    check(scalar(con, "SELECT SUM(won_60d) FROM mart_gtm_monthly")
          == scalar(con, "SELECT numerator FROM mart_kpi_summary WHERE kpi_key = 'lead_to_win_rate_60d'"),
          "monthly 60-day wins add up to the KPI summary")
    check(scalar(con, "SELECT COUNT(*) FROM mart_channel_performance "
                      "WHERE NOT lead_to_win_rate BETWEEN lead_to_win_ci_low AND lead_to_win_ci_high") == 0,
          "every channel rate lies inside its confidence interval")

    # 6. Cohorts: month 0 is the first purchase, so it must be 100 % everywhere
    check(scalar(con, "SELECT COUNT(*) FROM mart_buyer_retention "
                      "WHERE month_number = 0 AND retention_rate <> 1") == 0,
          "buyer retention: month 0 is 100 % in every cohort")
    # Cohort sizes vs KPI summary. The KPI counts all non-canceled orders, the
    # cohorts stop at the last full month, so the cohorts may only be smaller.
    cohort_buyers = scalar(con, "SELECT SUM(cohort_customers) FROM mart_buyer_retention WHERE month_number = 0")
    kpi_buyers = scalar(con, "SELECT denominator FROM mart_kpi_summary WHERE kpi_key = 'buyer_repeat_rate'")
    check(0 <= kpi_buyers - cohort_buyers < 100,
          f"buyer cohorts ({cohort_buyers:,}) match the KPI summary ({kpi_buyers:,.0f}) "
          f"except buyers after the data end")

    if problems:
        raise SystemExit(f"\n{len(problems)} validation problem(s). Do not use this warehouse.")


def show_lessons(con) -> None:
    """Two numbers worth seeing once with your own eyes."""
    print("\nLesson 1: what a wrong join does to GMV")
    right = scalar(con, "SELECT SUM(price) FROM stg_order_items")
    wrong = scalar(con, """
        SELECT SUM(i.price)
        FROM stg_order_items i
        JOIN stg_payments p ON p.order_id = i.order_id   -- one order has many payments!
    """)
    print(f"  correct GMV (items only):       {right:>16,.2f} BRL")
    print(f"  items joined with payments:     {wrong:>16,.2f} BRL  (+{wrong / right - 1:.1%})")

    print("\nLesson 2: the open activation decision")
    for label, where in [("exclude canceled only (current rule)", "NOT is_canceled"),
                         ("exclude canceled and unavailable", "NOT is_canceled AND NOT is_unavailable")]:
        rate = scalar(con, f"""
            SELECT AVG(CASE WHEN s.seller_id IS NOT NULL THEN 1 ELSE 0 END)
            FROM stg_deals d
            LEFT JOIN (SELECT DISTINCT seller_id FROM fct_order_items WHERE {where}) s
                ON s.seller_id = d.seller_id
        """)
        print(f"  activation rate, {label:<38} {rate:.2%}")


def show_kpis(con) -> None:
    """Print the KPI layer, so every run shows the headline numbers."""
    print("\nKPI summary (mart_kpi_summary)")
    for key, unit, value, num, den in con.execute(
            "SELECT kpi_key, unit, value, numerator, denominator FROM mart_kpi_summary").fetchall():
        shown = f"{value:.1%}" if unit == "rate" else f"{value:,.1f} {unit}"
        # UNION ALL gives all rows one common type (DOUBLE), so format as whole numbers
        basis = f"{num:,.0f} / {den:,.0f}" if den else f"n = {num:,.0f}"
        print(f"  {key:<36} {shown:>14}   ({basis})")

    print("\nChannel performance (mart_channel_performance)")
    print(f"  {'origin':<18} {'leads':>6} {'win rate':>9} {'95% CI':>15} "
          f"{'sellers*':>9} {'activ.':>7} {'GMV 90d':>8}")
    for o, leads, rate, lo, hi, small, n_s, act, gmv in con.execute("""
            SELECT origin, leads, lead_to_win_rate, lead_to_win_ci_low, lead_to_win_ci_high,
                   is_small_sample, won_sellers_full_window, activation_rate, gmv_90d_per_won_seller
            FROM mart_channel_performance""").fetchall():
        act_s = f"{act:.0%}" if act is not None else "-"
        gmv_s = f"{gmv:,.0f}" if gmv is not None else "-"
        flag = " (small)" if small else ""
        print(f"  {o:<18} {leads:>6,} {rate:>9.1%} {lo:>7.1%}-{hi:<7.1%} "
              f"{n_s:>9} {act_s:>7} {gmv_s:>8}{flag}")
    print("  * won sellers with a full 90-day window")


def main() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    with duckdb.connect(str(DB_PATH)) as con:
        print("1. Staging")
        load_staging(con)
        print("\n2. Model")
        build_model(con)
        print("\n3. Validation")
        validate(con)
        show_lessons(con)
        show_kpis(con)
    print(f"\nWarehouse ready: {DB_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
