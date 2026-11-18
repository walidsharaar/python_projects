"""Step 1: check that the raw data is complete before any analysis starts.

The script answers four questions:
    1. Are all CSV files there?
    2. Does each file have the expected number of rows?
    3. Is the key column of each table really unique?
    4. Do the tables fit together (keys, date ranges)?
"""

from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"

# file name -> (expected rows, key column that must be unique, or None)
EXPECTED = {
    "olist_marketing_qualified_leads_dataset.csv": (8_000, "mql_id"),
    "olist_closed_deals_dataset.csv": (842, "mql_id"),
    "olist_orders_dataset.csv": (99_441, "order_id"),
    "olist_order_items_dataset.csv": (112_650, None),
    "olist_customers_dataset.csv": (99_441, "customer_id"),
    "olist_sellers_dataset.csv": (3_095, "seller_id"),
    "olist_products_dataset.csv": (32_951, "product_id"),
    "olist_order_payments_dataset.csv": (103_886, None),
    "olist_order_reviews_dataset.csv": (99_224, None),
}

problems = []


def check(ok: bool, message: str) -> None:
    """Print one check result and remember it if it failed."""
    print(f"  [{'OK' if ok else 'FAIL'}] {message}")
    if not ok:
        problems.append(message)

tables = {}
for file_name, (expected_rows, key) in EXPECTED.items():
    print(f"\n{file_name}")
    path = RAW / file_name
    if not path.exists():
        check(False, f"{file_name} is missing in {RAW}")
        continue

    df = pd.read_csv(path)
    tables[file_name] = df
    check(len(df) == expected_rows, f"rows: {len(df):,} (expected {expected_rows:,})")
    if key:
        check(df[key].is_unique, f"key '{key}' is unique")

if len(tables) == len(EXPECTED):
    mql = tables["olist_marketing_qualified_leads_dataset.csv"]
    deals = tables["olist_closed_deals_dataset.csv"]
    orders = tables["olist_orders_dataset.csv"]
    items = tables["olist_order_items_dataset.csv"]

    print("\nRelationships")
    check(deals["mql_id"].isin(mql["mql_id"]).all(), "every closed deal belongs to a known MQL")
    check(items["order_id"].isin(orders["order_id"]).all(), "every order item belongs to a known order")

    selling = deals["seller_id"].isin(items["seller_id"]).mean()
    print(f"  [INFO] {selling:.1%} of won sellers appear in the order data")

    print("\nDate ranges")
    for label, series in [
        ("first contact (MQL)", mql["first_contact_date"]),
        ("won date (deals)", deals["won_date"]),
        ("purchase date (orders)", orders["order_purchase_timestamp"]),
    ]:
        dates = pd.to_datetime(series)
        print(f"  [INFO] {label:<24} {dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}")

print("\n" + "=" * 60)
if problems:
    print(f"{len(problems)} problem(s) found:")
    for p in problems:
        print(f"  - {p}")
    raise SystemExit(1)
print("All checks passed. The raw data is ready for Step 2.")
