-- Data quality rules. Each check_sql returns the number of rows that break the rule.
-- $$ ... $$ quotes the SQL text, so we don't have to escape the ' inside it.
INSERT INTO meta.dq_rule (rule_id, beschreibung, schwere, objekt, check_sql) VALUES

('DQ01', 'Verkauf mit unbekanntem Kunden', 'ERROR', 'silver.verkauf',
 $$SELECT COUNT(*) FROM silver.verkauf v
   LEFT JOIN silver.kunde k ON k.kunde_key = v.kunde_key
   WHERE k.kunde_key IS NULL$$),

('DQ02', 'Verkauf mit unbekanntem Artikel', 'ERROR', 'silver.verkauf',
 $$SELECT COUNT(*) FROM silver.verkauf v
   LEFT JOIN silver.artikel a ON a.artikel_key = v.artikel_key
   WHERE a.artikel_key IS NULL$$),

('DQ03', 'Artikel ohne EAN', 'WARN', 'silver.artikel',
 $$SELECT COUNT(*) FROM silver.artikel WHERE ean IS NULL$$),

('DQ04', 'EAN mehrfach vergeben', 'ERROR', 'silver.artikel',
 $$SELECT COUNT(*) FROM (
       SELECT ean FROM silver.artikel WHERE ean IS NOT NULL
       GROUP BY ean HAVING COUNT(*) > 1) x$$),

('DQ05', 'Rezyklatanteil für unbekannten Artikel', 'WARN', 'silver.rezyklat',
 $$SELECT COUNT(*) FROM silver.rezyklat WHERE NOT artikel_bekannt$$),

('DQ06', 'Kunden-Dublette innerhalb einer Firma', 'WARN', 'silver.kunde_map',
 $$SELECT COUNT(*) FROM (
       SELECT m.konzern_kunde_id, m.firma_id FROM silver.kunde_map m
       GROUP BY 1, 2 HAVING COUNT(*) > 1) x$$),

('DQ07', 'Zeilenabgleich Firma A: Bronze INV1 vs. Silver', 'ERROR', 'silver.verkauf',
 $$SELECT ABS((SELECT COUNT(*) FROM bronze.sap_b1_inv1)
            - (SELECT COUNT(*) FROM silver.verkauf WHERE firma_id = 'A'))$$),

('DQ08', 'Doppelte Zeilen im Export Firma B (entfernt)', 'WARN', 'bronze.erp_b_verkaeufe',
 $$SELECT (SELECT COUNT(*) FROM bronze.erp_b_verkaeufe)
        - (SELECT COUNT(*) FROM silver.verkauf WHERE firma_id = 'B')$$),

('DQ09', 'Belegsumme Firma A: Kopf vs. Summe der Positionen', 'ERROR', 'silver.verkauf',
 $$SELECT COUNT(*) FROM bronze.sap_b1_oinv h
   JOIN (SELECT beleg_nr, SUM(umsatz_netto) AS s FROM silver.verkauf
         WHERE firma_id = 'A' GROUP BY beleg_nr) l ON l.beleg_nr = h.docnum
   WHERE ABS(h.doctotal::numeric - l.s) > 0.01$$),

('DQ10', 'Verkauf ohne Kosten oder mit Menge 0', 'ERROR', 'silver.verkauf',
 $$SELECT COUNT(*) FROM silver.verkauf WHERE kosten IS NULL OR menge_stueck = 0$$),

('DQ11', 'Rezyklatanteil außerhalb 0–100 %', 'ERROR', 'silver.rezyklat',
 $$SELECT COUNT(*) FROM silver.rezyklat WHERE rezyklat_pct NOT BETWEEN 0 AND 100$$)

-- Running the file again updates existing rules instead of failing
ON CONFLICT (rule_id) DO UPDATE SET
    beschreibung = EXCLUDED.beschreibung,
    schwere      = EXCLUDED.schwere,
    objekt       = EXCLUDED.objekt,
    check_sql    = EXCLUDED.check_sql;