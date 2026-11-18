"""Data access for the dashboard.

Rules:
    - Read-only: the dashboard can never change the warehouse.
    - Only marts, facts and saved analysis results are read. No KPI is
      calculated here; if a page needs a new number, it belongs in
      sql/marts (or in an analysis script) first.
    - Results are cached, so switching the language does not query again.
    - Each query opens its own short connection and closes it at once.
      DuckDB does not allow a writer while another process has the file
      open, so a connection kept open by the dashboard would block
      src/warehouse.py and the weekly report.
"""

import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
# Default warehouse; set GTM_WAREHOUSE to use another copy (e.g. a test build)
DB_PATH = Path(os.environ.get("GTM_WAREHOUSE", ROOT / "database" / "warehouse.duckdb"))
RESULTS = ROOT / "data" / "results"


def database_exists() -> bool:
    return DB_PATH.exists()


@st.cache_data
def query(sql: str) -> pd.DataFrame:
    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql).df()


@st.cache_data
def analysis_result(name: str) -> pd.DataFrame | None:
    """Tables saved by the analysis scripts (statistics that SQL does not do well)."""
    path = RESULTS / f"{name}.parquet"
    return pd.read_parquet(path) if path.exists() else None


def reload() -> None:
    """Forget cached results, e.g. after src/warehouse.py was run again."""
    st.cache_data.clear()


def kpis() -> pd.DataFrame:
    """mart_kpi_summary, indexed by kpi_key."""
    return query("SELECT * FROM mart_kpi_summary").set_index("kpi_key")


def gtm_monthly() -> pd.DataFrame:
    return query("SELECT * FROM mart_gtm_monthly ORDER BY cohort_month")


def channels() -> pd.DataFrame:
    return query("SELECT * FROM mart_channel_performance")


def activation_curve() -> pd.DataFrame:
    return query("SELECT * FROM mart_seller_activation_curve ORDER BY won_month, window_days")


def buyer_retention() -> pd.DataFrame:
    return query("SELECT * FROM mart_buyer_retention ORDER BY cohort_month, month_number")


def executive_funnel() -> pd.DataFrame:
    return query("SELECT * FROM mart_executive_funnel ORDER BY stage_order").set_index("stage_key")


def opportunities() -> pd.DataFrame:
    return query("SELECT * FROM mart_opportunities ORDER BY priority")


def channel_scorecard() -> pd.DataFrame:
    return query("SELECT * FROM mart_channel_scorecard")


def data_quality() -> pd.DataFrame:
    return query("SELECT * FROM mart_data_quality")


def data_dates() -> dict:
    """Facts about the data itself, shown as context (not KPIs)."""
    row = query("""
        SELECT (SELECT MAX(purchased_at) FROM fct_order_items) AS data_end,
               (SELECT MIN(won_date)     FROM fct_leads)       AS tracking_start
    """).iloc[0]
    return {"data_end": row["data_end"], "tracking_start": row["tracking_start"]}
