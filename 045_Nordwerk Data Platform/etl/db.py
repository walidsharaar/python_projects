"""Shared database connection. Reads credentials from .env, never from code."""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()  # searches for .env in this folder and the folders above

# Session time zone: timestamps (run log, DQ results) are shown in local time, not UTC
TIMEZONE = os.environ.get("POSTGRES_TIMEZONE", "Europe/Berlin")


def get_engine(database: str | None = None):
    """Return a SQLAlchemy engine. Default database: POSTGRES_DB from .env."""
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=database or os.environ["POSTGRES_DB"],
    )
    # jit=off: JIT compilation costs seconds per query and only pays off for very large scans
    return create_engine(url, connect_args={"options": f"-c timezone={TIMEZONE} -c jit=off"})


def copy_rows(table, conn, keys, data_iter) -> None:
    """
    Bulk load for DataFrame.to_sql(method=copy_rows): PostgreSQL COPY instead of one INSERT per row.
    pandas still creates the table and its column types; only the row transfer changes (much faster).
    """
    target = f'"{table.schema}"."{table.name}"' if table.schema else f'"{table.name}"'
    columns = ", ".join(f'"{k}"' for k in keys)
    with conn.connection.driver_connection.cursor() as cur:
        with cur.copy(f"COPY {target} ({columns}) FROM STDIN") as copy:
            for row in data_iter:
                copy.write_row(row)


def ensure_database(name: str) -> None:
    """Create a database if it does not exist yet (e.g. the simulated SAP B1 source)."""
    engine = get_engine("postgres").execution_options(isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        exists = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": name}).first()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    engine.dispose()


if __name__ == "__main__":
    with get_engine().connect() as conn:
        print(conn.execute(text("SELECT version()")).scalar())
