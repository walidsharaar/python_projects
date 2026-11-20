"""
Excel file maintained by hand by the master data / sustainability team.
Recycled-material share (Rezyklatanteil) per item, for the 2030 sustainability goal.
Typical Excel problems on purpose: title rows above the table, percentages
sometimes typed as text ("45 %"), an unknown item number, several rows per item (history).
"""
import random
from datetime import date
from pathlib import Path

import pandas as pd

from etl.db import get_engine

SEED = 11
BASE_DIR = Path(__file__).resolve().parent.parent
B_ITEMS_FILE = BASE_DIR / "data" / "landing" / "company_b" / "artikel.csv"
OUTPUT_DIR = BASE_DIR / "data" / "landing" / "sustainability"
OUTPUT_FILE = OUTPUT_DIR / "rezyklatanteile.xlsx"

random.seed(SEED)


def load_items() -> pd.DataFrame:
    """Firma, Artikelnr, Bezeichnung for Company A (database) and Company B (CSV)."""
    a = pd.read_sql(
        "SELECT itemcode AS artikelnr, itemname AS bezeichnung FROM oitm",
        get_engine("src_sap_b1"),
    )
    a.insert(0, "firma", "Nordwerk Haushalt GmbH")

    b = pd.read_csv(B_ITEMS_FILE, sep=";", encoding="cp1252")[["Artikelnr", "Bezeichnung"]]
    b.columns = ["artikelnr", "bezeichnung"]
    b.insert(0, "firma", "Nordwerk Beutel GmbH")

    return pd.concat([a, b], ignore_index=True)


def recycled_share(name: str) -> int:
    """A plausible share in percent, depending on the product."""
    if "Recycling" in name:
        return random.randint(60, 85)
    if "Beutel" in name:
        return random.randint(10, 40)
    return random.randint(0, 35)


def make_sheet(items: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for it in items.itertuples(index=False):
        rows.append({
            "Firma":          it.firma,
            "Artikelnr":      it.artikelnr,
            "Bezeichnung":    it.bezeichnung,
            "Rezyklatanteil": recycled_share(it.bezeichnung),
            "Gültig ab":      date(2025, 1, 1),
            "Gepflegt von":   random.choice(["MDM", "Nachhaltigkeit"]),
        })
    df = pd.DataFrame(rows)

    # History: three items got a better share from 2026 (a second row each)
    updates = df.sample(3, random_state=SEED).copy()
    updates["Rezyklatanteil"] = (updates["Rezyklatanteil"] + 20).clip(upper=100)
    updates["Gültig ab"] = date(2026, 1, 1)

    # Problem: an item number that doesn't exist (typo)
    unknown = pd.DataFrame([{
        "Firma": "Nordwerk Haushalt GmbH", "Artikelnr": "A09999",
        "Bezeichnung": "Spülmittel Zitrone 500 ml", "Rezyklatanteil": 30,
        "Gültig ab": date(2025, 1, 1), "Gepflegt von": "MDM",
    }])

    df = pd.concat([df, updates, unknown], ignore_index=True)

    # Problem: about 10% of percentages typed as text, e.g. "45 %"
    text_rows = df.sample(frac=0.10, random_state=SEED).index
    df["Rezyklatanteil"] = df["Rezyklatanteil"].astype(object)
    df.loc[text_rows, "Rezyklatanteil"] = [f"{v} %" for v in df.loc[text_rows, "Rezyklatanteil"]]

    return df.sort_values(["Firma", "Artikelnr", "Gültig ab"]).reset_index(drop=True)



def write_excel(df: pd.DataFrame) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Rezyklat", startrow=3, index=False)  # table starts in row 4
        ws = writer.sheets["Rezyklat"]
        ws["A1"] = "Rezyklatanteile je Artikel (in %)"
        ws["A2"] = f"Stand: {date.today():%d.%m.%Y} - bitte nur Spalte D pflegen"
    print(f"rezyklatanteile.xlsx: {len(df)} rows written to {OUTPUT_DIR}")


def main():
    write_excel(make_sheet(load_items()))


if __name__ == "__main__":
    main()