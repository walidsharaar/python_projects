"""
Source system simulator: Company A  on SAP Business One.
Writes fake data with real SAP B1 table and column names into the database src_sap_b1.
Tables: OCRD (customers), OITB (item groups), OITM (items)
"""
import random

import pandas as pd
from faker import Faker

from etl.db import get_engine   # our shared helper; reads credentials from .env

SEED = 42
N_CUSTOMERS = 200
SOURCE_DB = "src_sap_b1"

fake = Faker("de_DE")
Faker.seed(SEED)
random.seed(SEED)



def make_customers(n: int) -> pd.DataFrame:
    """OCRD: n customers."""
    rows = []
    for i in range(1, n + 1):
        created = fake.date_between(start_date="-5y", end_date="-1y")
        rows.append({
            "cardcode":   f"C{10000 + i}",   # B1: CardCode, e.g. C10001
            "cardname":   fake.company(),    # B1: CardName
            "cardtype":   "C",               # C = customer, S = supplier
            "city":       fake.city(),
            "zipcode":    fake.postcode(),
            "country":    "DE",
            "createdate": created,
            "updatedate": fake.date_between(start_date=created, end_date="today"),
        })
    return pd.DataFrame(rows)



ITEM_GROUPS = {
    101: "Reinigungsmittel",
    102: "Spülen & Küche",
    103: "Aufbewahrung",
}

PRODUCTS = {
    101: ["Allzweckreiniger", "Glasreiniger", "Badreiniger", "Entkalker", "Bodenreiniger"],
    102: ["Spülmittel", "Spülschwamm", "Schwammtuch", "Topfreiniger", "Geschirrtuch"],
    103: ["Gefrierbeutel", "Frischhaltefolie", "Alufolie", "Backpapier", "Zipper-Beutel"],
}

VARIANTS = {
    101: ["500 ml", "750 ml", "1 l"],
    102: ["Einzeln", "3er Pack", "5er Pack"],
    103: ["Klein", "Mittel", "Groß"],
}

# (sales unit, pieces per sales unit); "Stk" twice = sold more often
SALES_UNITS = [("Stk", 1), ("Stk", 1), ("Krt", 6), ("Krt", 12), ("Krt", 24), ("Pal", 480)]


def make_item_groups() -> pd.DataFrame:
    """OITB: item groups."""
    return pd.DataFrame(
        [{"itmsgrpcod": code, "itmsgrpnam": name} for code, name in ITEM_GROUPS.items()]
    )


def make_items() -> pd.DataFrame:
    """OITM: one item per product and variant, with deliberate data problems."""
    rows = []
    n = 0
    for group, products in PRODUCTS.items():
        for product in products:
            for variant in VARIANTS[group]:
                n += 1
                unit, per_unit = random.choice(SALES_UNITS)
                created = fake.date_between(start_date="-5y", end_date="-1y")
                rows.append({
                    "itemcode":   f"A{n:05d}",              # e.g. A00001
                    "itemname":   f"{product} {variant}",
                    "itmsgrpcod": group,
                    "codebars":   fake.ean13(),             # valid 13-digit EAN
                    "salunitmsr": unit,
                    "numinsale":  per_unit,
                    "avgprice":   round(random.uniform(0.40, 4.00), 2),  # cost per piece
                    "createdate": created,
                    "updatedate": fake.date_between(start_date=created, end_date="today"),
                })
    items = pd.DataFrame(rows)

    # Deliberate problem 1: about 8% of items have no EAN
    missing = items.sample(frac=0.08, random_state=SEED).index
    items.loc[missing, "codebars"] = None

    # Deliberate problem 2: two items share the same EAN
    with_ean = items["codebars"].dropna().index
    items.loc[with_ean[-1], "codebars"] = items.loc[with_ean[0], "codebars"]

    return items


def main():
    engine = get_engine(SOURCE_DB)

    tables = {
        "ocrd": make_customers(N_CUSTOMERS),
        "oitb": make_item_groups(),
        "oitm": make_items(),
    }
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"{name}: {len(df)} rows written to {SOURCE_DB}")


if __name__ == "__main__":
    main()