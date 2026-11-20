-- The rules: what is checked and how serious a failure is
CREATE TABLE IF NOT EXISTS meta.dq_rule (
    rule_id      TEXT    PRIMARY KEY,
    beschreibung TEXT    NOT NULL,
    schwere      TEXT    NOT NULL CHECK (schwere IN ('ERROR', 'WARN')),
    objekt       TEXT    NOT NULL,                 -- which table the rule is about
    check_sql    TEXT    NOT NULL,                 -- must return ONE number: rows breaking the rule
    aktiv        BOOLEAN NOT NULL DEFAULT true
);

-- The results: one row per rule per run
CREATE TABLE IF NOT EXISTS meta.dq_result (
    run_id        INT         NOT NULL REFERENCES meta.etl_run (run_id),
    rule_id       TEXT        NOT NULL REFERENCES meta.dq_rule (rule_id),
    fehler_anzahl INT         NOT NULL,
    status        TEXT        NOT NULL,            -- OK / WARN / ERROR
    geprueft_am   TIMESTAMPTZ NOT NULL DEFAULT now()
);