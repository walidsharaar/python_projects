-- SIMULATED DATA. sim_channel_summary
-- Grain: one row per channel. 2025 vs. 2024 (two complete years, so the
-- year-over-year comparison is fair: same months, same seasonality).

CREATE OR REPLACE TABLE sim_channel_summary AS
WITH y AS (
    SELECT channel, year(month) AS yr,
           SUM(sessions) AS sessions, SUM(quote_requests) AS quotes,
           SUM(bookings) AS bookings, SUM(booking_value_eur) AS gmv, SUM(spend_eur) AS spend
    FROM sim_channel_monthly
    GROUP BY ALL
)
SELECT
    c.channel,
    c.sessions                                          AS sessions_2025,
    p.sessions                                          AS sessions_2024,
    c.sessions / p.sessions - 1                         AS sessions_yoy,
    c.sessions / SUM(c.sessions) OVER ()                AS session_share_2025,
    c.bookings                                          AS bookings_2025,
    c.bookings / SUM(c.bookings) OVER ()                AS booking_share_2025,
    c.quotes / c.sessions                               AS quote_rate_2025,
    c.bookings / c.sessions                             AS booking_per_session_2025,
    c.gmv                                               AS gmv_2025,
    CASE WHEN c.spend > 0 THEN c.spend END              AS spend_2025,
    CASE WHEN c.spend > 0 THEN c.spend / c.bookings END AS cost_per_booking_2025
FROM y AS c
JOIN y AS p ON p.channel = c.channel AND p.yr = 2024      -- one row per channel and year
WHERE c.yr = 2025
ORDER BY sessions_2025 DESC;
