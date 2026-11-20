"""
Data quality checks: run every active rule from meta.dq_rule, write results to meta.dq_result.
A rule's check_sql returns ONE number: how many rows break the rule (0 = OK).
If any ERROR rule fails, the run is marked 'failed'.
"""
from sqlalchemy import text

from etl.db import get_engine


def main():
    engine = get_engine()

    with engine.begin() as conn:
        run_id = conn.execute(
            text("INSERT INTO meta.etl_run (layer, status) VALUES ('dq', 'running') RETURNING run_id")
        ).scalar()
        rules = conn.execute(
            text("SELECT rule_id, beschreibung, schwere, check_sql FROM meta.dq_rule "
                 "WHERE aktiv ORDER BY rule_id")
        ).all()

    print(f"DQ run {run_id}: {len(rules)} rules")
    failed_errors = 0

    for rule in rules:
        with engine.begin() as conn:
            count = conn.execute(text(rule.check_sql)).scalar()
            status = "OK" if count == 0 else rule.schwere
            conn.execute(
                text("INSERT INTO meta.dq_result (run_id, rule_id, fehler_anzahl, status) "
                     "VALUES (:run_id, :rule_id, :count, :status)"),
                {"run_id": run_id, "rule_id": rule.rule_id, "count": count, "status": status},
            )
        if status == "ERROR":
            failed_errors += 1
        print(f"  {status:<5} {rule.rule_id}  {rule.beschreibung}: {count}")

    run_status = "success" if failed_errors == 0 else "failed"
    message = None if failed_errors == 0 else f"{failed_errors} rule(s) with status ERROR"
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE meta.etl_run SET status = :status, finished_at = now(), message = :msg "
                 "WHERE run_id = :run_id"),
            {"status": run_status, "msg": message, "run_id": run_id},
        )
    print(f"DQ run {run_id}: {run_status}" + (f" ({message})" if message else ""))


if __name__ == "__main__":
    main()