-- mart_channel_monthly
-- Grain: one row per tracked lead month x channel group.
-- For the "lead mix" chart: big channels by name, untracked together, the rest as "other".

CREATE OR REPLACE TABLE mart_channel_monthly AS
SELECT
    cohort_month,
    CASE WHEN origin IN ('organic_search', 'paid_search', 'social', 'direct_traffic') THEN origin
         WHEN NOT is_attributed THEN 'unknown'
         ELSE 'other' END                       AS channel_group,
    COUNT(*)                                    AS leads,
    SUM(is_won_within_60d::INT)                 AS won_60d
FROM fct_leads
WHERE deal_tracking_complete
GROUP BY ALL
ORDER BY cohort_month, channel_group;
