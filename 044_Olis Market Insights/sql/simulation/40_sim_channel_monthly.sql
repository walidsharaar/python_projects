-- SIMULATED DATA (EventPro, see docs/simulation.md). Never mixed with Olist.
-- sim_channel_monthly
-- Grain: one row per month x channel.
-- GA4-style funnel: session -> quote request -> booking, plus spend.

-- 95 % Wilson interval for a rate; used by the win/loss marts below.
CREATE OR REPLACE MACRO wilson_low(k, n) AS
    CASE WHEN n = 0 THEN NULL ELSE
    ((k / n) + 1.96^2 / (2 * n) - 1.96 * sqrt((k / n) * (1 - k / n) / n + 1.96^2 / (4 * n^2)))
    / (1 + 1.96^2 / n) END;
CREATE OR REPLACE MACRO wilson_high(k, n) AS
    CASE WHEN n = 0 THEN NULL ELSE
    ((k / n) + 1.96^2 / (2 * n) + 1.96 * sqrt((k / n) * (1 - k / n) / n + 1.96^2 / (4 * n^2)))
    / (1 + 1.96^2 / n) END;

CREATE OR REPLACE TABLE sim_channel_monthly AS
SELECT
    CAST(date_trunc('month', date) AS DATE)         AS month,
    channel,
    SUM(sessions)                                   AS sessions,
    SUM(quote_requests)                             AS quote_requests,
    SUM(bookings)                                   AS bookings,
    SUM(booking_value_eur)                          AS booking_value_eur,   -- GMV, not revenue
    SUM(spend_eur)                                  AS spend_eur,
    SUM(quote_requests) / NULLIF(SUM(sessions), 0)  AS quote_rate,
    SUM(bookings) / NULLIF(SUM(quote_requests), 0)  AS booking_rate,
    -- Cost per booking only where we pay for the traffic
    CASE WHEN SUM(spend_eur) > 0 THEN SUM(spend_eur) / NULLIF(SUM(bookings), 0) END AS cost_per_booking_eur
FROM sim_stg_web_traffic_daily
GROUP BY ALL
ORDER BY month, channel;
