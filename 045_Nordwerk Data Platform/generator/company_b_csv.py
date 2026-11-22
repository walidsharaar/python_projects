"""
Source system simulator: Company B (Nordwerk Beutel GmbH), another ERP.
Exports CSV files the way many German ERPs do:
  ';' as separator, decimal comma, dates as dd.mm.yyyy, Windows-1252 encoding.
Files: kunden.csv, artikel.csv, verkaeufe.csv (one row per invoice line)

Patterns: summer peak for bin bags, about 12 % growth per year, 3 % price increase every
January. 60 shops also buy from Company A (same market list, different customer numbers).
"""
import random
from pathlib import Path

import pandas as pd
from faker import Faker

from generator.common import market, price_factor, weighted_dates

SEED = 7
N_INVOICES = 1800
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "landing" / "company_b"

SEASON = [0.85, 0.85, 0.95, 1.05, 1.15, 1.25, 1.30, 1.25, 1.05, 0.95, 0.90, 0.95]
GROWTH = 0.12

fake = Faker("de_DE")        # the seed is set in main(), at run time



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
    """Kunden: market shops 141-200 (also Company A customers) plus 201-280 (only Company B)."""
    shops = market()
    rows = [{"Kundenname": vary_name(s["name"]), "Ort": s["city"], "PLZ": s["zipcode"]} for s in shops[140:200]]
    # Problem: a typo in one postcode, so automatic matching with Company A fails (K-4011).
    # The master data team resolves it with a manual override (sql/10_mdm/02_kunde_override.sql).
    rows[10]["PLZ"] = rows[10]["PLZ"][:-2] + rows[10]["PLZ"][-1] + rows[10]["PLZ"][-2]
    rows += [{"Kundenname": s["name"], "Ort": s["city"], "PLZ": s["zipcode"]} for s in shops[200:280]]
    rows.append({"Kundenname": "Nordwerk Haushalt GmbH", "Ort": "Köln", "PLZ": "50667"})   # intercompany
    customers = pd.DataFrame(rows)
    customers.insert(0, "Kundennr", [f"K-{4001 + i}" for i in range(len(customers))])
    return customers


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
            cost = round(random.uniform(0.80, 3.50), 2)
            rows.append({
                "Artikelnr":        f"MB-{n:04d}",
                "Bezeichnung":      f"Müllbeutel {line} {size}",
                "EAN":              fake.ean13() if random.random() > 0.10 else "",   # ~10 % missing
                "Einheit":          unit,
                "Stück je Einheit": per_unit,
                "Einstandspreis":   cost,                                             # cost per roll
                "_listenpreis":     round(cost * per_unit * random.uniform(1.25, 1.70), 2),
            })
    return pd.DataFrame(rows)


def make_sales(customers: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """Verkäufe: flat file, one row per invoice line. RE = invoice, GS = credit note."""
    kunden = customers["Kundennr"].tolist()
    weights = [min(random.paretovariate(1.6), 15.0) for _ in kunden]
    discount = {k: round(random.uniform(0.0, 0.06), 3) for k in kunden}
    artikel = items.to_dict("records")

    rows = []
    for i, belegdatum in enumerate(weighted_dates(N_INVOICES, SEASON, GROWTH), start=1):
        kunde = random.choices(kunden, weights=weights)[0]
        belegart = "GS" if random.random() < 0.03 else "RE"
        sign = -1 if belegart == "GS" else 1          # credit notes are negative
        for item in random.sample(artikel, k=random.randint(1, 4)):
            menge = random.randint(1, 2) if item["Einheit"] == "Palette" else random.randint(1, 30)
            preis = round(item["_listenpreis"] * price_factor(belegdatum) * (1 - discount[kunde]), 2)
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
    duplicates = sales.sample(frac=0.01, random_state=SEED)       # export bug: rows exported twice
    return pd.concat([sales, duplicates], ignore_index=True)



def write_csv(df: pd.DataFrame, filename: str) -> None:
    """Write like a German ERP export: ; separator, decimal comma, dd.mm.yyyy, Windows-1252."""
    df = df.drop(columns=[c for c in df.columns if c.startswith("_")]).copy()
    for col in df.columns:
        if col.endswith("datum"):
            df[col] = df[col].map(lambda d: d.strftime("%d.%m.%Y"))
    df.to_csv(OUTPUT_DIR / filename, sep=";", decimal=",", index=False, encoding="cp1252")
    print(f"{filename}: {len(df)} rows written to {OUTPUT_DIR}")



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
