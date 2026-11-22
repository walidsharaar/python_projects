"""
Shared test setup.

Three levels, chosen by folder (the marker is set automatically):
    tests/unit  -> marker "unit": no database, runs in about a second
    tests/db    -> marker "db":   reads the built warehouse; changes are rolled back
    tests/e2e   -> marker "e2e":  runs the real pipeline as a subprocess

    pytest -m unit          # only fast tests
    pytest -m "unit or db"  # no full pipeline runs except the one session build
    pytest                  # everything
"""
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text

PROJECT = Path(__file__).resolve().parent.parent


def pytest_collection_modifyitems(items):
    for item in items:
        level = Path(str(item.fspath)).parent.name
        if level in ("unit", "db", "e2e"):
            item.add_marker(getattr(pytest.mark, level))



def run_pipeline(*args) -> subprocess.CompletedProcess:
    """Run the pipeline exactly as a user would, in its own process."""
    return subprocess.run([sys.executable, "-m", "etl.run_pipeline", *args],
                          cwd=PROJECT, capture_output=True, text=True)



@pytest.fixture(scope="session")
def engine():
    from etl.db import get_engine
    eng = get_engine()
    try:
        with eng.connect():
            pass
    except Exception as exc:  # noqa: BLE001 - any connection problem means: no database here
        pytest.skip(f"PostgreSQL not reachable ({type(exc).__name__}) - start it with 'docker compose up -d'")
    return eng


@pytest.fixture(scope="session")
def built_db(engine):
    """Build the warehouse once per test session from freshly generated sources."""
    result = run_pipeline("--generate")
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-3000:]
    return engine


@pytest.fixture()
def db(built_db):
    """A connection inside a transaction that is always rolled back: tests may change anything."""
    with built_db.connect() as conn:
        tx = conn.begin()
        try:
            yield conn
        finally:
            tx.rollback()


def scalar(conn_or_engine, sql: str, **params):
    if hasattr(conn_or_engine, "connect"):
        with conn_or_engine.connect() as conn:
            return conn.execute(text(sql), params).scalar()
    return conn_or_engine.execute(text(sql), params).scalar()


def rows(conn, sql: str, **params):
    return conn.execute(text(sql), params).all()
