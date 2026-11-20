-- Date dimension: one row per day, full years, German names.
DROP TABLE IF EXISTS gold.dim_datum CASCADE;

CREATE TABLE gold.dim_datum AS
SELECT
    d::date                                      AS datum,
    EXTRACT(YEAR    FROM d)::int                 AS jahr,
    EXTRACT(QUARTER FROM d)::int                 AS quartal,
    'Q' || EXTRACT(QUARTER FROM d)               AS quartal_name,
    EXTRACT(MONTH   FROM d)::int                 AS monat,
    (ARRAY['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
           'September', 'Oktober', 'November', 'Dezember'])[EXTRACT(MONTH FROM d)::int]
                                                 AS monat_name,
    TO_CHAR(d, 'YYYY-MM')                        AS jahr_monat,
    EXTRACT(WEEK    FROM d)::int                 AS kalenderwoche,      -- ISO week
    EXTRACT(ISODOW  FROM d)::int                 AS wochentag,          -- 1 = Montag
    (ARRAY['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'])
        [EXTRACT(ISODOW FROM d)::int]            AS wochentag_name,
    EXTRACT(ISODOW  FROM d) IN (6, 7)            AS ist_wochenende
FROM generate_series(
    (SELECT DATE_TRUNC('year', MIN(beleg_datum)) FROM silver.verkauf),                            -- 1 Jan of first year
    (SELECT DATE_TRUNC('year', MAX(beleg_datum)) + INTERVAL '1 year - 1 day' FROM silver.verkauf), -- 31 Dec of last year
    INTERVAL '1 day'
) AS d;

ALTER TABLE gold.dim_datum ADD PRIMARY KEY (datum);