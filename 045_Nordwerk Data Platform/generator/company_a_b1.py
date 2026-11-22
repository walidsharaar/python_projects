"""
Source system simulator: Company A (Nordwerk Haushalt GmbH) on SAP Business One.
Writes fake data with real SAP B1 table and column names into the database src_sap_b1.
Tables: OCRD (customers), OITB (item groups), OITM (items),
        ORDR/RDR1 (sales orders), OINV/INV1 (invoices)

The data has patterns a report can discover:
- seasonality (spring cleaning, pre-Christmas) and about 5 % growth per year
- a price list with a 3 % price increase every January, customer-specific discounts
- few large and many small customers
- one customer that grows strongly in 2026 and one that stops buying after March 2026
- a supply problem in August and September 2025 (many partial deliveries)
and the deliberate data problems the quality checks must find.
"""
import random
from datetime import date, timedelta

import pandas as pd
from faker import Faker

from etl.db import copy_rows, ensure_database, get_engine
from generator.common import REFERENCE_DATE, market, price_factor, weighted_dates

SEED = 42
N_CUSTOMERS = 200
N_ORDERS = 3600
SOURCE_DB = "src_sap_b1"

SEASON = [0.90, 0.90, 1.20, 1.25, 1.15, 0.95, 0.85, 0.85, 1.00, 1.05, 1.15, 1.20]
GROWTH = 0.05

GROWER = "C10141"            # buys five times as much from 2026 on
LOST = "C10012"              # no orders after 31.03.2026
LOST_AFTER = date(2026, 3, 31)
SUPPLY_PROBLEM = (date(2025, 8, 1), date(2025, 9, 30))

fake = Faker("de_DE")        # the seed is set in main(), at run time



def make_customers() -> pd.DataFrame:
    """OCRD: the first 200 shops of the market. Shops 141-200 also buy from Company B."""
    rows = []
    for i, shop in enumerate(market()[:N_CUSTOMERS]):
        created = fake.date_between(start_date=date(2016, 1, 1), end_date=date(2022, 6, 30))
        rows.append({
            "cardcode":   f"C{10001 + i}",      # B1: CardCode
            "cardname":   shop["name"],         # B1: CardName
            "cardtype":   "C",                  # C = customer, S = supplier
            "city":       shop["city"],
            "zipcode":    shop["zipcode"],
            "country":    "DE",
            "createdate": created,
            "updatedate": fake.date_between(start_date=created, end_date=REFERENCE_DATE),
        })
    return pd.DataFrame(rows)


def make_special_customers(customers: pd.DataFrame) -> pd.DataFrame:
    """Group companies as customers (intercompany) and one duplicate customer."""
    created = date(2022, 1, 15)
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



ITEM_GROUPS = {101: "Reinigungsmittel", 102: "Spülen & Küche", 103: "Aufbewahrung"}

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
    return pd.DataFrame([{"itmsgrpcod": c, "itmsgrpnam": n} for c, n in ITEM_GROUPS.items()])


def make_items() -> pd.DataFrame:
    """OITM: one item per product and variant, with deliberate data problems."""
    rows = []
    n = 0
    for group, products in PRODUCTS.items():
        for product in products:
            for variant in VARIANTS[group]:
                n += 1
                unit, per_unit = random.choice(SALES_UNITS)
                created = fake.date_between(start_date=date(2016, 1, 1), end_date=date(2022, 6, 30))
                cost = round(random.uniform(0.40, 4.00), 2)
                rows.append({
                    "itemcode":   f"A{n:05d}",
                    "itemname":   f"{product} {variant}",
                    "itmsgrpcod": group,
                    "codebars":   fake.ean13(),
                    "salunitmsr": unit,
                    "numinsale":  per_unit,
                    "avgprice":   cost,                                            # cost per piece
                    "listprice":  round(cost * per_unit * random.uniform(1.35, 1.75), 2),  # 2023 list price per sales unit
                    "createdate": created,
                    "updatedate": fake.date_between(start_date=created, end_date=REFERENCE_DATE),
                })
    items = pd.DataFrame(rows)

    # Problem 1: about 8 % of items have no EAN
    missing = items.sample(frac=0.08, random_state=SEED).index
    items.loc[missing, "codebars"] = None
    # Problem 2: two items share the same EAN
    with_ean = items["codebars"].dropna().index
    items.loc[with_ean[-1], "codebars"] = items.loc[with_ean[0], "codebars"]
    return items


# --- Orders -------------------------------------------------------------
def customer_weights(customers: pd.DataFrame) -> dict:
    """Few large, many small customers (Pareto); group companies buy now and then."""
    weights = {c: min(random.paretovariate(1.6), 15.0) for c in customers["cardcode"]}
    for ic in ("C19001", "C19002"):
        weights[ic] = 1.5
    weights[GROWER] = 2.0        # mid-sized customer that takes off in 2026
    weights[LOST] = 8.0          # one of the larger customers, lost after March 2026
    return weights


def pick_customer(base: dict, d: date) -> str:
    codes = list(base)
    weights = []
    for c in codes:
        w = base[c]
        if c == GROWER and d.year >= 2026:
            w *= 5
        if c == LOST and d > LOST_AFTER:
            w = 0
        weights.append(w)
    return random.choices(codes, weights=weights)[0]


def make_orders(customers: pd.DataFrame, items: pd.DataFrame, n: int):
    """ORDR (headers) and RDR1 (lines), in date order like real document numbers."""
    headers, lines = [], []
    base = customer_weights(customers)
    discount = {c: round(random.uniform(0.0, 0.08), 3) for c in base}
    item_list = items.to_dict("records")

    for docentry, docdate in enumerate(weighted_dates(n, SEASON, GROWTH), start=1):
        duedate = docdate + timedelta(days=random.randint(2, 14))
        cardcode = pick_customer(base, docdate)
        if random.random() < 0.01:
            cardcode = "C99999"            # Problem 3: customer not in OCRD

        doctotal = 0.0
        for linenum, item in enumerate(random.sample(item_list, k=random.randint(1, 5))):
            qty = random.randint(1, 2) if item["salunitmsr"] == "Pal" else random.randint(1, 20)
            price = round(item["listprice"] * price_factor(docdate) * (1 - discount.get(cardcode, 0.0)), 2)
            linetotal = round(qty * price, 2)
            doctotal += linetotal
            lines.append({
                "docentry":  docentry,
                "linenum":   linenum,                # B1 counts lines from 0
                "itemcode":  item["itemcode"],
                "quantity":  qty,                    # in sales units
                "unitmsr":   item["salunitmsr"],
                "numpermsr": item["numinsale"],
                "price":     price,                  # per sales unit
                "linetotal": linetotal,
            })

        headers.append({
            "docentry":   docentry,
            "docnum":     100000 + docentry,
            "cardcode":   cardcode,
            "docdate":    docdate,
            "docduedate": duedate,
            "docstatus":  "C" if duedate <= REFERENCE_DATE else "O",
            "canceled":   "Y" if random.random() < 0.02 else "N",
            "doctotal":   round(doctotal, 2),
            "updatedate": min(docdate + timedelta(days=random.randint(0, 10)), REFERENCE_DATE),
        })
    return pd.DataFrame(headers), pd.DataFrame(lines)


# --- Invoices -----------------------------------------------------------
def make_invoices(ordr: pd.DataFrame, rdr1: pd.DataFrame, items: pd.DataFrame):
    """OINV (headers) and INV1 (lines): one invoice per delivered, not canceled order."""
    cost_per_piece = items.set_index("itemcode")["avgprice"].to_dict()
    delivered = ordr[(ordr["canceled"] == "N") & (ordr["docduedate"] <= REFERENCE_DATE)]
    order_lines = rdr1.groupby("docentry")

    headers, lines = [], []
    for docentry, order in enumerate(delivered.itertuples(index=False), start=1):
        problem = SUPPLY_PROBLEM[0] <= order.docduedate <= SUPPLY_PROBLEM[1]
        partial_rate = 0.30 if problem else 0.04
        doctotal = 0.0
        for linenum, ol in enumerate(order_lines.get_group(order.docentry).itertuples(index=False)):
            qty = ol.quantity
            if qty > 1 and random.random() < partial_rate:
                qty = random.randint(max(1, qty // 3), qty - 1)      # partial delivery
            linetotal = round(qty * ol.price, 2)
            doctotal += linetotal
            lines.append({
                "docentry":   docentry,
                "linenum":    linenum,
                "basetype":   17,                    # 17 = based on a sales order
                "baseentry":  order.docentry,
                "baseline":   ol.linenum,
                "itemcode":   ol.itemcode,
                "quantity":   qty,
                "unitmsr":    ol.unitmsr,
                "numpermsr":  ol.numpermsr,
                "price":      ol.price,
                "linetotal":  linetotal,
                "stockprice": cost_per_piece[ol.itemcode],   # cost per piece
            })
        headers.append({
            "docentry":   docentry,
            "docnum":     200000 + docentry,
            "cardcode":   order.cardcode,
            "docdate":    order.docduedate,          # invoiced on delivery
            "docduedate": order.docduedate + timedelta(days=30),
            "canceled":   "N",
            "doctotal":   round(doctotal, 2),
            "updatedate": order.docduedate,
        })
    return pd.DataFrame(headers), pd.DataFrame(lines)



def main():
    Faker.seed(SEED)             # seed at run time, not at import time
    random.seed(SEED)
    ensure_database(SOURCE_DB)
    engine = get_engine(SOURCE_DB)

    customers = make_customers()
    customers = pd.concat([customers, make_special_customers(customers)], ignore_index=True)
    items = make_items()
    ordr, rdr1 = make_orders(customers, items, N_ORDERS)
    oinv, inv1 = make_invoices(ordr, rdr1, items)

    tables = {
        "ocrd": customers,
        "oitb": make_item_groups(),
        "oitm": items.drop(columns=["listprice"]),     # B1 keeps prices in a price list, not in OITM
        "ordr": ordr,
        "rdr1": rdr1,
        "oinv": oinv,
        "inv1": inv1,
    }
    for name, df in tables.items():
        df.to_sql(name, engine, if_exists="replace", index=False, method=copy_rows)
        print(f"{name}: {len(df)} rows written to {SOURCE_DB}")


if __name__ == "__main__":
    main()
