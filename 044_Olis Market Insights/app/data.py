"""Data access for the dashboard.

Rules:
    - Read-only connection: the dashboard can never change the warehouse.
    - Only marts and facts are read. No KPI is calculated here; if a page
      needs a new number, it belongs in sql/marts first.
    - Results are cached, so switching the language does not query again.
"""

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "warehouse.duckdb"


def database_exists() -> bool:
    return DB_PATH.exists()


@st.cache_resource
def _connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    return _connection().execute(sql).df()


def kpis() -> pd.DataFrame:
    """mart_kpi_summary, indexed by kpi_key."""
    return query("SELECT * FROM mart_kpi_summary").set_index("kpi_key")


def gtm_monthly() -> pd.DataFrame:
    return query("SELECT * FROM mart_gtm_monthly ORDER BY cohort_month")


def data_dates() -> dict:
    """Facts about the data itself, shown as context (not KPIs)."""
    row = query("""
        SELECT (SELECT MAX(purchased_at) FROM fct_order_items) AS data_end,
               (SELECT MIN(won_date)     FROM fct_leads)       AS tracking_start
    """).iloc[0]
    return {"data_end": row["data_end"], "tracking_start": row["tracking_start"]}
