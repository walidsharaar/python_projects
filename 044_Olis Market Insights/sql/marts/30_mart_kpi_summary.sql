-- mart_kpi_summary
-- Grain: one row per KPI.
-- The single source of truth for headline numbers (KPI tiles, weekly report).
-- Every row keeps numerator and denominator, so nobody has to trust a
-- percentage without knowing how many cases are behind it.
-- Human-readable definitions: docs/kpi_definitions.md (same kpi_key).

CREATE OR REPLACE TABLE mart_kpi_summary AS

-- Marketing / Sales ------------------------------------------------------
SELECT 'mql_count' AS kpi_key, 'count' AS unit,
       COUNT(*)::DOUBLE AS value, COUNT(*) AS numerator, NULL::BIGINT AS denominator
FROM fct_leads

UNION ALL
-- Won ever. Easy to understand, but unfair to recent leads (less time to close).
SELECT 'lead_to_win_rate', 'rate',
       AVG(is_won::INT), SUM(is_won::INT), COUNT(*)
FROM fct_leads

UNION ALL
-- Fixed 60-day window: every lead gets the same time to close.
SELECT 'lead_to_win_rate_60d', 'rate',
       AVG(is_won_within_60d::INT), SUM(is_won_within_60d::INT), COUNT(*)
FROM fct_leads

UNION ALL
-- Median, because a few very long deals pull the mean up (48 vs 14 days).
SELECT 'sales_cycle_median_days', 'days',
       MEDIAN(sales_cycle_days), COUNT(*), NULL
FROM fct_leads
WHERE is_won AND NOT dq_negative_sales_cycle

-- Seller activation (Marketplace) ----------------------------------------
UNION ALL
SELECT 'seller_activation_rate', 'rate',
       AVG(is_activated::INT), SUM(is_activated::INT), COUNT(*)
FROM fct_seller_activation

UNION ALL
-- Same KPI, only sellers who had the full 90 days. Use this one for comparisons.
SELECT 'seller_activation_rate_full_window', 'rate',
       AVG(is_activated::INT), SUM(is_activated::INT), COUNT(*)
FROM fct_seller_activation
WHERE has_full_90d_window

UNION ALL
SELECT 'time_to_first_sale_median_days', 'days',
       MEDIAN(days_to_first_sale), COUNT(*), NULL
FROM fct_seller_activation
WHERE is_activated

UNION ALL
-- Average over ALL won sellers in the window, including those who sold nothing.
SELECT 'gmv_90d_per_won_seller', 'brl',
       AVG(gmv_90d), SUM(gmv_90d), COUNT(*)
FROM fct_seller_activation
WHERE has_full_90d_window

-- Buyers (demand side) ---------------------------------------------------
UNION ALL
-- Real person = customer_unique_id. Canceled orders do not count as a purchase,
-- so customers whose only orders were canceled are not customers here.
SELECT 'buyer_repeat_rate', 'rate',
       AVG((n_orders >= 2)::INT), SUM((n_orders >= 2)::INT), COUNT(*)
FROM (
    SELECT customer_unique_id, COUNT(*) AS n_orders
    FROM fct_orders
    WHERE NOT is_canceled
    GROUP BY customer_unique_id
);
