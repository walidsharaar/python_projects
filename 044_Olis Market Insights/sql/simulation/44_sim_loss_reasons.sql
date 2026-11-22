-- SIMULATED DATA. sim_loss_reasons
-- Grain: one row per industry x loss reason (lost deals only).
-- share = share of the industry's lost deals. 'not_recorded' = the sales
-- rep left the field empty; shown on purpose, not hidden.

CREATE OR REPLACE TABLE sim_loss_reasons AS
WITH lost AS (
    SELECT COALESCE(industry, 'unknown')         AS industry,
           COALESCE(loss_reason, 'not_recorded') AS loss_reason,
           COUNT(*)                              AS lost_deals
    FROM sim_stg_crm_opportunities
    WHERE status = 'lost'
    GROUP BY ALL
)
SELECT industry, loss_reason, lost_deals,
       lost_deals / SUM(lost_deals) OVER (PARTITION BY industry) AS share
FROM lost
ORDER BY industry, lost_deals DESC;
