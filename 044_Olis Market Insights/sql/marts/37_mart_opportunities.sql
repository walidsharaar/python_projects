-- mart_opportunities
-- Grain: one row per recommended action.
-- "What is at stake?": each action sized in contracts and active sellers, using
-- only observed rates (no targets are invented). Read every row as:
--   "if <group> reached <benchmark>, we would have <extra> more ... in the data period".
-- Period: the tracked lead months (contracts) / sellers with a full 90-day window.

CREATE OR REPLACE TABLE mart_opportunities AS
WITH act AS (   -- overall activation of signed sellers (the KPI)
    SELECT value AS rate FROM mart_kpi_summary WHERE kpi_key = 'seller_activation_rate_full_window'
),
search AS (     -- benchmark for channels: organic + paid search together
    SELECT SUM(won)::DOUBLE / SUM(leads) AS rate FROM mart_channel_performance
    WHERE origin IN ('organic_search', 'paid_search')
),
social AS (
    SELECT leads, lead_to_win_rate AS rate FROM mart_channel_performance WHERE origin = 'social'
),
weak_types AS ( -- seller types that activate clearly below the average
    SELECT COUNT(*) AS sellers, AVG(is_activated::INT) AS rate
    FROM fct_seller_activation
    WHERE has_full_90d_window AND lead_type IN ('offline', 'industry')
),
months AS (     -- latest tracked lead month against the earlier tracked months
    SELECT cohort_month, leads, won_60d, lead_to_win_rate_60d AS rate,
           ROW_NUMBER() OVER (ORDER BY cohort_month DESC) AS rn
    FROM mart_gtm_monthly WHERE deal_tracking_complete
),
latest AS (SELECT * FROM months WHERE rn = 1),
earlier AS (SELECT SUM(won_60d)::DOUBLE / SUM(leads) AS rate FROM months WHERE rn > 1)

SELECT 1 AS priority, 'fix_tracking' AS action_key, 'data' AS owner, 1 AS finding,
       -- precondition, not a gain: contracts we cannot credit to any channel today
       k.numerator AS base, k.value AS rate_now, NULL::DOUBLE AS rate_benchmark,
       k.numerator AS contracts_at_stake, NULL::DOUBLE AS active_sellers_at_stake
FROM mart_kpi_summary AS k WHERE k.kpi_key = 'unattributed_win_share'
UNION ALL
SELECT 2, 'social_quality', 'marketing', 3,
       s.leads, s.rate, x.rate,
       s.leads * (x.rate - s.rate), s.leads * (x.rate - s.rate) * a.rate
FROM social AS s, search AS x, act AS a
UNION ALL
SELECT 3, 'onboarding', 'product', 4,
       w.sellers, w.rate, a.rate,
       NULL, w.sellers * (a.rate - w.rate)
FROM weak_types AS w, act AS a
UNION ALL
SELECT 4, 'check_latest_month', 'data', 2,
       l.leads, l.rate, e.rate,
       l.leads * (e.rate - l.rate), l.leads * (e.rate - l.rate) * a.rate
FROM latest AS l, earlier AS e, act AS a;
