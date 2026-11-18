-- mart_channel_scorecard
-- Grain: one row per channel. The marketing team's one table.
-- Verdict rule (written down so anyone can check it):
--   fix_tracking  the channel is unknown / not tracked
--   too_little    fewer than 100 leads or fewer than 30 sellers: not enough data to judge
--   grow          active sellers per 1,000 leads at or above the overall funnel
--   review        below half of the overall funnel
--   watch         everything in between

CREATE OR REPLACE TABLE mart_channel_scorecard AS
WITH overall AS (
    SELECT per_1000_leads AS active_per_1000 FROM mart_executive_funnel WHERE stage_key = 'activated'
),
months AS (SELECT COUNT(*) AS n FROM mart_gtm_monthly WHERE deal_tracking_complete)
SELECT
    c.origin,
    c.leads,
    c.leads / m.n                                   AS leads_per_month,
    c.lead_to_win_rate,
    c.lead_to_win_ci_low,
    c.lead_to_win_ci_high,
    c.activation_rate,
    c.activated_per_1000_leads,
    o.active_per_1000                               AS overall_active_per_1000,
    CASE
        WHEN NOT c.is_attributed                                THEN 'fix_tracking'
        WHEN c.is_small_sample OR c.is_small_seller_sample       THEN 'too_little'
        WHEN c.activated_per_1000_leads >= o.active_per_1000     THEN 'grow'
        WHEN c.activated_per_1000_leads <  o.active_per_1000 / 2 THEN 'review'
        ELSE 'watch'
    END                                             AS verdict
FROM mart_channel_performance AS c, overall AS o, months AS m
ORDER BY c.leads DESC;
