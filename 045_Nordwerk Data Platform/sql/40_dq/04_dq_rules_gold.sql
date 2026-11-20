-- Reconciliation silver -> gold: the same revenue must arrive in the fact table
INSERT INTO meta.dq_rule (rule_id, beschreibung, schwere, objekt, check_sql) VALUES
('DQ12', 'Umsatzabgleich Silver vs. Gold', 'ERROR', 'gold.fact_verkauf',
 $$SELECT CASE WHEN (SELECT SUM(umsatz_netto) FROM silver.verkauf)
                  = (SELECT SUM(umsatz_netto) FROM gold.fact_verkauf)
          THEN 0 ELSE 1 END$$)
ON CONFLICT (rule_id) DO UPDATE SET
    beschreibung = EXCLUDED.beschreibung,
    schwere      = EXCLUDED.schwere,
    objekt       = EXCLUDED.objekt,
    check_sql    = EXCLUDED.check_sql;