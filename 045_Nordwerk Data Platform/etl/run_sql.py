"""
Run .sql files against nordwerk_dwh.

"""
import sys
from pathlib import Path

from etl.db import get_engine


def run_sql_path(path: str) -> None:
    path = Path(path)
    files = sorted(path.glob("*.sql")) if path.is_dir() else [path]
    engine = get_engine()

    for file in files:
        sql = file.read_text(encoding="utf-8")
        conn = engine.raw_connection()      # plain driver connection: allows several statements
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"ok: {file}")
        except Exception:
            conn.rollback()
            print(f"FAILED: {file}")
            raise
        finally:
            conn.close()


if __name__ == "__main__":
    run_sql_path(sys.argv[1])