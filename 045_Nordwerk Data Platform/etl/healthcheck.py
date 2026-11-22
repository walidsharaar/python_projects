"""
Health check after a pipeline run: runs sql/checks/healthcheck.sql and prints target vs. actual.

    python -m etl.healthcheck        # exit code 0 = all OK, 1 = at least one line to check
"""
import sys
from pathlib import Path

from etl.db import get_engine

SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "checks" / "healthcheck.sql"


def run_checks(engine=None) -> list[tuple]:
    """Returns (check, actual, expected, result) per line."""
    conn = (engine or get_engine()).raw_connection()      # driver level: the SQL contains '%'
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_FILE.read_text(encoding="utf-8"))
            return cur.fetchall()
    finally:
        conn.rollback()
        conn.close()


def main() -> int:
    results = run_checks()
    width = max(len(r[0]) for r in results)
    print(f"{'Prüfung':<{width}}  {'Ist':>14}  {'Soll':>14}  Ergebnis")
    for check, actual, expected, result in results:
        print(f"{check:<{width}}  {actual!s:>14}  {expected!s:>14}  {result}")
    failed = [r for r in results if r[3] != "OK"]
    print(f"\n{len(results) - len(failed)} of {len(results)} OK")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
