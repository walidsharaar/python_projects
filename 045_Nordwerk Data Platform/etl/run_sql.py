"""
Run .sql files against nordwerk_dwh.

run_sql_path()  - every file in its own transaction (setup, MDM)
run_layer()     - all files of a layer on ONE open connection, NOT committed:
                  the caller checks the data first and then commits or rolls back.

Usage:  python -m etl.run_sql sql/00_setup
        python -m etl.run_sql sql/00_setup/01_schemas.sql
"""
import sys
from pathlib import Path

from etl.db import get_engine
from etl.runlog import get_logger

log = get_logger()


def sql_files(path: Path) -> list[Path]:
    path = Path(path)
    return sorted(path.glob("*.sql")) if path.is_dir() else [path]


def run_sql_path(path) -> None:
    """Each file is committed on its own."""
    engine = get_engine()
    for file in sql_files(path):
        conn = engine.raw_connection()      # plain driver connection: allows several statements
        try:
            with conn.cursor() as cur:
                cur.execute(file.read_text(encoding="utf-8"))
            conn.commit()
            log.info("ok: %s", file.relative_to(file.parents[2]))
        except Exception:
            conn.rollback()
            log.error("FAILED: %s", file)
            raise
        finally:
            conn.close()


def run_layer(conn, path) -> None:
    """Run all files of a layer in the open transaction of conn. Does not commit."""
    for file in sql_files(path):
        try:
            with conn.cursor() as cur:
                cur.execute(file.read_text(encoding="utf-8"))
            log.info("ok: %s", file.relative_to(file.parents[2]))
        except Exception:
            log.error("FAILED: %s", file)
            raise


if __name__ == "__main__":
    run_sql_path(sys.argv[1])
