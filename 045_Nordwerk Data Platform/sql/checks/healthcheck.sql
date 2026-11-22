-- Health check after a pipeline run: every line should say OK.
-- The simulated data is fixed (reference date 20.11.2026), so the expected numbers never change.
-- Run in VS Code (SQLTools) or:  docker exec -i nordwerk-db psql -U nordwerk -d nordwerk_dwh < sql/checks/healthcheck.sql
WITH checks (pruefung, ist, soll) AS (
    VALUES
    ('Letzter Lauf veröffentlicht',     (SELECT CASE WHEN status LIKE 'success%' THEN 1 ELSE 0 END FROM meta.etl_run WHERE layer = 'pipeline' ORDER BY run_id DESC LIMIT 1)::numeric, 1),
    ('Quellkunden (silver.kunde_map)',  (SELECT COUNT(*) FROM silver.kunde_map), 344),
    ('Konzernkunden',                   (SELECT COUNT(DISTINCT konzern_kunde_id) FROM silver.kunde_map), 283),
    ('Kunden in beiden Firmen',         (SELECT COUNT(*) FROM gold.dim_kunde WHERE anzahl_firmen >= 2), 60),
    ('Manuelle Zuordnungen (MDM)',      (SELECT COUNT(*) FROM silver.kunde_map WHERE match_methode = 'manuell'), 1),
    ('gold.dim_kunde (inkl. -1)',       (SELECT COUNT(*) FROM gold.dim_kunde), 284),
    ('gold.dim_artikel',                (SELECT COUNT(*) FROM gold.dim_artikel), 58),
    ('gold.dim_datum',                  (SELECT COUNT(*) FROM gold.dim_datum), 1826),
    ('gold.fact_verkauf',               (SELECT COUNT(*) FROM gold.fact_verkauf), 14910),
    ('gold.fact_lieferung',             (SELECT COUNT(*) FROM gold.fact_lieferung), 10745),
    ('Positionen ohne Kunde (DQ01)',    (SELECT COUNT(*) FROM gold.fact_verkauf WHERE kunde_sk = -1), 78),
    ('Umsatz Konzern 2025 (€)',         (SELECT ROUND(SUM(umsatz_netto)) FROM gold.fact_verkauf WHERE NOT ist_intercompany AND datum BETWEEN '2025-01-01' AND '2025-12-31'), 4678909),
    ('Silver = Gold Umsatz (Diff €)',   (SELECT ABS((SELECT SUM(umsatz_netto) FROM silver.verkauf) - (SELECT SUM(umsatz_netto) FROM gold.fact_verkauf))), 0),
    ('Blockierende DQ-Regeln verletzt', (SELECT COUNT(*) FROM meta.v_dq_aktuell WHERE status = 'BLOCKIERT'), 0)
)
SELECT pruefung, ist, soll, CASE WHEN ist = soll THEN 'OK' ELSE '<<< PRÜFEN' END AS ergebnis
FROM checks;
