"""
Bronze layer: copy every source 1:1 into nordwerk_dwh.bronze.
- all values stored as text: no interpretation yet, that is silver's job
- technical columns: _source_system, _source_object, _run_id, _load_ts
- every run is logged in meta.etl_run and meta.load_log
"""
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from etl.db import get_engine

BASE_DIR = Path(__file__).resolve().parent.parent
LANDING = BASE_DIR / "data" / "landing"

SAP_B1_TABLES = ["ocrd", "oitb", "oitm", "ordr", "rdr1", "oinv", "inv1"]
COMPANY_B_FILES = ["kunden", "artikel", "verkaeufe"]



def extract_sap_b1(source_engine, table: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table}", source_engine)


def extract_company_b(name: str) -> pd.DataFrame:
    # dtype=str + keep_default_na=False: keep every value exactly as written in the file
    return pd.read_csv(LANDING / "company_b" / f"{name}.csv",
                       sep=";", encoding="cp1252", dtype=str, keep_default_na=False)


def extract_excel() -> pd.DataFrame:
    return pd.read_excel(LANDING / "sustainability" / "rezyklatanteile.xlsx",
                         header=3, dtype=str)


def clean_column(name: str) -> str:
    """'Stück je Einheit' -> 'stueck_je_einheit'"""
    name = name.strip().lower()
    for old, new in {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}.items():
        name = name.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "_", name).strip("_")


def load_to_bronze(df, target, source_system, source_object, run_id, load_ts, engine):
    df = df.astype("string")                          # everything as text, NULL stays NULL
    df.columns = [clean_column(c) for c in df.columns]
    df["_source_system"] = source_system
    df["_source_object"] = source_object
    df["_run_id"] = run_id
    df["_load_ts"] = load_ts

    df.to_sql(target, engine, schema="bronze", if_exists="replace", index=False)

    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO meta.load_log (run_id, source_system, source_object, target_table, rows_loaded)
                    VALUES (:run_id, :system, :object, :target, :rows)"""),
            {"run_id": run_id, "system": source_system, "object": source_object,
             "target": f"bronze.{target}", "rows": len(df)},
        )
    print(f"bronze.{target}: {len(df)} rows")



def start_run(engine) -> int:
    with engine.begin() as conn:
        return conn.execute(
            text("INSERT INTO meta.etl_run (layer, status) VALUES ('bronze', 'running') RETURNING run_id")
        ).scalar()


def finish_run(engine, run_id: int, status: str, message: str | None = None) -> None:
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE meta.etl_run SET status = :status, finished_at = now(), message = :msg "
                 "WHERE run_id = :run_id"),
            {"status": status, "msg": message, "run_id": run_id},
        )



def main():
    dwh = get_engine()                    # target: nordwerk_dwh
    sap_b1 = get_engine("src_sap_b1")     # source: Company A
    run_id = start_run(dwh)
    load_ts = datetime.now(timezone.utc)
    print(f"Run {run_id} started")

    try:
        for table in SAP_B1_TABLES:
            load_to_bronze(extract_sap_b1(sap_b1, table), f"sap_b1_{table}",
                           "sap_b1", table, run_id, load_ts, dwh)

        for name in COMPANY_B_FILES:
            load_to_bronze(extract_company_b(name), f"erp_b_{name}",
                           "erp_b", f"{name}.csv", run_id, load_ts, dwh)

        load_to_bronze(extract_excel(), "excel_rezyklat",
                       "excel", "rezyklatanteile.xlsx", run_id, load_ts, dwh)

        finish_run(dwh, run_id, "success")
        print(f"Run {run_id} finished: success")

    except Exception as exc:
        finish_run(dwh, run_id, "failed", str(exc)[:500])
        print(f"Run {run_id} FAILED: {exc}")
        raise


if __name__ == "__main__":
    main()