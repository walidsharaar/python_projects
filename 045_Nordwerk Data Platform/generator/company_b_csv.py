"""
Source system simulator: Company B (Nordwerk Beutel GmbH), another ERP.
Exports CSV files the way many German ERPs do:
  ';' as separator, decimal comma, dates as dd.mm.yyyy, Windows-1252 encoding.
Files: kunden.csv, artikel.csv, verkaeufe.csv (one row per invoice line)
"""
import random
from pathlib import Path

import pandas as pd
from faker import Faker

from etl.db import get_engine

SEED = 7
N_SHARED_CUSTOMERS = 60      # shops that also buy from Company A
N_NEW_CUSTOMERS = 80         # shops only Company B knows
N_INVOICES = 1200
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "landing" / "company_b"

fake = Faker("de_DE")        # the seed is set in main(), at run time


# --- Customers ----------------------------------------------------------
def vary_name(name: str) -> str:
    """Same shop, written differently: typical when two systems keep master data."""
    r = random.random()
    if r < 0.3:
        return name.upper()
    if r < 0.5:
        return name.replace("&", "und")
    if r < 0.7:
        return name + " "            # trailing space
    return name


def make_customers() -> pd.DataFrame:
    """Kunden: some shops are also Company A customers, but with different numbers."""
    engine = get_engine("src_sap_b1")
    a_customers = pd.read_sql(
        "SELECT cardname, city, zipcode FROM ocrd WHERE cardcode BETWEEN 'C10001' AND 'C10200'",
        engine,
    )
    shared = a_customers.sample(N_SHARED_CUSTOMERS, random_state=SEED)

    rows = []
    for _, c in shared.iterrows():
        rows.append({"Kundenname": vary_name(c["cardname"]), "Ort": c["city"], "PLZ": c["zipcode"]})
    for _ in range(N_NEW_CUSTOMERS):
        rows.append({"Kundenname": fake.company(), "Ort": fake.city(), "PLZ": fake.postcode()})
    # Intercompany: Company B sells to Company A
    rows.append({"Kundenname": "Nordwerk Haushalt GmbH", "Ort": "Köln", "PLZ": "50667"})

    customers = pd.DataFrame(rows)
    customers.insert(0, "Kundennr", [f"K-{4001 + i}" for i in range(len(customers))])
    return customers


# --- Items --------------------------------------------------------------
LINES = ["Standard", "Extra stark", "Recycling"]
SIZES = ["10 l", "35 l", "60 l", "120 l"]
UNITS = [("Rolle", 1), ("Karton", 20), ("Karton", 40), ("Palette", 960)]


def make_items() -> pd.DataFrame:
    """Artikel: bin bags. Different unit names than Company A."""
    rows = []
    n = 0
    for line in LINES:
        for size in SIZES:
            n += 1
            unit, per_unit = random.choice(UNITS)
            rows.append({
                "Artikelnr":        f"MB-{n:04d}",
                "Bezeichnung":      f"Müllbeutel {line} {size}",
                "EAN":              fake.ean13() if random.random() > 0.10 else "",  # ~10% missing
                "Einheit":          unit,
                "Stück je Einheit": per_unit,
                "Einstandspreis":   round(random.uniform(0.80, 3.50), 2),  # cost per roll
            })
    return pd.DataFrame(rows)


# --- Sales --------------------------------------------------------------
def make_sales(customers: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Verkäufe: flat file, one row per invoice line. RE = invoice, GS = credit note."""
    rows = []
    kunden = customers["Kundennr"].tolist()
    artikel = items.to_dict("records")

    for i in range(1, N_INVOICES + 1):
        belegdatum = fake.date_between(start_date="-2y", end_date="today")
        kunde = random.choice(kunden)
        belegart = "GS" if random.random() < 0.03 else "RE"
        sign = -1 if belegart == "GS" else 1          # credit notes are negative

        for item in random.sample(artikel, k=random.randint(1, 4)):
            menge = random.randint(1, 2) if item["Einheit"] == "Palette" else random.randint(1, 30)
            preis = round(item["Einstandspreis"] * item["Stück je Einheit"] * random.uniform(1.25, 1.7), 2)
            rows.append({
                "Belegnr":     f"{belegart}-{belegdatum.year}-{i:05d}",
                "Belegart":    belegart,
                "Belegdatum":  belegdatum,
                "Kundennr":    kunde,
                "Artikelnr":   item["Artikelnr"],
                "Menge":       sign * menge,
                "Einheit":     item["Einheit"],
                "Einzelpreis": preis,
                "Nettobetrag": round(sign * menge * preis, 2),
            })

    sales = pd.DataFrame(rows)
    # Export bug: about 1% of rows exported twice
    duplicates = sales.sample(frac=0.01, random_state=SEED)
    return pd.concat([sales, duplicates], ignore_index=True)


# --- Export -------------------------------------------------------------
def write_csv(df: pd.DataFrame, filename: str) -> None:
    """Write like a German ERP export: ; separator, decimal comma, dd.mm.yyyy, Windows-1252."""
    df = df.copy()
    for col in df.columns:
        if col.endswith("datum"):
            df[col] = df[col].map(lambda d: d.strftime("%d.%m.%Y"))
    df.to_csv(OUTPUT_DIR / filename, sep=";", decimal=",", index=False, encoding="cp1252")
    print(f"{filename}: {len(df)} rows written to {OUTPUT_DIR}")


# --- Main ---------------------------------------------------------------
def main():
    Faker.seed(SEED)             # seed at run time, not at import time
    random.seed(SEED)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    customers = make_customers()
    items = make_items()
    write_csv(customers, "kunden.csv")
    write_csv(items, "artikel.csv")
    write_csv(make_sales(customers, items), "verkaeufe.csv")


if __name__ == "__main__":
    main()