"""
Source system simulator: Company A (Nordwerk Haushalt GmbH) on SAP Business One.
Writes fake data with real SAP B1 table and column names into the database src_sap_b1.
Tables: OCRD (customers), OITB (item groups), OITM (items), ORDR/RDR1 (orders)
"""
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from etl.db import get_engine   # our shared helper; reads credentials from .env

SEED = 42
N_CUSTOMERS = 200
N_ORDERS = 2000
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


def make_special_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """Group companies as customers (intercompany) and one duplicate customer."""
    created = date(2024, 1, 15)
    group_companies = pd.DataFrame([
        {"cardcode": "C19001", "cardname": "Nordwerk Beutel GmbH", "cardtype": "C",
         "city": "Bielefeld", "zipcode": "33602", "country": "DE",
         "createdate": created, "updatedate": created},
        {"cardcode": "C19002", "cardname": "Nordwerk Handschuhe GmbH", "cardtype": "C",
         "city": "Hamburg", "zipcode": "20095", "country": "DE",
         "createdate": created, "updatedate": created},
    ])
    # Problem 5: the first customer exists a second time, name in capitals
    duplicate = customers.iloc[[0]].copy()
    duplicate["cardcode"] = "C10999"
    duplicate["cardname"] = duplicate["cardname"].str.upper()

    return pd.concat([group_companies, duplicate], ignore_index=True)


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

    # Problem 1: about 8% of items have no EAN
    missing = items.sample(frac=0.08, random_state=SEED).index
    items.loc[missing, "codebars"] = None

    # Problem 2: two items share the same EAN
    with_ean = items["codebars"].dropna().index
    items.loc[with_ean[-1], "codebars"] = items.loc[with_ean[0], "codebars"]

    return items



def make_orders(customers: pd.DataFrame, items: pd.DataFrame, n: int):
    """ORDR (headers) and RDR1 (lines)."""
    headers, lines = [], []
    cardcodes = customers["cardcode"].tolist()
    item_list = items.to_dict("records")
    today = date.today()

    for docentry in range(1, n + 1):
        docdate = fake.date_between(start_date="-2y", end_date="today")
        duedate = docdate + timedelta(days=random.randint(2, 14))
        cardcode = random.choice(cardcodes)
        if random.random() < 0.01:
            cardcode = "C99999"            # Problem 3: customer not in OCRD

        doctotal = 0.0
        order_items = random.sample(item_list, k=random.randint(1, 5))
        for linenum, item in enumerate(order_items):   # B1 lines start at 0
            qty = random.randint(1, 2) if item["salunitmsr"] == "Pal" else random.randint(1, 20)
            price = round(item["avgprice"] * item["numinsale"] * random.uniform(1.3, 1.8), 2)
            linetotal = round(qty * price, 2)
            doctotal += linetotal
            lines.append({
                "docentry":  docentry,
                "linenum":   linenum,
                "itemcode":  item["itemcode"],
                "quantity":  qty,                    # in sales units
                "unitmsr":   item["salunitmsr"],     # Stk / Krt / Pal
                "numpermsr": item["numinsale"],      # pieces per sales unit
                "price":     price,                  # per sales unit
                "linetotal": linetotal,
            })

        headers.append({
            "docentry":   docentry,                  # internal key
            "docnum":     100000 + docentry,         # number the user sees
            "cardcode":   cardcode,
            "docdate":    docdate,
            "docduedate": duedate,
            "docstatus":  "C" if duedate < today else "O",   # C = closed, O = open
            "canceled":   "Y" if random.random() < 0.02 else "N",
            "doctotal":   round(doctotal, 2),
            "updatedate": min(docdate + timedelta(days=random.randint(0, 10)), today),
        })

    return pd.DataFrame(headers), pd.DataFrame(lines)



def main():
    engine = get_engine(SOURCE_DB)

    customers = make_customers(N_CUSTOMERS)
    customers = pd.concat([customers, make_special_customers(customers)], ignore_index=True)
    items = make_items()
    ordr, rdr1 = make_orders(customers, items, N_ORDERS)

    tables = {
        "ocrd": customers,
        "oitb": make_item_groups(),
        "oitm": items,
        "ordr": ordr,
        "rdr1": rdr1,
    }
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False)
        print(f"{name}: {len(df)} rows written to {SOURCE_DB}")


if __name__ == "__main__":
    main()