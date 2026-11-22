"""SQL helper functions in the warehouse."""
import pytest

from tests.conftest import scalar


@pytest.mark.parametrize("raw, expected", [
    ("Müller & Söhne GmbH", "müller und söhne gmbh"),
    ("  MÜLLER   und SÖHNE GmbH ", "müller und söhne gmbh"),
    ("Straße & Co", "strasse und co"),
    ("GROSSE KG", "grosse kg"),
    ("Tab\tand\nnewline", "tab and newline"),
])
def test_norm_name(db, raw, expected):
    assert scalar(db, "SELECT silver.norm_name(:n)", n=raw) == expected


def test_norm_name_null_stays_null(db):
    assert scalar(db, "SELECT silver.norm_name(NULL)") is None


def test_calendar_names(db):
    row = db.exec_driver_sql("SELECT monat_name, wochentag_name, quartal_name, jahr_monat, kalenderwoche "
                             "FROM gold.dim_datum WHERE datum = '2026-11-20'").one()
    assert tuple(row) == ("November", "Freitag", "Q4", "2026-11", 47)


def test_weekend_flag(db):
    assert db.exec_driver_sql("SELECT COUNT(*) FROM gold.dim_datum "
                              "WHERE ist_wochenende <> (wochentag IN (6, 7))").scalar() == 0


def test_no_persian_calendar_left(db):
    """v1 objects are removed on upgrade (report is German and English only)."""
    assert db.exec_driver_sql("SELECT COUNT(*) FROM pg_proc WHERE proname = 'to_jalali'").scalar() == 0
    assert scalar(db, "SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'gold' "
                      "AND column_name LIKE :p", p="jalali%") == 0
