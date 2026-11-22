-- The rules: what is checked, when, and what happens if it fails
CREATE TABLE IF NOT EXISTS meta.dq_rule (
    rule_id      TEXT    PRIMARY KEY,
    beschreibung TEXT    NOT NULL,
    schwere      TEXT    NOT NULL CHECK (schwere IN ('ERROR', 'WARN')),
    objekt       TEXT    NOT NULL,
    check_sql    TEXT    NOT NULL,
    aktiv        BOOLEAN NOT NULL DEFAULT true
);
-- v2: phase, blocking and threshold (ADD COLUMN IF NOT EXISTS: works on an existing v1 database)
ALTER TABLE meta.dq_rule ADD COLUMN IF NOT EXISTS phase       TEXT    NOT NULL DEFAULT 'silver'; -- silver | gold
ALTER TABLE meta.dq_rule ADD COLUMN IF NOT EXISTS blockierend BOOLEAN NOT NULL DEFAULT false;    -- true = stop, do not publish
ALTER TABLE meta.dq_rule ADD COLUMN IF NOT EXISTS schwellwert NUMERIC NOT NULL DEFAULT 0;        -- result <= threshold = OK

-- The results: one row per rule per run
CREATE TABLE IF NOT EXISTS meta.dq_result (
    run_id        INT         NOT NULL REFERENCES meta.etl_run (run_id),
    rule_id       TEXT        NOT NULL REFERENCES meta.dq_rule (rule_id),
    fehler_anzahl NUMERIC     NOT NULL,
    status        TEXT        NOT NULL,        -- OK | WARN | ERROR | BLOCKIERT
    geprueft_am   TIMESTAMPTZ NOT NULL DEFAULT now()
);
DROP VIEW IF EXISTS meta.v_dq_aktuell;                  -- recreated in 04_dq_views.sql
ALTER TABLE meta.dq_result ALTER COLUMN fehler_anzahl TYPE NUMERIC;   -- v1 had INT
