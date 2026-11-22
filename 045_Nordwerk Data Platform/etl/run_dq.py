"""
Data quality checks.

A rule's check_sql returns ONE number. Result <= schwellwert -> OK, otherwise:
  blockierend = true   -> BLOCKIERT: the layer is rolled back, nothing is published
  schwere ERROR / WARN -> ERROR / WARN: published and shown in the report ("publish and flag")

check_phase() runs inside the open transaction of a layer, so it sees the new,
not yet committed data. save_results() writes the results on a separate connection,
so they are kept even if the layer is rolled back.
"""
from dataclasses import dataclass

from sqlalchemy import text

from etl.db import get_engine
from etl.runlog import get_logger

log = get_logger()


@dataclass
class DqResult:
    rule_id: str
    beschreibung: str
    wert: float
    status: str


def rate(wert, schwellwert, schwere: str, blockierend: bool) -> str:
    if wert <= schwellwert:
        return "OK"
    return "BLOCKIERT" if blockierend else schwere


def check_phase(conn, phase: str) -> list[DqResult]:
    """conn = open driver connection of the layer transaction."""
    with conn.cursor() as cur:
        cur.execute("SELECT rule_id, beschreibung, schwere, blockierend, schwellwert, check_sql "
                    "FROM meta.dq_rule WHERE aktiv AND phase = %s ORDER BY rule_id", (phase,))
        rules = cur.fetchall()
        results = []
        for rule_id, beschreibung, schwere, blockierend, schwellwert, check_sql in rules:
            cur.execute(check_sql)
            wert = cur.fetchone()[0] or 0
            status = rate(wert, schwellwert, schwere, blockierend)
            results.append(DqResult(rule_id, beschreibung, float(wert), status))
            level = {"OK": 20, "WARN": 30, "ERROR": 30, "BLOCKIERT": 40}[status]
            log.log(level, "  %-9s %s  %s: %s", status, rule_id, beschreibung, wert)
    return results


def save_results(engine, run_id: int, results: list[DqResult]) -> None:
    with engine.begin() as conn:
        for r in results:
            conn.execute(
                text("INSERT INTO meta.dq_result (run_id, rule_id, fehler_anzahl, status) "
                     "VALUES (:run_id, :rule_id, :wert, :status)"),
                {"run_id": run_id, "rule_id": r.rule_id, "wert": r.wert, "status": r.status},
            )


def blocked(results: list[DqResult]) -> list[str]:
    return [r.rule_id for r in results if r.status == "BLOCKIERT"]


def main():
    """Stand-alone: check the data as it is now, without changing it."""
    engine = get_engine()
    conn = engine.raw_connection()
    try:
        for phase in ("silver", "gold"):
            log.info("DQ phase %s", phase)
            check_phase(conn, phase)
    finally:
        conn.rollback()
        conn.close()


if __name__ == "__main__":
    main()
