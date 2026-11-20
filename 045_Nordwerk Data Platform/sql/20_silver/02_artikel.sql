-- Items of all group companies in one table, with one unit vocabulary.
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
    CASE i.salunitmsr
        WHEN 'Stk' THEN 'STK'
        WHEN 'Krt' THEN 'KRT'
        WHEN 'Pal' THEN 'PAL'
    END                               AS einheit,
    i.numinsale::int                  AS stueck_je_einheit,
    i.avgprice::numeric(12, 4)        AS kosten_je_stueck
FROM bronze.sap_b1_oitm i
LEFT JOIN bronze.sap_b1_oitb g ON g.itmsgrpcod = i.itmsgrpcod

UNION ALL

-- Company B: CSV export
SELECT
    'B',
    a.artikelnr,
    'B-' || a.artikelnr,
    a.bezeichnung,
    'Müllbeutel',                                           -- B has no item groups
    NULLIF(TRIM(a.ean), ''),
    CASE a.einheit
        WHEN 'Rolle'   THEN 'STK'
        WHEN 'Karton'  THEN 'KRT'
        WHEN 'Palette' THEN 'PAL'
    END,
    a.stueck_je_einheit::int,
    REPLACE(a.einstandspreis, ',', '.')::numeric(12, 4)     -- '1,85' -> 1.85
FROM bronze.erp_b_artikel a;

ALTER TABLE silver.artikel ADD PRIMARY KEY (artikel_key);