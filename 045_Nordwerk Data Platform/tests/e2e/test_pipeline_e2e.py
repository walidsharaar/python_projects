"""
End-to-end: the real pipeline, started as a user would start it, against the real database.

Scenarios
  1. clean build          generate -> all layers -> reference numbers and DQ findings
  2. rerun                same result, same keys, bronze keeps history (idempotency)
  3. fix at the source    master data corrected in SAP -> findings disappear
  4. bad delivery         half the invoice lines missing -> blocked, gold unchanged
  5. schema change        a source column disappears -> stopped with a clear message
  6. manual MDM match     without the override the duplicate is reported (DQ13)
  7. blocking rule        any blocking rule keeps the last good gold
Scenarios that change the sources restore them afterwards with --generate.
"""
import pytest
from sqlalchemy import text

from etl.load_bronze import KEEP_RUNS
from tests.conftest import run_pipeline, scalar

GOLD_FINGERPRINT = """
    SELECT md5(string_agg(x, '|' ORDER BY x)) FROM (
        SELECT concat_ws(',', firma_id, beleg_nr, beleg_pos, kunde_sk, artikel_sk, umsatz_netto, kosten) AS x
        FROM gold.fact_verkauf) t"""


def sap(engine, sql):
    """Change the simulated SAP Business One database."""
    from etl.db import get_engine
    with get_engine("src_sap_b1").begin() as conn:
        conn.execute(text(sql))


def last_run(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT status, message FROM meta.etl_run "
                                 "WHERE layer = 'pipeline' ORDER BY run_id DESC LIMIT 1")).one()


def dq(engine, rule_id):
    return scalar(engine, "SELECT status FROM meta.v_dq_aktuell WHERE rule_id = :r", r=rule_id)


@pytest.fixture()
def restore_sources(built_db):
    yield built_db
    result = run_pipeline("--generate")
    assert result.returncode == 0, result.stdout[-2000:]



@pytest.mark.parametrize("sql, expected", [
    ("SELECT COUNT(*) FROM gold.fact_verkauf", 14910),
    ("SELECT COUNT(*) FROM gold.fact_lieferung", 10745),
    ("SELECT COUNT(*) FROM gold.dim_kunde", 284),
    ("SELECT COUNT(*) FROM gold.dim_artikel", 58),
    ("SELECT COUNT(*) FROM gold.dim_datum", 1826),
    ("SELECT COUNT(*) FROM silver.kunde_map", 344),
    ("SELECT COUNT(DISTINCT konzern_kunde_id) FROM silver.kunde_map", 283),
    ("SELECT ROUND(SUM(umsatz_netto)) FROM gold.fact_verkauf WHERE NOT ist_intercompany "
     "AND datum BETWEEN '2025-01-01' AND '2025-12-31'", 4678909),
])
def test_clean_build_reference_numbers(built_db, sql, expected):
    assert scalar(built_db, sql) == expected


def test_clean_build_status_and_findings(built_db):
    status, message = last_run(built_db)
    assert status == "success_with_findings"
    assert message == "DQ01 ERROR, DQ03 WARN, DQ04 ERROR, DQ05 WARN, DQ06 WARN, DQ08 WARN"


def test_every_source_load_is_logged(built_db):
    loaded = scalar(built_db, "SELECT COUNT(*) FROM meta.load_log WHERE run_id = "
                              "(SELECT MAX(run_id) FROM meta.load_log)")
    assert loaded == 11                     # 7 SAP tables + 3 CSV files + 1 Excel


def test_healthcheck_all_ok(built_db):
    from etl.healthcheck import run_checks
    results = run_checks(built_db)
    assert len(results) == 14
    assert [r[0] for r in results if r[3] != "OK"] == []



def test_rerun_is_idempotent_and_keys_stay_stable(built_db):
    keys = "SELECT string_agg(konzern_kunde_id || ':' || kunde_sk, ',' ORDER BY kunde_sk) FROM gold.dim_kunde"
    before = (scalar(built_db, GOLD_FINGERPRINT), scalar(built_db, keys))
    assert run_pipeline().returncode == 0
    assert (scalar(built_db, GOLD_FINGERPRINT), scalar(built_db, keys)) == before


def test_bronze_keeps_only_the_last_loads(built_db):
    for _ in range(KEEP_RUNS):
        assert run_pipeline().returncode == 0
    loads = scalar(built_db, "SELECT COUNT(DISTINCT _run_id) FROM bronze.sap_b1_inv1_hist")
    current = scalar(built_db, "SELECT COUNT(DISTINCT _run_id) FROM bronze.sap_b1_inv1")
    assert (loads, current) == (KEEP_RUNS, 1)



def test_fix_at_source_clears_findings(restore_sources):
    engine = restore_sources
    sap(engine, "INSERT INTO ocrd (cardcode, cardname, cardtype, city, zipcode, country, createdate, updatedate) "
                "VALUES ('C99999', 'Neukunde Muster GmbH', 'C', 'Köln', '50667', 'DE', CURRENT_DATE, CURRENT_DATE)")
    sap(engine, "UPDATE oitm SET codebars = '4012345000016' WHERE itemcode = 'A00045'")
    assert run_pipeline().returncode == 0
    assert (dq(engine, "DQ01"), dq(engine, "DQ04")) == ("OK", "OK")
    assert scalar(engine, "SELECT COUNT(*) FROM gold.fact_verkauf WHERE kunde_sk = -1") == 0



def test_bad_delivery_is_blocked_and_gold_kept(restore_sources):
    engine = restore_sources
    before = scalar(engine, GOLD_FINGERPRINT)
    sap(engine, "DELETE FROM inv1 WHERE docentry::int % 2 = 0")
    result = run_pipeline()
    assert result.returncode == 1
    assert "BLOCKIERT" in result.stderr + result.stdout
    status, message = last_run(engine)
    assert status == "blocked" and "DQ14" in message
    assert scalar(engine, GOLD_FINGERPRINT) == before



def test_missing_source_column_stops_the_load(restore_sources):
    engine = restore_sources
    before = scalar(engine, GOLD_FINGERPRINT)
    sap(engine, "ALTER TABLE ocrd DROP COLUMN zipcode")
    result = run_pipeline()
    assert result.returncode == 1
    assert "SchemaDriftError" in result.stderr + result.stdout
    assert last_run(engine).status == "failed"
    assert scalar(engine, GOLD_FINGERPRINT) == before


def test_new_source_column_is_tolerated(restore_sources):
    engine = restore_sources
    sap(engine, "ALTER TABLE ocrd ADD COLUMN email TEXT")
    result = run_pipeline()
    assert result.returncode == 0
    assert "new source columns ignored" in result.stderr + result.stdout



def test_without_override_the_duplicate_is_reported(built_db):
    with built_db.begin() as conn:
        saved = conn.execute(text("SELECT * FROM mdm.kunde_override")).mappings().all()
        conn.execute(text("DELETE FROM mdm.kunde_override"))
    try:                                   # rebuild silver only, so the MDM file does not restore the row
        from etl.run_pipeline import build_layer
        from etl.runlog import start_run
        results = build_layer(built_db, start_run(built_db, "test"), "silver")
        assert {r.rule_id: r.status for r in results}["DQ13"] == "WARN"
        ids = scalar(built_db, "SELECT COUNT(DISTINCT konzern_kunde_id) FROM silver.kunde_map "
                               "WHERE kunde_key IN ('A-C10151', 'B-K-4011')")
        assert ids == 2
    finally:
        with built_db.begin() as conn:
            for row in saved:
                conn.execute(text("INSERT INTO mdm.kunde_override VALUES "
                                  "(:kunde_key, :ziel_kunde_key, :grund, :angelegt_von, :angelegt_am) "
                                  "ON CONFLICT DO NOTHING"), dict(row))
        assert run_pipeline().returncode == 0
    assert scalar(built_db, "SELECT COUNT(DISTINCT konzern_kunde_id) FROM silver.kunde_map "
                            "WHERE kunde_key IN ('A-C10151', 'B-K-4011')") == 1



def test_any_blocking_rule_keeps_last_good_gold(built_db):
    before = scalar(built_db, GOLD_FINGERPRINT)
    with built_db.begin() as conn:
        conn.execute(text("INSERT INTO meta.dq_rule (rule_id, beschreibung, schwere, objekt, phase, "
                          "blockierend, check_sql) VALUES ('DQ99', 'Test: fails in gold', 'ERROR', "
                          "'test', 'gold', true, 'SELECT 1')"))
    try:
        assert run_pipeline().returncode == 1
        assert last_run(built_db).status == "blocked"
        assert scalar(built_db, GOLD_FINGERPRINT) == before
    finally:
        with built_db.begin() as conn:
            conn.execute(text("DELETE FROM meta.dq_result WHERE rule_id = 'DQ99'"))
            conn.execute(text("DELETE FROM meta.dq_rule WHERE rule_id = 'DQ99'"))
        assert run_pipeline().returncode == 0
