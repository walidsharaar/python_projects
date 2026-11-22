"""
Every data quality rule must find the problem it was written for.

Each test plants one defect inside a transaction, runs the rule's own check_sql from
meta.dq_rule and expects the count to go up. The transaction is rolled back afterwards.
A rule that never fires is worse than no rule - these tests prove each one works.
"""
import pytest
from sqlalchemy import text

from tests.conftest import scalar


def rule_value(conn, rule_id):
    sql = scalar(conn, "SELECT check_sql FROM meta.dq_rule WHERE rule_id = :r", r=rule_id)
    return conn.execute(text(sql)).scalar() or 0


def a_sales_row(conn):
    return conn.execute(text("SELECT * FROM silver.verkauf WHERE firma_id = 'A' LIMIT 1")).mappings().one()


DEFECTS = {
    "DQ01": ["UPDATE silver.verkauf SET kunde_key = 'A-NIEMAND' WHERE ctid = (SELECT ctid FROM silver.verkauf LIMIT 1)"],
    "DQ02": ["UPDATE silver.verkauf SET artikel_key = 'A-X0000' WHERE ctid = (SELECT ctid FROM silver.verkauf LIMIT 1)"],
    "DQ03": ["UPDATE silver.artikel SET ean = NULL WHERE artikel_key = (SELECT MIN(artikel_key) FROM silver.artikel WHERE ean IS NOT NULL)"],
    "DQ04": ["UPDATE silver.artikel SET ean = '4000000000001' WHERE artikel_key IN "
             "(SELECT artikel_key FROM silver.artikel WHERE ean IS NOT NULL ORDER BY artikel_key DESC LIMIT 2)"],
    "DQ05": ["UPDATE silver.rezyklat SET artikel_bekannt = false WHERE ctid = (SELECT ctid FROM silver.rezyklat WHERE artikel_bekannt LIMIT 1)"],
    "DQ06": ["UPDATE silver.kunde_map SET konzern_kunde_id = (SELECT konzern_kunde_id FROM silver.kunde_map WHERE kunde_key = 'A-C10002') "
             "WHERE kunde_key = 'A-C10003'"],
    "DQ07": ["DELETE FROM silver.verkauf WHERE ctid = (SELECT ctid FROM silver.verkauf WHERE firma_id = 'A' LIMIT 1)"],
    "DQ08": ["DELETE FROM silver.verkauf WHERE ctid = (SELECT ctid FROM silver.verkauf WHERE firma_id = 'B' LIMIT 1)"],
    "DQ09": ["UPDATE silver.verkauf SET umsatz_netto = umsatz_netto + 1 WHERE ctid = (SELECT ctid FROM silver.verkauf WHERE firma_id = 'A' LIMIT 1)"],
    "DQ10": ["UPDATE silver.verkauf SET kosten = NULL WHERE ctid = (SELECT ctid FROM silver.verkauf LIMIT 1)"],
    "DQ11": ["UPDATE silver.rezyklat SET rezyklat_pct = 150 WHERE ctid = (SELECT ctid FROM silver.rezyklat LIMIT 1)"],
    "DQ12": ["DELETE FROM gold.fact_verkauf WHERE ctid = (SELECT ctid FROM gold.fact_verkauf WHERE umsatz_netto > 0 LIMIT 1)"],
    "DQ13": ["DELETE FROM mdm.kunde_override",
             "UPDATE silver.kunde_map m SET konzern_kunde_id = k.konzern_kunde_id FROM mdm.konzern_kunde k, silver.kunde s "
             "WHERE m.kunde_key = 'B-K-4011' AND s.kunde_key = m.kunde_key AND k.match_key = s.match_key"],
    "DQ14": ["INSERT INTO meta.load_log (run_id, source_system, source_object, target_table, rows_loaded) "
             "SELECT run_id + 1000, source_system, source_object, target_table, rows_loaded / 2 FROM meta.load_log "
             "WHERE run_id = (SELECT MAX(run_id) FROM meta.load_log)"],
    "DQ15": ["ALTER TABLE gold.fact_verkauf DROP CONSTRAINT fact_verkauf_datum_fkey",
             "ALTER TABLE gold.fact_lieferung DROP CONSTRAINT fact_lieferung_datum_fkey",
             "DELETE FROM gold.dim_datum WHERE datum = (SELECT MAX(datum) FROM gold.fact_verkauf)"],
}


def test_every_rule_has_a_defect_test(db):
    active = {r[0] for r in db.execute(text("SELECT rule_id FROM meta.dq_rule WHERE aktiv"))}
    assert active == set(DEFECTS)


@pytest.mark.parametrize("rule_id", sorted(DEFECTS))
def test_rule_detects_its_defect(db, rule_id):
    if rule_id == "DQ14":      # the load_log row needs a run in etl_run for the FK
        db.execute(text("INSERT INTO meta.etl_run (run_id, layer, status) "
                        "SELECT MAX(run_id) + 1000, 'test', 'running' FROM meta.load_log"))
    before = rule_value(db, rule_id)
    for sql in DEFECTS[rule_id]:
        db.execute(text(sql))
    after = rule_value(db, rule_id)
    assert after > before, f"{rule_id} did not notice the planted defect ({before} -> {after})"


@pytest.mark.parametrize("rule_id, expected", [
    ("DQ01", 78), ("DQ02", 0), ("DQ03", 5), ("DQ04", 1), ("DQ05", 1), ("DQ06", 1), ("DQ07", 0),
    ("DQ08", 45), ("DQ09", 0), ("DQ10", 0), ("DQ11", 0), ("DQ12", 0), ("DQ13", 0), ("DQ15", 0),
])
def test_rule_baseline_on_test_data(db, rule_id, expected):
    """The planned problems of the test data, and nothing else."""
    assert rule_value(db, rule_id) == expected
