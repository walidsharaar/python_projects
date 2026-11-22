-- Recycled-material share per item, with validity periods (history).
DROP TABLE IF EXISTS silver.rezyklat CASCADE;

CREATE TABLE silver.rezyklat AS
WITH roh AS (
    SELECT
        f.firma_id,
        f.firma_id || '-' || TRIM(r.artikelnr)                          AS artikel_key,
        REPLACE(REGEXP_REPLACE(r.rezyklatanteil, '[^0-9,.]', '', 'g'), ',', '.')::numeric(5, 2)
                                                                         AS rezyklat_pct,
        r.gueltig_ab::timestamp::date                                    AS gueltig_ab,
        r.gepflegt_von
    FROM bronze.excel_rezyklat r
    JOIN silver.firma f ON f.firma_name = TRIM(r.firma)
)
SELECT
    r.*,
    COALESCE(
        LEAD(r.gueltig_ab) OVER (PARTITION BY r.artikel_key ORDER BY r.gueltig_ab) - 1,
        DATE '9999-12-31'
    )                                                                    AS gueltig_bis,
    EXISTS (SELECT 1 FROM silver.artikel a WHERE a.artikel_key = r.artikel_key)
                                                                         AS artikel_bekannt
FROM roh r;

ALTER TABLE silver.rezyklat ADD COLUMN ist_aktuell BOOLEAN;
UPDATE silver.rezyklat SET ist_aktuell = (gueltig_bis = DATE '9999-12-31');
ALTER TABLE silver.rezyklat ADD PRIMARY KEY (artikel_key, gueltig_ab);
