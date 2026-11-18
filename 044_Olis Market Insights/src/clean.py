"""Step 2b:clean the raw data and save it.

Rules we follow (and you should be able to explain in an interview):
    1. Raw files are only read, never changed.
    2. No row is deleted. Problem rows get a flag column (dq_...),
       and each KPI later decides whether to exclude them.
    3. Missing values are never invented. Hidden missing values
       ("unknown", 0) are made visible, not filled.
    4. The script is idempotent: running it twice gives the same result,
       because it always starts from the raw files.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
REPORT = ROOT / "docs" / "cleaning_report.md"

# Every cleaning step writes one line here: (table, rule, rows affected).
LOG: list[tuple[str, str, int]] = []


def log(table: str, rule: str, rows: int) -> None:
    LOG.append((table, rule, int(rows)))


def read_raw(file_name: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(RAW / file_name, **kwargs)


def normalize_text(df: pd.DataFrame, table: str, columns: list[str]) -> pd.DataFrame:
    """Trim spaces and use lower case, so 'Social ' and 'social' are one value."""
    for col in columns:
        before = df[col].copy()
        df[col] = df[col].str.strip().str.lower()
        changed = (before.fillna("") != df[col].fillna("")).sum()
        log(table, f"normalize text in '{col}'", changed)
    return df


def fix_zip(series: pd.Series) -> pd.Series:
    """Zip prefixes are labels, not numbers: 1037 must be '01037'."""
    return series.astype(str).str.zfill(5)


def clean_leads() -> pd.DataFrame:
    df = read_raw("olist_marketing_qualified_leads_dataset.csv",
                  parse_dates=["first_contact_date"])
    df = normalize_text(df, "leads", ["origin"])

    # Two kinds of "we don't know the channel": empty, or the text 'unknown'.
    # We keep them apart, because they convert very differently (README H2).
    missing = df["origin"].isna()
    df["origin"] = df["origin"].fillna("not_tracked")
    log("leads", "origin empty -> label 'not_tracked'", missing.sum())

    df["is_attributed"] = ~df["origin"].isin(["unknown", "not_tracked"])
    log("leads", "flag is_attributed = False (unknown or not_tracked)",
        (~df["is_attributed"]).sum())
    return df


# --------------------------------------------------------------- deals
def clean_deals(leads: pd.DataFrame) -> pd.DataFrame:
    df = read_raw("olist_closed_deals_dataset.csv", parse_dates=["won_date"])
    df = normalize_text(df, "deals", ["business_segment", "lead_type",
                                      "business_type", "lead_behaviour_profile"])

    unusable = ["has_company", "has_gtin", "average_stock",
                "declared_product_catalog_size"]
    df = df.drop(columns=unusable)
    log("deals", f"drop {len(unusable)} columns with ~92% missing", len(unusable))

    # 0 here means "not declared", not "zero revenue". Make that visible.
    zero = df["declared_monthly_revenue"] == 0
    df.loc[zero, "declared_monthly_revenue"] = np.nan
    log("deals", "declared_monthly_revenue 0 -> missing", zero.sum())

    df = df.merge(leads[["mql_id", "first_contact_date"]], on="mql_id",
                  how="left", validate="one_to_one")
    df["sales_cycle_days"] = (df["won_date"] - df["first_contact_date"]).dt.days

    df["dq_negative_sales_cycle"] = df["sales_cycle_days"] < 0
    log("deals", "flag dq_negative_sales_cycle (won before first contact)",
        df["dq_negative_sales_cycle"].sum())
    return df


def clean_orders() -> pd.DataFrame:
    date_cols = ["order_purchase_timestamp", "order_approved_at",
                 "order_delivered_carrier_date", "order_delivered_customer_date",
                 "order_estimated_delivery_date"]
    df = read_raw("olist_orders_dataset.csv", parse_dates=date_cols)

    df["is_canceled"] = df["order_status"] == "canceled"
    df["is_unavailable"] = df["order_status"] == "unavailable"
    log("orders", "flag is_canceled", df["is_canceled"].sum())
    log("orders", "flag is_unavailable", df["is_unavailable"].sum())

    purchase = df["order_purchase_timestamp"]
    carrier = df["order_delivered_carrier_date"]
    delivered = df["order_delivered_customer_date"]

    df["dq_impossible_dates"] = (carrier < purchase) | (delivered < carrier)
    log("orders", "flag dq_impossible_dates (handed over before purchase, "
                  "or delivered before handover)", df["dq_impossible_dates"].sum())

    df["dq_delivered_without_date"] = (df["order_status"] == "delivered") & delivered.isna()
    log("orders", "flag dq_delivered_without_date",
        df["dq_delivered_without_date"].sum())
    return df


def clean_order_items() -> pd.DataFrame:
    df = read_raw("olist_order_items_dataset.csv", parse_dates=["shipping_limit_date"])
    # No single key exists. order_id + order_item_id together must be unique.
    dups = df.duplicated(["order_id", "order_item_id"]).sum()
    log("order_items", "duplicates on key (order_id, order_item_id)", dups)
    return df


def clean_customers() -> pd.DataFrame:
    df = read_raw("olist_customers_dataset.csv")
    df["customer_zip_code_prefix"] = fix_zip(df["customer_zip_code_prefix"])
    log("customers", "zip prefix as 5-digit text", len(df))
    return df


def clean_sellers() -> pd.DataFrame:
    df = read_raw("olist_sellers_dataset.csv")
    df["seller_zip_code_prefix"] = fix_zip(df["seller_zip_code_prefix"])
    log("sellers", "zip prefix as 5-digit text", len(df))
    return df

def clean_products() -> pd.DataFrame:
    df = read_raw("olist_products_dataset.csv")

    # The source has typos in two column names.
    df = df.rename(columns={"product_name_lenght": "product_name_length",
                            "product_description_lenght": "product_description_length"})
    log("products", "rename misspelled columns (lenght -> length)", 2)

    translation = read_raw("product_category_name_translation.csv")
    df = df.merge(translation, on="product_category_name", how="left",
                  validate="many_to_one")
    untranslated = df["product_category_name"].notna() & df["product_category_name_english"].isna()
    df.loc[untranslated, "product_category_name_english"] = df.loc[untranslated, "product_category_name"]
    log("products", "no English category name -> keep Portuguese name", untranslated.sum())
    return df


def clean_payments() -> pd.DataFrame:
    # Not used for GMV (see Phase 4: joining it to items would double prices).
    return read_raw("olist_order_payments_dataset.csv")


def clean_reviews() -> pd.DataFrame:
    df = read_raw("olist_order_reviews_dataset.csv",
                  parse_dates=["review_creation_date", "review_answer_timestamp"])
    log("reviews", "review_id appears more than once (kept, not a key)",
        df["review_id"].duplicated().sum())
    return df


def validate(tables: dict[str, pd.DataFrame], raw_rows: dict[str, int]) -> None:
    """Stop the pipeline if cleaning broke something."""
    for name, df in tables.items():
        assert len(df) == raw_rows[name], f"{name}: row count changed"
    for name, key in [("leads", "mql_id"), ("deals", "mql_id"), ("orders", "order_id"),
                      ("customers", "customer_id"), ("sellers", "seller_id"),
                      ("products", "product_id")]:
        assert tables[name][key].is_unique, f"{name}: key {key} not unique"
    print("Validation passed: no rows lost, all keys unique.")


def write_report(tables: dict[str, pd.DataFrame]) -> None:
    lines = ["# Cleaning report", "",
             "Generated by `src/clean.py`. Do not edit by hand.", "",
             "| Table | Rule | Rows affected |", "|---|---|---|"]
    lines += [f"| {t} | {rule} | {n:,} |" for t, rule, n in LOG]
    lines += ["", "## Output files", "", "| Table | Rows | Columns |", "|---|---|---|"]
    lines += [f"| {name} | {len(df):,} | {df.shape[1]} |" for name, df in tables.items()]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    leads = clean_leads()
    tables = {
        "leads": leads,
        "deals": clean_deals(leads),
        "orders": clean_orders(),
        "order_items": clean_order_items(),
        "customers": clean_customers(),
        "sellers": clean_sellers(),
        "products": clean_products(),
        "payments": clean_payments(),
        "reviews": clean_reviews(),
    }
    raw_rows = {"leads": 8_000, "deals": 842, "orders": 99_441, "order_items": 112_650,
                "customers": 99_441, "sellers": 3_095, "products": 32_951,
                "payments": 103_886, "reviews": 99_224}
    validate(tables, raw_rows)

    PROCESSED.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(PROCESSED / f"{name}.parquet", index=False)

    print(f"\n{'table':<12} {'rule':<78} rows")
    for table, rule, n in LOG:
        print(f"{table:<12} {rule:<78} {n:,}")

    write_report(tables)
    print(f"\nSaved {len(tables)} Parquet files to {PROCESSED.relative_to(ROOT)}")
    print(f"Saved report to {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
