"""Bronze: column names, schema contract and the three extractors."""
import pandas as pd
import pytest

from etl import load_bronze
from etl.load_bronze import TECH_COLUMNS, SchemaDriftError, check_schema, clean_column


# ---------------------------------------------------------------- column names
@pytest.mark.parametrize("raw, expected", [
    ("Stück je Einheit", "stueck_je_einheit"),
    ("  Größe (cm) ", "groesse_cm"),
    ("Artikel-Nr.", "artikel_nr"),
    ("Gültig ab", "gueltig_ab"),
    ("CardCode", "cardcode"),
    ("a__b", "a_b"),
])
def test_clean_column(raw, expected):
    assert clean_column(raw) == expected


def test_clean_column_is_idempotent():
    once = clean_column("Stück je Einheit")
    assert clean_column(once) == once


# ---------------------------------------------------------------- schema contract
KNOWN = ["kundennr", "kundenname", "plz", *TECH_COLUMNS]


def test_first_load_accepts_any_schema():
    df = pd.DataFrame(columns=["a", "b"])
    assert list(check_schema(df, [], "x").columns) == ["a", "b"]


def test_same_schema_passes_unchanged():
    df = pd.DataFrame([["K-1", "Shop", "01067"]], columns=["kundennr", "kundenname", "plz"])
    pd.testing.assert_frame_equal(check_schema(df, KNOWN, "erp_b_kunden"), df)


def test_missing_column_stops_the_load():
    df = pd.DataFrame(columns=["kundennr", "kundenname"])
    with pytest.raises(SchemaDriftError, match=r"erp_b_kunden.*plz"):
        check_schema(df, KNOWN, "erp_b_kunden")


def test_new_column_is_dropped_and_logged(caplog):
    df = pd.DataFrame(columns=["kundennr", "kundenname", "plz", "email"])
    with caplog.at_level("WARNING", logger="nordwerk"):
        out = check_schema(df, KNOWN, "erp_b_kunden")
    assert list(out.columns) == ["kundennr", "kundenname", "plz"]
    assert "email" in caplog.text


def test_column_order_follows_the_history_table():
    df = pd.DataFrame(columns=["plz", "kundennr", "kundenname"])
    assert list(check_schema(df, KNOWN, "t").columns) == ["kundennr", "kundenname", "plz"]


# ---------------------------------------------------------------- extractors
@pytest.fixture()
def landing(tmp_path, monkeypatch):
    monkeypatch.setattr(load_bronze, "LANDING", tmp_path)
    (tmp_path / "company_b").mkdir()
    (tmp_path / "sustainability").mkdir()
    return tmp_path


def test_csv_is_read_as_text_with_german_format(landing):
    content = "Kundennr;Kundenname;PLZ;Betrag\nK-4001;Müller & Söhne;01067;12,50\n"
    (landing / "company_b" / "kunden.csv").write_bytes(content.encode("cp1252"))
    df = load_bronze.extract_company_b("kunden")
    assert df.loc[0, "Kundenname"] == "Müller & Söhne"      # Windows-1252 decoded
    assert df.loc[0, "PLZ"] == "01067"                       # leading zero kept
    assert df.loc[0, "Betrag"] == "12,50"                    # not interpreted in bronze


def test_csv_empty_values_stay_empty_strings(landing):
    (landing / "company_b" / "artikel.csv").write_bytes("Artikelnr;EAN\nMB-0001;\n".encode("cp1252"))
    assert load_bronze.extract_company_b("artikel").loc[0, "EAN"] == ""


def test_excel_skips_the_title_rows(landing):
    path = landing / "sustainability" / "rezyklatanteile.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"Artikelnr": ["A00001"], "Rezyklatanteil": ["45 %"]}).to_excel(
            writer, sheet_name="Rezyklat", startrow=3, index=False)
        writer.sheets["Rezyklat"]["A1"] = "Titel"
    df = load_bronze.extract_excel()
    assert list(df.columns) == ["Artikelnr", "Rezyklatanteil"]
    assert df.loc[0, "Rezyklatanteil"] == "45 %"
