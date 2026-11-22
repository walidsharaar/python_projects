"""Bronze loader against the real database, in-process: history, current view, schema contract."""
import pandas as pd
import pytest
from sqlalchemy import text

from etl.db import ensure_database
from etl.load_bronze import SchemaDriftError, load_to_bronze
from etl.runlog import start_run
from tests.conftest import scalar

TARGET = "zz_test_kunden"


@pytest.fixture()
def bronze(built_db):
    yield built_db
    with built_db.begin() as conn:
        conn.execute(text(f"DROP VIEW IF EXISTS bronze.{TARGET}"))
        conn.execute(text(f"DROP TABLE IF EXISTS bronze.{TARGET}_hist"))
        conn.execute(text("DELETE FROM meta.load_log WHERE target_table = :t"), {"t": f"bronze.{TARGET}"})


def load(engine, df):
    run_id = start_run(engine, "test")
    load_to_bronze(df, TARGET, "test", "kunden.csv", run_id, pd.Timestamp.now(tz="UTC"), engine)
    return run_id


def test_history_and_current_view(bronze):
    first = load(bronze, pd.DataFrame({"Kundennr": ["K-1", "K-2"], "PLZ": ["01067", "50667"]}))
    second = load(bronze, pd.DataFrame({"Kundennr": ["K-1"], "PLZ": ["01067"]}))
    assert scalar(bronze, f"SELECT COUNT(*) FROM bronze.{TARGET}_hist") == 3          # both loads kept
    assert scalar(bronze, f"SELECT COUNT(*) FROM bronze.{TARGET}") == 1               # view = latest
    assert scalar(bronze, f"SELECT MIN(_run_id) FROM bronze.{TARGET}") == second > first
    assert scalar(bronze, f"SELECT plz FROM bronze.{TARGET} LIMIT 1") == "01067"      # text, zero kept
    logged = scalar(bronze, "SELECT string_agg(rows_loaded::text, ',' ORDER BY run_id) FROM meta.load_log "
                            "WHERE target_table = :t", t=f"bronze.{TARGET}")
    assert logged == "2,1"


def test_schema_drift_against_existing_history(bronze):
    load(bronze, pd.DataFrame({"Kundennr": ["K-1"], "PLZ": ["01067"]}))
    with pytest.raises(SchemaDriftError):
        load(bronze, pd.DataFrame({"Kundennr": ["K-1"]}))
    load(bronze, pd.DataFrame({"Kundennr": ["K-1"], "PLZ": ["01067"], "Email": ["a@b.de"]}))
    columns = scalar(bronze, "SELECT string_agg(column_name, ',') FROM information_schema.columns "
                             "WHERE table_schema = 'bronze' AND table_name = :t", t=f"{TARGET}_hist")
    assert "email" not in columns


def test_ensure_database_is_idempotent(built_db):
    ensure_database("src_sap_b1")                 # exists already: nothing happens, no error
    ensure_database("src_sap_b1")
