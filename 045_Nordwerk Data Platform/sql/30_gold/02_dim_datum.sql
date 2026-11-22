-- Date dimension: one row per day, full calendar years around the data.
-- Coverage flags let the report compare only complete periods (no misleading partial months or years).

DROP FUNCTION IF EXISTS gold.to_jalali(DATE);          -- left over from v1 (Persian calendar), no longer used
DROP TABLE IF EXISTS gold.dim_datum CASCADE;

CREATE TABLE gold.dim_datum AS
SELECT
    x.datum,
    EXTRACT(YEAR    FROM x.datum)::int           AS jahr,
    EXTRACT(QUARTER FROM x.datum)::int           AS quartal,
    'Q' || EXTRACT(QUARTER FROM x.datum)         AS quartal_name,
    EXTRACT(MONTH   FROM x.datum)::int           AS monat,
    (ARRAY['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',
           'September', 'Oktober', 'November', 'Dezember'])[EXTRACT(MONTH FROM x.datum)::int]
                                                 AS monat_name,
    TO_CHAR(x.datum, 'YYYY-MM')                  AS jahr_monat,
    EXTRACT(WEEK    FROM x.datum)::int           AS kalenderwoche,      -- ISO week
    EXTRACT(ISODOW  FROM x.datum)::int           AS wochentag,          -- 1 = Montag
    (ARRAY['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'])
        [EXTRACT(ISODOW FROM x.datum)::int]      AS wochentag_name,
    EXTRACT(ISODOW  FROM x.datum) IN (6, 7)      AS ist_wochenende,
    -- data coverage
    (x.datum BETWEEN b.beginn AND b.stand)::int  AS ist_im_datenbereich,
    (DATE_TRUNC('month', x.datum)::date >= b.beginn
     AND (DATE_TRUNC('month', x.datum) + INTERVAL '1 month - 1 day')::date <= b.stand)::int
                                                 AS ist_vollstaendiger_monat,
    b.beginn                                     AS datenbeginn,
    b.stand                                      AS datenstand
FROM (
    SELECT d::date AS datum
    FROM generate_series(
        (SELECT DATE_TRUNC('year', MIN(beleg_datum)) FROM silver.verkauf),                             -- 1 Jan of first year
        (SELECT DATE_TRUNC('year', MAX(beleg_datum)) + INTERVAL '1 year - 1 day' FROM silver.verkauf), -- 31 Dec of last year
        INTERVAL '1 day'
    ) AS d
) x
CROSS JOIN (SELECT MIN(beleg_datum) AS beginn, MAX(beleg_datum) AS stand FROM silver.verkauf) b;

ALTER TABLE gold.dim_datum ADD PRIMARY KEY (datum);
