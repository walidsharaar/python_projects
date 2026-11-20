-- All invoice lines of all companies: typed, deduplicated, quantities in pieces.
DROP TABLE IF EXISTS silver.verkauf CASCADE;

CREATE TABLE silver.verkauf AS

-- Company A: SAP B1 invoices (header OINV + lines INV1)
SELECT
    'A'                                  AS firma_id,
    h.docnum                             AS beleg_nr,
    l.linenum::int + 1                   AS beleg_pos,       -- B1 counts lines from 0
    'RE'                                 AS belegart,        -- RE = invoice, GS = credit note
    h.docdate::date                      AS beleg_datum,
    'A-' || h.cardcode                   AS kunde_key,
    'A-' || l.itemcode                   AS artikel_key,
    l.quantity::numeric                  AS menge_einheit,
    CASE l.unitmsr
        WHEN 'Stk' THEN 'STK'
        WHEN 'Krt' THEN 'KRT'
        WHEN 'Pal' THEN 'PAL'
    END                                  AS einheit,
    l.quantity::numeric * l.numpermsr::int                                    AS menge_stueck,
    l.linetotal::numeric(14, 2)                                               AS umsatz_netto,
    ROUND(l.quantity::numeric * l.numpermsr::int * l.stockprice::numeric, 2)  AS kosten
FROM bronze.sap_b1_inv1 l
JOIN bronze.sap_b1_oinv h ON h.docentry = l.docentry
WHERE h.canceled = 'N'

UNION ALL

-- Company B: flat CSV export. Remove duplicate rows first, then number the lines.
SELECT
    'B',
    v.belegnr,
    ROW_NUMBER() OVER (PARTITION BY v.belegnr ORDER BY v.artikelnr)::int,
    v.belegart,
    TO_DATE(v.belegdatum, 'DD.MM.YYYY'),
    'B-' || v.kundennr,
    'B-' || v.artikelnr,
    v.menge::numeric,
    a.einheit,
    v.menge::numeric * a.stueck_je_einheit,
    REPLACE(v.nettobetrag, ',', '.')::numeric(14, 2),
    ROUND(v.menge::numeric * a.stueck_je_einheit * a.kosten_je_stueck, 2)
FROM (
    SELECT DISTINCT belegnr, belegart, belegdatum, kundennr, artikelnr,
                    menge, einheit, einzelpreis, nettobetrag
    FROM bronze.erp_b_verkaeufe
) v
LEFT JOIN silver.artikel a ON a.artikel_key = 'B-' || v.artikelnr;

ALTER TABLE silver.verkauf ADD PRIMARY KEY (firma_id, beleg_nr, beleg_pos);