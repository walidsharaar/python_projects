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
    silver.norm_name(a.kundenname) || '|' || COALESCE(a.plz, '') AS match_key,   -- automatic matching rule
    a.plz,
    a.ort,
    f.firma_id IS NOT NULL           AS ist_konzern,        -- customer is one of our own companies
    f.firma_id                       AS konzern_firma_id    -- ...and which one
FROM alle a
LEFT JOIN silver.firma f
       ON silver.norm_name(f.firma_name) = silver.norm_name(a.kundenname);

ALTER TABLE silver.kunde ADD PRIMARY KEY (kunde_key);


-- New match keys get a stable group customer id; existing ones keep theirs
INSERT INTO mdm.konzern_kunde (match_key, konzern_kunde_id)
SELECT match_key, 'GK' || LPAD(nextval('mdm.konzern_kunde_nr')::text, 5, '0')
FROM (SELECT DISTINCT match_key FROM silver.kunde
      WHERE match_key NOT IN (SELECT match_key FROM mdm.konzern_kunde)
      ORDER BY match_key) neu;


-- MDM mapping: every source customer -> one group customer id.
-- A manual override (mdm.kunde_override) wins over the automatic match.
CREATE TABLE silver.kunde_map AS
SELECT
    k.kunde_key,
    k.firma_id,
    k.kundennr,
    COALESCE(ziel_id.konzern_kunde_id, auto_id.konzern_kunde_id) AS konzern_kunde_id,
    CASE WHEN o.kunde_key IS NOT NULL THEN 'manuell' ELSE 'auto: name + plz' END AS match_methode,
    o.grund                                                       AS match_grund
FROM silver.kunde k
JOIN mdm.konzern_kunde auto_id   ON auto_id.match_key = k.match_key
LEFT JOIN mdm.kunde_override o   ON o.kunde_key = k.kunde_key
LEFT JOIN silver.kunde ziel      ON ziel.kunde_key = o.ziel_kunde_key
LEFT JOIN mdm.konzern_kunde ziel_id ON ziel_id.match_key = ziel.match_key;

ALTER TABLE silver.kunde_map ADD PRIMARY KEY (kunde_key);
