-- Health check: compare key results with expected values.
-- Run in the VS Code query editor. Every row should show ok = true.
SELECT pruefung, ergebnis, erwartet, ergebnis = erwartet AS ok
FROM (
    SELECT 1 AS nr, 'Bronze-Tabellen' AS pruefung,
           (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'bronze')::text AS ergebnis,
           '11' AS erwartet
    UNION ALL
    SELECT 2, 'Silver-Tabellen',
           (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'silver')::text, '7'
    UNION ALL
    SELECT 3, 'Gold-Tabellen',
           (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'gold')::text, '6'
    UNION ALL
    SELECT 4, 'Letzter Bronze-Lauf',
           (SELECT status FROM meta.etl_run WHERE layer = 'bronze' ORDER BY run_id DESC LIMIT 1), 'success'
    UNION ALL
    SELECT 5, 'Zeilen fact_verkauf = silver.verkauf',
           (SELECT COUNT(*) FROM gold.fact_verkauf)::text,
           (SELECT COUNT(*) FROM silver.verkauf)::text
    UNION ALL
    SELECT 6, 'Konzernkunden in dim_kunde (inkl. -1)',
           (SELECT COUNT(*) FROM gold.dim_kunde)::text, '284'
    UNION ALL
    SELECT 7, 'Zeilen mit unbekanntem Kunden',
           (SELECT COUNT(*) FROM gold.fact_verkauf WHERE kunde_sk = -1)::text, '90'
    UNION ALL
    SELECT 8, 'DQ12 Umsatz Silver = Gold',
           (SELECT status FROM meta.v_dq_aktuell WHERE rule_id = 'DQ12'), 'OK'
    UNION ALL
    SELECT 9, 'Duplikate Firma B entfernt',
           (SELECT fehler_anzahl FROM meta.v_dq_aktuell WHERE rule_id = 'DQ08')::text, '29'
) checks
ORDER BY nr;