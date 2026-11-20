-- Layers of the data platform
CREATE SCHEMA IF NOT EXISTS bronze;   -- raw copies of the sources
CREATE SCHEMA IF NOT EXISTS silver;   -- cleaned and harmonised
CREATE SCHEMA IF NOT EXISTS gold;     -- star schema for reporting
CREATE SCHEMA IF NOT EXISTS meta;     -- run log, load log, data quality results

-- One row per pipeline run
CREATE TABLE IF NOT EXISTS meta.etl_run (
    run_id      SERIAL PRIMARY KEY,
    layer       TEXT        NOT NULL,
    status      TEXT        NOT NULL,          -- running / success / failed
    started_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    message     TEXT                           -- error text if it failed
);

-- One row per loaded table per run
CREATE TABLE IF NOT EXISTS meta.load_log (
    run_id        INT         NOT NULL REFERENCES meta.etl_run (run_id),
    source_system TEXT        NOT NULL,
    source_object TEXT        NOT NULL,
    target_table  TEXT        NOT NULL,
    rows_loaded   INT         NOT NULL,
    loaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);