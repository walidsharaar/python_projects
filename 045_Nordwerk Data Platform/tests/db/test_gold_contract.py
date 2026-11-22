"""
Contract between gold and Power BI, and the integrity of the star schema.

REPORT_CONTRACT lists every column the Power BI report (powerbi/Nordwerk.pbix) reads, with the type
Power BI expects. If someone renames or retypes a gold column, these tests fail before the report
breaks on a refresh.
"""
import pytest
from sqlalchemy import text

from tests.conftest import scalar

INT, NUM, TEXT, BOOL, DATE = ("integer", "bigint"), ("numeric", "double precision"), ("text",), ("boolean",), \
    ("date", "timestamp with time zone")

REPORT_CONTRACT = {
    "gold.dim_firma": {"firma_id": TEXT, "firma_name": TEXT, "quellsystem": TEXT},
    "gold.dim_datum": {"datum": DATE, "jahr": INT, "quartal": INT, "quartal_name": TEXT, "monat": INT,
                       "monat_name": TEXT, "jahr_monat": TEXT, "kalenderwoche": INT, "wochentag": INT,
                       "wochentag_name": TEXT, "ist_wochenende": BOOL, "ist_im_datenbereich": INT,
                       "ist_vollstaendiger_monat": INT, "datenbeginn": DATE, "datenstand": DATE},
    "gold.dim_kunde": {"kunde_sk": INT, "konzern_kunde_id": TEXT, "kundenname": TEXT, "plz": TEXT, "ort": TEXT,
                       "anzahl_firmen": INT, "firmen": TEXT, "ist_konzern": BOOL, "konzern_firma_id": TEXT},
    "gold.dim_artikel": {"artikel_sk": INT, "artikel_key": TEXT, "firma_id": TEXT, "artikelnr": TEXT,
                         "bezeichnung": TEXT, "artikelgruppe": TEXT, "ean": TEXT, "einheit": TEXT,
                         "stueck_je_einheit": INT, "kosten_je_stueck": NUM, "rezyklat_pct_aktuell": NUM},
    "gold.fact_verkauf": {"datum": DATE, "firma_id": TEXT, "kunde_sk": INT, "artikel_sk": INT, "beleg_nr": TEXT,
                          "beleg_pos": INT, "belegart": TEXT, "menge_stueck": NUM, "umsatz_netto": NUM,
                          "kosten": NUM, "deckungsbeitrag": NUM, "ist_intercompany": BOOL},
    "gold.fact_lieferung": {"datum": DATE, "firma_id": TEXT, "kunde_sk": INT, "artikel_sk": INT,
                            "auftrag_nr": TEXT, "auftrag_pos": INT, "menge_bestellt_stueck": NUM,
                            "menge_geliefert_stueck": NUM, "ist_vollstaendig_geliefert": BOOL,
                            "ist_storniert": BOOL, "ist_faellig": BOOL},
    "meta.v_dq_aktuell": {"rule_id": TEXT, "beschreibung": TEXT, "schwere": TEXT, "objekt": TEXT,
                          "fehler_anzahl": NUM, "status": TEXT, "geprueft_am": DATE, "run_id": INT,
                          "phase": TEXT, "blockierend": BOOL, "schwellwert": NUM},
}


@pytest.mark.parametrize("table", sorted(REPORT_CONTRACT))
def test_report_columns_exist_with_expected_type(db, table):
    schema, name = table.split(".")
    actual = dict(db.execute(text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = :s AND table_name = :t"), {"s": schema, "t": name}).all())
    assert actual, f"{table} does not exist"
    problems = [f"{col}: missing" if col not in actual else f"{col}: {actual[col]}"
                for col, types in REPORT_CONTRACT[table].items()
                if col not in actual or actual[col] not in types]
    assert not problems, f"{table}: " + ", ".join(problems)


@pytest.mark.parametrize("table, key", [
    ("gold.dim_kunde", "kunde_sk"), ("gold.dim_artikel", "artikel_sk"), ("gold.dim_datum", "datum"),
    ("gold.dim_firma", "firma_id"), ("gold.dim_kunde", "konzern_kunde_id"),
    ("gold.fact_verkauf", "firma_id, beleg_nr, beleg_pos"),
    ("gold.fact_lieferung", "firma_id, auftrag_nr, auftrag_pos"),
])
def test_keys_are_unique_and_not_null(db, table, key):
    dupes = scalar(db, f"SELECT COUNT(*) FROM (SELECT {key} FROM {table} GROUP BY {key} HAVING COUNT(*) > 1) x")
    nulls = scalar(db, f"SELECT COUNT(*) FROM {table} WHERE ({key}) IS NULL")
    assert (dupes, nulls) == (0, 0)


@pytest.mark.parametrize("fact", ["gold.fact_verkauf", "gold.fact_lieferung"])
@pytest.mark.parametrize("fk, dim", [("kunde_sk", "gold.dim_kunde"), ("artikel_sk", "gold.dim_artikel"),
                                     ("datum", "gold.dim_datum"), ("firma_id", "gold.dim_firma")])
def test_every_fact_row_finds_its_dimension(db, fact, fk, dim):
    orphans = scalar(db, f"SELECT COUNT(*) FROM {fact} f LEFT JOIN {dim} d USING ({fk}) "
                         f"WHERE d.{fk} IS NULL OR f.{fk} IS NULL")
    assert orphans == 0


@pytest.mark.parametrize("dim, key", [("gold.dim_kunde", "kunde_sk"), ("gold.dim_artikel", "artikel_sk")])
def test_unknown_member_exists(db, dim, key):
    assert scalar(db, f"SELECT COUNT(*) FROM {dim} WHERE {key} = -1") == 1


def test_surrogate_key_matches_group_customer_id(db):
    """kunde_sk is the number of the stable group id: GK00042 -> 42."""
    bad = scalar(db, "SELECT COUNT(*) FROM gold.dim_kunde WHERE kunde_sk <> -1 "
                     "AND kunde_sk <> SUBSTRING(konzern_kunde_id FROM 3)::int")
    assert bad == 0


# ---------------------------------------------------------------- calendar
def test_calendar_is_continuous_and_covers_all_facts(db):
    days, first, last = db.execute(text(
        "SELECT COUNT(*), MIN(datum), MAX(datum) FROM gold.dim_datum")).one()
    assert days == (last - first).days + 1
    f_first, f_last = db.execute(text("SELECT MIN(datum), MAX(datum) FROM gold.fact_lieferung")).one()
    assert first <= f_first and f_last <= last


def test_complete_month_flags(db):
    """Only months fully inside the data range count as complete (no misleading partial months)."""
    partial = db.execute(text(
        "SELECT jahr_monat FROM gold.dim_datum WHERE ist_vollstaendiger_monat = 1 "
        "GROUP BY jahr_monat HAVING MIN(datum) < MIN(datenbeginn) OR MAX(datum) > MAX(datenstand)")).all()
    assert partial == []
    assert scalar(db, "SELECT MAX(ist_vollstaendiger_monat) FROM gold.dim_datum WHERE jahr_monat = '2026-11'") == 0
    assert scalar(db, "SELECT MIN(ist_vollstaendiger_monat) FROM gold.dim_datum WHERE jahr_monat = '2025-11'") == 1



def test_margin_equals_revenue_minus_cost(db):
    assert scalar(db, "SELECT COUNT(*) FROM gold.fact_verkauf "
                      "WHERE ABS(deckungsbeitrag - (umsatz_netto - kosten)) > 0.005") == 0


def test_intercompany_flag_matches_customer(db):
    bad = scalar(db, "SELECT COUNT(*) FROM gold.fact_verkauf f JOIN gold.dim_kunde k USING (kunde_sk) "
                     "WHERE f.ist_intercompany <> COALESCE(k.ist_konzern, false)")
    assert bad == 0


def test_delivered_never_more_than_ordered(db):
    assert scalar(db, "SELECT COUNT(*) FROM gold.fact_lieferung "
                      "WHERE menge_geliefert_stueck > menge_bestellt_stueck") == 0


def test_quantities_are_in_pieces(db):
    """A pallet line must be at least 480 pieces: units were converted."""
    assert scalar(db, "SELECT MIN(f.menge_stueck) FROM gold.fact_verkauf f JOIN gold.dim_artikel a USING (artikel_sk) "
                      "WHERE a.einheit = 'PAL' AND f.menge_stueck > 0") >= 480


def test_one_unit_vocabulary(db):
    units = {r[0] for r in db.execute(text("SELECT DISTINCT einheit FROM gold.dim_artikel WHERE artikel_sk <> -1"))}
    assert units == {"STK", "KRT", "PAL"}
