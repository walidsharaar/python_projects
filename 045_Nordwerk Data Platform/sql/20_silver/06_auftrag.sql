-- Order lines of Company A with delivered quantity (from invoice lines based on them).
DROP TABLE IF EXISTS silver.auftrag CASCADE;

CREATE TABLE silver.auftrag AS
WITH geliefert AS (
    SELECT baseentry, baseline, SUM(quantity::numeric) AS menge_geliefert
    FROM bronze.sap_b1_inv1
    WHERE basetype = '17'                      -- 17 = based on a sales order
    GROUP BY baseentry, baseline
),
stichtag AS (
    SELECT MAX(docdate::date) AS datum FROM bronze.sap_b1_oinv
)
SELECT
    'A'                                                 AS firma_id,
    h.docnum                                            AS auftrag_nr,
    l.linenum::int + 1                                  AS auftrag_pos,
    h.docdate::date                                     AS auftrag_datum,
    h.docduedate::date                                  AS liefertermin,
    'A-' || h.cardcode                                  AS kunde_key,
    'A-' || l.itemcode                                  AS artikel_key,
    l.quantity::numeric * l.numpermsr::int              AS menge_bestellt_stueck,
    COALESCE(g.menge_geliefert, 0) * l.numpermsr::int   AS menge_geliefert_stueck,
    h.canceled = 'Y'                                    AS ist_storniert,
    h.docduedate::date <= s.datum                       AS ist_faellig
FROM bronze.sap_b1_rdr1 l
JOIN bronze.sap_b1_ordr h ON h.docentry = l.docentry
CROSS JOIN stichtag s
LEFT JOIN geliefert g
       ON g.baseentry = l.docentry
      AND g.baseline  = l.linenum;

ALTER TABLE silver.auftrag ADD PRIMARY KEY (firma_id, auftrag_nr, auftrag_pos);
