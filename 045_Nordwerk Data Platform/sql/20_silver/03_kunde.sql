-- Helper: normalise a company name, so the same shop matches across systems.
-- '&' -> 'und', lowercase, single spaces, no leading/trailing spaces, 'ß' -> 'ss'
CREATE OR REPLACE FUNCTION silver.norm_name(name TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$
    SELECT REPLACE(
               LOWER(TRIM(REGEXP_REPLACE(REPLACE(name, '&', 'und'), '\s+', ' ', 'g'))),
               'ß', 'ss')
$$;


-- Customers of all companies, cleaned
DROP TABLE IF EXISTS silver.kunde_map CASCADE;
DROP TABLE IF EXISTS silver.kunde CASCADE;

CREATE TABLE silver.kunde AS
WITH alle AS (
    SELECT 'A' AS firma_id, cardcode AS kundennr, TRIM(cardname) AS kundenname,
           TRIM(zipcode) AS plz, TRIM(city) AS ort
    FROM bronze.sap_b1_ocrd

    UNION ALL

    SELECT 'B', kundennr, TRIM(kundenname), TRIM(plz), TRIM(ort)
    FROM bronze.erp_b_kunden
)
SELECT
    a.firma_id,
    a.kundennr,
    a.firma_id || '-' || a.kundennr  AS kunde_key,
    a.kundenname,
    silver.norm_name(a.kundenname)   AS name_norm,
    a.plz,
    a.ort,
    f.firma_id IS NOT NULL           AS ist_konzern,        -- customer is one of our own companies
    f.firma_id                       AS konzern_firma_id    -- ...and which one
FROM alle a
LEFT JOIN silver.firma f
       ON silver.norm_name(f.firma_name) = silver.norm_name(a.kundenname);

ALTER TABLE silver.kunde ADD PRIMARY KEY (kunde_key);


-- MDM mapping: every source customer -> one group customer id
CREATE TABLE silver.kunde_map AS
SELECT
    k.kunde_key,
    k.firma_id,
    k.kundennr,
    'GK' || LPAD(DENSE_RANK() OVER (ORDER BY k.name_norm, k.plz)::text, 5, '0') AS konzern_kunde_id,
    'auto: name + plz' AS match_methode
FROM silver.kunde k;

ALTER TABLE silver.kunde_map ADD PRIMARY KEY (kunde_key);