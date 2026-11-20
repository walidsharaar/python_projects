-- Customer dimension: ONE row per group customer, with a golden-record name.
DROP TABLE IF EXISTS gold.dim_kunde CASCADE;

CREATE TABLE gold.dim_kunde AS
WITH kandidaten AS (
    -- all source records of a group customer, ranked by the survivorship rule
    SELECT
        m.konzern_kunde_id,
        k.kundenname,
        k.plz,
        k.ort,
        k.ist_konzern,
        k.konzern_firma_id,
        ROW_NUMBER() OVER (
            PARTITION BY m.konzern_kunde_id
            ORDER BY
                (k.kundenname = UPPER(k.kundenname)),   -- 1. normal spelling before ALL CAPS
                (k.firma_id <> 'A'),                    -- 2. SAP B1 is the leading system
                k.kunde_key                             -- 3. tie-breaker
        ) AS rang
    FROM silver.kunde_map m
    JOIN silver.kunde k ON k.kunde_key = m.kunde_key
),
firmen AS (
    -- in which group companies does this customer buy?
    SELECT
        konzern_kunde_id,
        COUNT(DISTINCT firma_id)                              AS anzahl_firmen,
        STRING_AGG(DISTINCT firma_id, ', ' ORDER BY firma_id) AS firmen
    FROM silver.kunde_map
    GROUP BY konzern_kunde_id
)
SELECT
    ROW_NUMBER() OVER (ORDER BY c.konzern_kunde_id)::int AS kunde_sk,
    c.konzern_kunde_id,
    c.kundenname,
    c.plz,
    c.ort,
    f.anzahl_firmen,
    f.firmen,
    c.ist_konzern,
    c.konzern_firma_id
FROM kandidaten c
JOIN firmen f USING (konzern_kunde_id)
WHERE c.rang = 1

UNION ALL

-- Unknown member: catches sales whose customer is missing in the master data
SELECT -1, 'UNBEKANNT', 'Unbekannter Kunde', NULL, NULL, 0, NULL, false, NULL;

ALTER TABLE gold.dim_kunde ADD PRIMARY KEY (kunde_sk);