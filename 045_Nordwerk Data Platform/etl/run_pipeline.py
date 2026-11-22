"""
Run the whole Nordwerk pipeline in the right order with one command.

    setup -> MDM -> bronze -> silver (+ checks) -> gold (+ checks)

Silver and gold are each built in ONE transaction. Their data quality checks run
inside that transaction. If a blocking rule fails, the layer is rolled back and
Power BI keeps showing the last good data. Otherwise the layer is committed.

Usage (from the project folder):
    python -m etl.run_pipeline              # load and transform
    python -m etl.run_pipeline --generate   # re-create the source data first

Exit code: 0 = published (findings, if any, are flagged in the report)
           1 = stopped: a blocking rule failed or a step crashed
"""
import argparse
import sys
import time
from pathlib import Path

from etl import load_bronze, run_dq
from etl.db import get_engine
from etl.run_sql import run_layer, run_sql_path
from etl.runlog import finish_run, get_logger, start_run
from generator import company_a_b1, company_b_csv, sustainability_excel

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
log = get_logger()


class Blocked(Exception):
    """A blocking data quality rule failed."""


def step(name, func):
    """Run one pipeline step and log how long it took."""
    log.info("=== %s ===", name)
    start = time.perf_counter()
    result = func()
    log.info("--- %s done in %.1f s", name, time.perf_counter() - start)
    return result


def generate_sources():
    company_a_b1.main()
    company_b_csv.main()
    sustainability_excel.main()


def build_layer(engine, run_id: int, layer: str) -> list:
    """Build one layer and check it in one transaction: commit only if no blocking rule fails."""
    conn = engine.raw_connection()
    try:
        run_layer(conn, SQL_DIR / {"silver": "20_silver", "gold": "30_gold"}[layer])
        results = run_dq.check_phase(conn, layer)
        stop = run_dq.blocked(results)
        if stop:
            conn.rollback()
        else:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    run_dq.save_results(engine, run_id, results)
    if stop:
        raise Blocked(f"{layer} not published, blocking rule(s): {', '.join(stop)}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Nordwerk data pipeline")
    parser.add_argument("--generate", action="store_true",
                        help="re-create the simulated source data first")
    args = parser.parse_args()

    if args.generate:
        step("Generate sources", generate_sources)

    step("Setup", lambda: run_sql_path(SQL_DIR / "00_setup"))
    step("MDM", lambda: run_sql_path(SQL_DIR / "10_mdm"))

    engine = get_engine()
    run_id = start_run(engine)
    log.info("Pipeline run %s started", run_id)
    try:
        step("Bronze", lambda: load_bronze.main(run_id))
        silver = step("Silver + checks", lambda: build_layer(engine, run_id, "silver"))
        gold = step("Gold + checks", lambda: build_layer(engine, run_id, "gold"))
    except Blocked as exc:
        finish_run(engine, run_id, "blocked", str(exc))
        log.error("Run %s BLOCKED: %s", run_id, exc)
        sys.exit(1)
    except Exception as exc:
        finish_run(engine, run_id, "failed", str(exc)[:500])
        log.exception("Run %s FAILED", run_id)
        sys.exit(1)

    findings = [r for r in silver + gold if r.status in ("ERROR", "WARN")]
    status = "success" if not findings else "success_with_findings"
    message = None if not findings else ", ".join(f"{r.rule_id} {r.status}" for r in findings)
    finish_run(engine, run_id, status, message)
    log.info("Run %s finished: %s%s", run_id, status, f" ({message})" if message else "")
    sys.exit(0)


if __name__ == "__main__":
    main()
