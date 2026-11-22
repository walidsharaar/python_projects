-- SIMULATED DATA. sim_winloss_industry
-- Grain: one row per industry ('unknown' = not maintained in the CRM).
-- Win rate = won / (won + lost). Open deals are not decided yet, so they are
-- counted but never in the denominator (same idea as fixed windows in Olist).

CREATE OR REPLACE TABLE sim_winloss_industry AS
SELECT
    COALESCE(industry, 'unknown')                           AS industry,
    COUNT(*)                                                AS opportunities,
    COUNT(*) FILTER (WHERE status = 'won')                  AS won,
    COUNT(*) FILTER (WHERE status = 'lost')                 AS lost,
    COUNT(*) FILTER (WHERE status = 'open')                 AS open,
    won / NULLIF(won + lost, 0)                             AS win_rate,
    wilson_low(won, won + lost)                             AS win_rate_ci_low,
    wilson_high(won, won + lost)                            AS win_rate_ci_high,
    MEDIAN(deal_value_eur) FILTER (WHERE status = 'won')    AS median_deal_value_won,
    MEDIAN(closed_date - created_date) FILTER (WHERE status <> 'open') AS median_cycle_days,
    -- Automotive: did the win rate change in H2 2025? (planned budget cuts)
    COUNT(*) FILTER (WHERE status = 'won'  AND created_date >= DATE '2025-07-01')
      / NULLIF(COUNT(*) FILTER (WHERE status <> 'open' AND created_date >= DATE '2025-07-01'), 0) AS win_rate_h2_2025,
    COUNT(*) FILTER (WHERE status = 'won'  AND created_date <  DATE '2025-07-01')
      / NULLIF(COUNT(*) FILTER (WHERE status <> 'open' AND created_date <  DATE '2025-07-01'), 0) AS win_rate_before_h2_2025,
    (won + lost) < 50                                       AS is_small_sample
FROM sim_stg_crm_opportunities
GROUP BY ALL
ORDER BY win_rate DESC;
