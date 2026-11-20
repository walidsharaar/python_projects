"""
Company A (Nordwerk Haushalt GmbH) on SAP Business One.
Writes fake data with real SAP B1 table and column names into the database src_sap_b1.
Part 1: OCRD = business partners (customers)
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
    """Create n customers in the OCRD structure."""
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


def main():
    engine = get_engine(SOURCE_DB)
    ocrd = make_customers(N_CUSTOMERS)
    ocrd.to_sql("ocrd", engine, if_exists="replace", index=False)
    print(f"ocrd: {len(ocrd)} rows written to {SOURCE_DB}")


if __name__ == "__main__":
    main()