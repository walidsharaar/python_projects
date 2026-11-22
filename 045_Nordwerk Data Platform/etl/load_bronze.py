"""
Bronze layer: copy every source 1:1 into nordwerk_dwh.bronze.

- all values stored as text: no interpretation yet, that is silver's job
- technical columns: _source_system, _source_object, _run_id, _load_ts
- append-only history: bronze.<name>_hist keeps the last KEEP_RUNS loads,
  the view bronze.<name> always shows the latest load (silver reads the view)
- schema check: a source column that disappears stops the load,
  a new source column is logged and ignored until silver is adapted
- every table load is logged in meta.load_log
"""
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.db import copy_rows, get_engine
from etl.runlog import finish_run, get_logger, start_run

log = get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent
LANDING = BASE_DIR / "data" / "landing"
KEEP_RUNS = 5

SAP_B1_TABLES = ["ocrd", "oitb", "oitm", "ordr", "rdr1", "oinv", "inv1"]
COMPANY_B_FILES = ["kunden", "artikel", "verkaeufe"]
TECH_COLUMNS = ["_source_system", "_source_object", "_run_id", "_load_ts"]


class SchemaDriftError(Exception):
    """A source no longer delivers a column that bronze/silver expects."""


def extract_sap_b1(source_engine, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table}", source_engine)


def extract_company_b(name: str) -> pd.DataFrame:
    return pd.read_csv(LANDING / "company_b" / f"{name}.csv",
                       sep=";", encoding="cp1252", dtype=str, keep_default_na=False)


def extract_excel() -> pd.DataFrame:
    return pd.read_excel(LANDING / "sustainability" / "rezyklatanteile.xlsx", header=3, dtype=str)


def clean_column(name: str) -> str:
    """'Stück je Einheit' -> 'stueck_je_einheit'"""
    name = name.strip().lower()
    for old, new in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        name = name.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def existing_columns(conn, table: str) -> list[str]:
    return conn.execute(
        text("SELECT column_name FROM information_schema.columns "
             "WHERE table_schema = 'bronze' AND table_name = :t ORDER BY ordinal_position"),
        {"t": table},
    ).scalars().all()


def check_schema(df: pd.DataFrame, known: list[str], target: str) -> pd.DataFrame:
    """Compare the incoming columns with the history table. Returns the columns to load."""
    if not known:                                    # first load: the source defines the schema
        return df
    expected = [c for c in known if c not in TECH_COLUMNS]
    missing = [c for c in expected if c not in df.columns]
    new = [c for c in df.columns if c not in expected]
    if missing:
        raise SchemaDriftError(f"bronze.{target}: source no longer delivers {missing}")
    if new:
        log.warning("bronze.%s: new source columns ignored until silver uses them: %s", target, new)
    return df[expected]


def load_to_bronze(df, target, source_system, source_object, run_id, load_ts, engine):
    hist = f"{target}_hist"
    df = df.astype("string")
    df.columns = [clean_column(c) for c in df.columns]

    with engine.begin() as conn:
        # v1 kept bronze as plain tables with this name: replace them by views once
        is_table = conn.execute(
            text("SELECT 1 FROM information_schema.tables WHERE table_schema = 'bronze' "
                 "AND table_name = :t AND table_type = 'BASE TABLE'"), {"t": target}).first()
        if is_table:
            conn.execute(text(f'DROP TABLE bronze."{target}"'))
        df = check_schema(df, existing_columns(conn, hist), target)

    df["_source_system"] = source_system
    df["_source_object"] = source_object
    df["_run_id"] = run_id
    df["_load_ts"] = load_ts
    df.to_sql(hist, engine, schema="bronze", if_exists="append", index=False, method=copy_rows)

    with engine.begin() as conn:
        conn.execute(text(f'CREATE INDEX IF NOT EXISTS "ix_{hist}_run" ON bronze."{hist}" (_run_id)'))
        conn.execute(text(f'ANALYZE bronze."{hist}"'))      # fresh statistics after a bulk load: good query plans
        conn.execute(text(
            f'CREATE OR REPLACE VIEW bronze."{target}" AS '
            f'SELECT * FROM bronze."{hist}" WHERE _run_id = (SELECT MAX(_run_id) FROM bronze."{hist}")'))
        conn.execute(text(  # retention: keep the last KEEP_RUNS loads
            f'DELETE FROM bronze."{hist}" WHERE _run_id NOT IN '
            f'(SELECT DISTINCT _run_id FROM bronze."{hist}" ORDER BY _run_id DESC LIMIT {KEEP_RUNS})'))
        conn.execute(
            text("""INSERT INTO meta.load_log (run_id, source_system, source_object, target_table, rows_loaded)
                    VALUES (:run_id, :system, :object, :target, :rows)"""),
            {"run_id": run_id, "system": source_system, "object": source_object,
             "target": f"bronze.{target}", "rows": len(df)},
        )
    log.info("bronze.%s: %s rows", target, len(df))


def main(run_id: int | None = None):
    """Load all sources. Inside the pipeline the run_id comes from run_pipeline."""
    dwh = get_engine()
    sap_b1 = get_engine("src_sap_b1")
    own_run = run_id is None
    if own_run:
        run_id = start_run(dwh, "bronze")
    load_ts = datetime.now(UTC)
    try:
        for table in SAP_B1_TABLES:
            load_to_bronze(extract_sap_b1(sap_b1, table), f"sap_b1_{table}", "sap_b1", table, run_id, load_ts, dwh)
        for name in COMPANY_B_FILES:
            load_to_bronze(extract_company_b(name), f"erp_b_{name}", "erp_b", f"{name}.csv", run_id, load_ts, dwh)
        load_to_bronze(extract_excel(), "excel_rezyklat", "excel", "rezyklatanteile.xlsx", run_id, load_ts, dwh)
        if own_run:
            finish_run(dwh, run_id, "success")
    except Exception as exc:
        if own_run:
            finish_run(dwh, run_id, "failed", str(exc)[:500])
        raise


if __name__ == "__main__":
    main()
