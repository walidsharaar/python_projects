-- Items of all group companies in one table, with one unit vocabulary (mdm.einheit_map).
DROP TABLE IF EXISTS silver.artikel CASCADE;

CREATE TABLE silver.artikel AS

-- Company A: SAP Business One
SELECT
    'A'                               AS firma_id,
    i.itemcode                        AS artikelnr,
    'A-' || i.itemcode                AS artikel_key,      -- unique across companies
    i.itemname                        AS bezeichnung,
    g.itmsgrpnam                      AS artikelgruppe,
    NULLIF(TRIM(i.codebars), '')      AS ean,
    e.einheit                         AS einheit,         -- from mdm.einheit_map
    i.numinsale::int                  AS stueck_je_einheit,
    i.avgprice::numeric(12, 4)        AS kosten_je_stueck
FROM bronze.sap_b1_oitm i
LEFT JOIN bronze.sap_b1_oitb g ON g.itmsgrpcod = i.itmsgrpcod
LEFT JOIN mdm.einheit_map e ON e.quellsystem = 'sap_b1' AND e.quell_einheit = i.salunitmsr

UNION ALL

-- Company B: CSV export
SELECT
    'B',
    a.artikelnr,
    'B-' || a.artikelnr,
    a.bezeichnung,
    'Müllbeutel',                                           -- B has no item groups
    NULLIF(TRIM(a.ean), ''),
    e.einheit,
    a.stueck_je_einheit::int,
    REPLACE(a.einstandspreis, ',', '.')::numeric(12, 4)     -- '1,85' -> 1.85
FROM bronze.erp_b_artikel a
LEFT JOIN mdm.einheit_map e ON e.quellsystem = 'erp_b' AND e.quell_einheit = a.einheit;

ALTER TABLE silver.artikel ADD PRIMARY KEY (artikel_key);

-- New items get a stable key; existing items keep theirs
INSERT INTO mdm.artikel_schluessel (artikel_key, artikel_sk)
SELECT artikel_key, nextval('mdm.artikel_nr')
FROM (SELECT artikel_key FROM silver.artikel
      WHERE artikel_key NOT IN (SELECT artikel_key FROM mdm.artikel_schluessel)
      ORDER BY artikel_key) neu;
