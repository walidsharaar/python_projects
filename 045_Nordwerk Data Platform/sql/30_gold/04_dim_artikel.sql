-- Item dimension: one row per item, with its CURRENT recycled-material share.
DROP TABLE IF EXISTS gold.dim_artikel CASCADE;

CREATE TABLE gold.dim_artikel AS
SELECT
    ROW_NUMBER() OVER (ORDER BY a.artikel_key)::int AS artikel_sk,
    a.artikel_key,
    a.firma_id,
    a.artikelnr,
    a.bezeichnung,
    a.artikelgruppe,
    a.ean,
    a.einheit,
    a.stueck_je_einheit,
    a.kosten_je_stueck,
    r.rezyklat_pct                                   AS rezyklat_pct_aktuell
FROM silver.artikel a
LEFT JOIN silver.rezyklat r
       ON r.artikel_key = a.artikel_key
      AND r.ist_aktuell                              -- only the currently valid row

UNION ALL

-- Unknown member
SELECT -1, 'UNBEKANNT', NULL, NULL, 'Unbekannter Artikel', NULL, NULL, NULL, NULL, NULL, NULL;

ALTER TABLE gold.dim_artikel ADD PRIMARY KEY (artikel_sk);
