-- Data quality rules. Each check_sql returns ONE number (rows that break the rule).
-- phase       silver = checked after silver is built, before gold is touched
--             gold   = checked after gold is built, before it is published (committed)
-- blockierend true   = the layer is rolled back, Power BI keeps the last good data
--             false  = "publish and flag": data is published, the finding is shown in the report
-- schwellwert result <= schwellwert counts as OK
INSERT INTO meta.dq_rule (rule_id, beschreibung, schwere, objekt, phase, blockierend, schwellwert, check_sql) VALUES

('DQ01', 'Verkauf mit unbekanntem Kunden', 'ERROR', 'silver.verkauf', 'silver', false, 0,
 $$SELECT COUNT(*) FROM silver.verkauf v
   LEFT JOIN silver.kunde k ON k.kunde_key = v.kunde_key
   WHERE k.kunde_key IS NULL$$),

('DQ02', 'Verkauf mit unbekanntem Artikel', 'ERROR', 'silver.verkauf', 'silver', true, 0,
 $$SELECT COUNT(*) FROM silver.verkauf v
   LEFT JOIN silver.artikel a ON a.artikel_key = v.artikel_key
   WHERE a.artikel_key IS NULL$$),

('DQ03', 'Artikel ohne EAN', 'WARN', 'silver.artikel', 'silver', false, 0,
 $$SELECT COUNT(*) FROM silver.artikel WHERE ean IS NULL$$),

('DQ04', 'EAN mehrfach vergeben', 'ERROR', 'silver.artikel', 'silver', false, 0,
 $$SELECT COUNT(*) FROM (
       SELECT ean FROM silver.artikel WHERE ean IS NOT NULL
       GROUP BY ean HAVING COUNT(*) > 1) x$$),

('DQ05', 'Rezyklatanteil für unbekannten Artikel', 'WARN', 'silver.rezyklat', 'silver', false, 0,
 $$SELECT COUNT(*) FROM silver.rezyklat WHERE NOT artikel_bekannt$$),

('DQ06', 'Kunden-Dublette innerhalb einer Firma', 'WARN', 'silver.kunde_map', 'silver', false, 0,
 $$SELECT COUNT(*) FROM (
       SELECT m.konzern_kunde_id, m.firma_id FROM silver.kunde_map m
       GROUP BY 1, 2 HAVING COUNT(*) > 1) x$$),

('DQ07', 'Zeilenabgleich Firma A: Bronze INV1 vs. Silver', 'ERROR', 'silver.verkauf', 'silver', true, 0,
 $$SELECT ABS((SELECT COUNT(*) FROM bronze.sap_b1_inv1)
            - (SELECT COUNT(*) FROM silver.verkauf WHERE firma_id = 'A'))$$),

('DQ08', 'Doppelte Zeilen im Export Firma B (entfernt)', 'WARN', 'bronze.erp_b_verkaeufe', 'silver', false, 0,
 $$SELECT (SELECT COUNT(*) FROM bronze.erp_b_verkaeufe)
        - (SELECT COUNT(*) FROM silver.verkauf WHERE firma_id = 'B')$$),

('DQ09', 'Belegsumme Firma A: Kopf vs. Summe der Positionen', 'ERROR', 'silver.verkauf', 'silver', true, 0,
 $$SELECT COUNT(*) FROM bronze.sap_b1_oinv h
   JOIN (SELECT beleg_nr, SUM(umsatz_netto) AS s FROM silver.verkauf
         WHERE firma_id = 'A' GROUP BY beleg_nr) l ON l.beleg_nr = h.docnum
   WHERE ABS(h.doctotal::numeric - l.s) > 0.01$$),

('DQ10', 'Verkauf ohne Kosten oder mit Menge 0', 'ERROR', 'silver.verkauf', 'silver', true, 0,
 $$SELECT COUNT(*) FROM silver.verkauf WHERE kosten IS NULL OR menge_stueck = 0$$),

('DQ11', 'Rezyklatanteil außerhalb 0–100 %', 'ERROR', 'silver.rezyklat', 'silver', true, 0,
 $$SELECT COUNT(*) FROM silver.rezyklat WHERE rezyklat_pct NOT BETWEEN 0 AND 100$$),

('DQ13', 'Möglicher Konzernkunde nicht zusammengeführt (gleicher Name und Ort, andere PLZ)', 'WARN', 'silver.kunde_map', 'silver', false, 0,
 $$SELECT COUNT(*) FROM (
       SELECT k.name_norm FROM silver.kunde k
       JOIN silver.kunde_map m ON m.kunde_key = k.kunde_key
       WHERE NOT k.ist_konzern
       GROUP BY k.name_norm, LOWER(k.ort)
       HAVING COUNT(DISTINCT k.firma_id) > 1
          AND COUNT(DISTINCT m.konzern_kunde_id) > 1) x$$),

('DQ14', 'Ladevolumen: max. Abweichung zum letzten veröffentlichten Lauf in %', 'ERROR', 'bronze', 'silver', true, 30,
 $$SELECT COALESCE(MAX(ROUND(100.0 * ABS(akt.rows_loaded - vor.rows_loaded) / NULLIF(vor.rows_loaded, 0))), 0)
   FROM meta.load_log akt
   JOIN LATERAL (SELECT l.rows_loaded FROM meta.load_log l
                 JOIN meta.etl_run e ON e.run_id = l.run_id AND e.status LIKE 'success%'
                 WHERE l.target_table = akt.target_table AND l.run_id < akt.run_id
                 ORDER BY l.run_id DESC LIMIT 1) vor ON true          -- compare with the last PUBLISHED load
   WHERE akt.run_id = (SELECT MAX(run_id) FROM meta.load_log)$$),

('DQ12', 'Umsatzabgleich Silver vs. Gold', 'ERROR', 'gold.fact_verkauf', 'gold', true, 0.01,
 $$SELECT ABS(COALESCE((SELECT SUM(umsatz_netto) FROM silver.verkauf), 0)
            - COALESCE((SELECT SUM(umsatz_netto) FROM gold.fact_verkauf), 0))$$),

('DQ15', 'Positionen ohne Datum im Kalender', 'ERROR', 'gold.fact_verkauf', 'gold', true, 0,
 $$SELECT COUNT(*) FROM gold.fact_verkauf f
   LEFT JOIN gold.dim_datum d ON d.datum = f.datum
   WHERE d.datum IS NULL$$)

ON CONFLICT (rule_id) DO UPDATE SET
    beschreibung = EXCLUDED.beschreibung,
    schwere      = EXCLUDED.schwere,
    objekt       = EXCLUDED.objekt,
    phase        = EXCLUDED.phase,
    blockierend  = EXCLUDED.blockierend,
    schwellwert  = EXCLUDED.schwellwert,
    check_sql    = EXCLUDED.check_sql;
