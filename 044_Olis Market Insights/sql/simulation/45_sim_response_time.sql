-- SIMULATED DATA. sim_response_time
-- Grain: one row per first-response bucket.
-- Association, not proof of cause: fast answers may also go to easier deals.
-- analysis/07_simulated_eventpro.py checks it with a regression.

CREATE OR REPLACE TABLE sim_response_time AS
SELECT
    CASE WHEN first_response_hours <= 4  THEN 'under_4h'
         WHEN first_response_hours <= 24 THEN '4h_to_24h'
         ELSE 'over_24h' END                         AS response_bucket,
    CASE WHEN first_response_hours <= 4 THEN 1
         WHEN first_response_hours <= 24 THEN 2 ELSE 3 END AS sort_order,
    COUNT(*) FILTER (WHERE status <> 'open')         AS decided,
    COUNT(*) FILTER (WHERE status = 'won')           AS won,
    won / decided                                    AS win_rate,
    wilson_low(won, decided)                         AS win_rate_ci_low,
    wilson_high(won, decided)                        AS win_rate_ci_high,
    COUNT(*) / SUM(COUNT(*)) OVER ()                 AS share_of_opportunities
FROM sim_stg_crm_opportunities
GROUP BY ALL
ORDER BY sort_order;
