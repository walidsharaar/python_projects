-- Date dimension: one row per day, full years.
-- German names for DE/EN pages, Solar Hijri (Jalali) calendar fields for the Farsi pages
-- (month names for Iran and for Afghanistan/Dari).

-- Gregorian date -> Solar Hijri date, returned as ARRAY[year, month, day]
CREATE OR REPLACE FUNCTION gold.to_jalali(d DATE) RETURNS INT[]
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    gy    INT := EXTRACT(YEAR  FROM d);
    gm    INT := EXTRACT(MONTH FROM d);
    gd    INT := EXTRACT(DAY   FROM d);
    g_d_m INT[] := ARRAY[0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
    gy2   INT;
    days  INT;
    jy    INT;
    jm    INT;
    jd    INT;
BEGIN
    gy2  := CASE WHEN gm > 2 THEN gy + 1 ELSE gy END;
    days := 355666 + 365 * gy + (gy2 + 3) / 4 - (gy2 + 99) / 100 + (gy2 + 399) / 400 + gd + g_d_m[gm];
    jy   := -1595 + 33 * (days / 12053);
    days := days % 12053;
    jy   := jy + 4 * (days / 1461);
    days := days % 1461;
    IF days > 365 THEN
        jy   := jy + (days - 1) / 365;
        days := (days - 1) % 365;
    END IF;
    IF days < 186 THEN
        jm := 1 + days / 31;
        jd := 1 + days % 31;
    ELSE
        jm := 7 + (days - 186) / 30;
        jd := 1 + (days - 186) % 30;
    END IF;
    RETURN ARRAY[jy, jm, jd];
END
$$;


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
    -- Solar Hijri (Jalali) calendar for the Farsi report pages
    x.j[1]                                       AS jalali_jahr,
    x.j[2]                                       AS jalali_monat,
    x.j[3]                                       AS jalali_tag,
    x.j[1] || '-' || LPAD(x.j[2]::text, 2, '0')  AS jalali_jahr_monat,
    (ARRAY['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
           'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'])[x.j[2]]
                                                 AS jalali_monat_name,
    (ARRAY['حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله',
           'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت'])[x.j[2]]
                                                 AS jalali_monat_name_dari,
    -- labels for the Farsi report pages, with Persian digits, e.g. 'عقرب ۱۴۰۵'
    TRANSLATE(x.j[1]::text, '0123456789', '۰۱۲۳۴۵۶۷۸۹')
                                                 AS jalali_jahr_label,
    (ARRAY['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
           'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'])[x.j[2]]
        || ' ' || TRANSLATE(x.j[1]::text, '0123456789', '۰۱۲۳۴۵۶۷۸۹')
                                                 AS jalali_monat_label,
    (ARRAY['حمل', 'ثور', 'جوزا', 'سرطان', 'اسد', 'سنبله',
           'میزان', 'عقرب', 'قوس', 'جدی', 'دلو', 'حوت'])[x.j[2]]
        || ' ' || TRANSLATE(x.j[1]::text, '0123456789', '۰۱۲۳۴۵۶۷۸۹')
                                                 AS jalali_monat_label_dari,
    x.j[1] || '/' || LPAD(x.j[2]::text, 2, '0') || '/' || LPAD(x.j[3]::text, 2, '0')
                                                 AS jalali_datum
FROM (
    SELECT d::date AS datum, gold.to_jalali(d::date) AS j
    FROM generate_series(
        (SELECT DATE_TRUNC('year', MIN(beleg_datum)) FROM silver.verkauf),                             -- 1 Jan of first year
        (SELECT DATE_TRUNC('year', MAX(beleg_datum)) + INTERVAL '1 year - 1 day' FROM silver.verkauf), -- 31 Dec of last year
        INTERVAL '1 day'
    ) AS d
) x;

ALTER TABLE gold.dim_datum ADD PRIMARY KEY (datum);
