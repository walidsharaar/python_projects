-- mart_channel_performance
-- Grain: one row per acquisition channel (origin).
-- Answers two different questions per channel:
--   1. Do its leads CLOSE?          (lead-to-win, all leads)
--   2. Do its sellers SELL?         (activation and GMV, full-window sellers only)
-- A channel can be good at 1 and bad at 2. That is the point of this mart.
--
-- Wilson interval (95 %): the range where the true conversion rate probably
-- lies. Better than the simple "p +- 1.96 * SE" for small groups or rates
-- close to 0, where the simple formula can even go below 0 %.

CREATE OR REPLACE TABLE mart_channel_performance AS
WITH leads AS (
    SELECT
        origin,
        MIN(is_attributed::INT) = 1     AS is_attributed,
        COUNT(*)                        AS leads,
        SUM(is_won::INT)                AS won
    FROM fct_leads
    GROUP BY origin
),
sellers AS (
    SELECT
        origin,
        COUNT(*)                        AS won_sellers_full_window,
        AVG(is_activated::INT)          AS activation_rate,
        AVG(gmv_90d)                    AS gmv_90d_per_won_seller
    FROM fct_seller_activation
    WHERE has_full_90d_window
    GROUP BY origin
),
rates AS (
    SELECT l.*, l.won / l.leads AS p, 1.96 AS z
    FROM leads AS l
)
SELECT
    r.origin,
    r.is_attributed,
    r.leads,
    r.won,
    r.p                                                    AS lead_to_win_rate,
    -- Wilson score interval
    (r.p + r.z^2 / (2 * r.leads)
       - r.z * SQRT(r.p * (1 - r.p) / r.leads + r.z^2 / (4 * r.leads^2)))
       / (1 + r.z^2 / r.leads)                             AS lead_to_win_ci_low,
    (r.p + r.z^2 / (2 * r.leads)
       + r.z * SQRT(r.p * (1 - r.p) / r.leads + r.z^2 / (4 * r.leads^2)))
       / (1 + r.z^2 / r.leads)                             AS lead_to_win_ci_high,
    r.leads < 100                                          AS is_small_sample,
    COALESCE(s.won_sellers_full_window, 0)                 AS won_sellers_full_window,
    s.activation_rate,
    s.gmv_90d_per_won_seller
FROM rates AS r
LEFT JOIN sellers AS s
    ON s.origin = r.origin              -- one channel : zero or one row
ORDER BY r.leads DESC;
