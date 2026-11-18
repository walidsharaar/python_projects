-- mart_executive_funnel
-- Grain: one row per funnel stage.
-- The headline of the executive story: what happens to 1,000 leads?
--
-- Built only from KPIs in mart_kpi_summary, so it can never disagree with them:
--   won       = 1,000 x lead_to_win_rate_60d_tracked     (tracked lead months)
--   activated = won   x seller_activation_rate_full_window (sellers with a full 90-day window)
-- The two rates come from two fair populations, so "per 1,000 leads" is an
-- estimate of the chain, not a count of one group of people. The dashboard says so.

CREATE OR REPLACE TABLE mart_executive_funnel AS
WITH k AS (
    SELECT
        MAX(value) FILTER (WHERE kpi_key = 'lead_to_win_rate_60d_tracked')       AS win_rate,
        MAX(value) FILTER (WHERE kpi_key = 'seller_activation_rate_full_window') AS activation_rate,
        MAX(value) FILTER (WHERE kpi_key = 'gmv_90d_per_won_seller')             AS gmv_per_won_seller
    FROM mart_kpi_summary
)
SELECT 1 AS stage_order, 'leads' AS stage_key, 1000.0 AS per_1000_leads,
       NULL::DOUBLE AS rate_from_previous
FROM k
UNION ALL
SELECT 2, 'won', 1000 * win_rate, win_rate FROM k
UNION ALL
SELECT 3, 'activated', 1000 * win_rate * activation_rate, activation_rate FROM k
UNION ALL
-- Value in BRL, not a count: shown as a number next to the funnel, never on the same axis
SELECT 4, 'gmv_90d_brl', 1000 * win_rate * gmv_per_won_seller, NULL FROM k
ORDER BY stage_order;
