-- fct_leads
-- Grain: one row per MQL (8,000 rows), won or not.
-- LEFT JOIN keeps the leads without a deal. An INNER JOIN would keep
-- only the 842 won leads, and every conversion rate would be 100 %.

CREATE OR REPLACE TABLE fct_leads AS
SELECT
    l.mql_id,
    CAST(l.first_contact_date AS DATE)                  AS first_contact_date,
    CAST(date_trunc('month', l.first_contact_date) AS DATE) AS cohort_month,
    -- Deals were only recorded from the first won_date on (5 Dec 2017).
    -- A lead month is fair only if it starts after that, so its whole
    -- 60-day window was tracked. One definition for every mart and analysis.
    date_trunc('month', l.first_contact_date)
        >= (SELECT MIN(won_date) FROM stg_deals)        AS deal_tracking_complete,
    l.origin,
    l.is_attributed,
    l.landing_page_id,

    -- outcome
    d.mql_id IS NOT NULL                                AS is_won,
    d.won_date,
    d.sales_cycle_days,
    COALESCE(d.sales_cycle_days BETWEEN 0 AND 60, FALSE) AS is_won_within_60d,
    COALESCE(d.dq_negative_sales_cycle, FALSE)          AS dq_negative_sales_cycle,

    -- deal attributes: only filled for won leads (see README, section 6)
    d.seller_id,
    d.sdr_id,
    d.sr_id,
    d.business_segment,
    d.lead_type,
    d.business_type,
    d.lead_behaviour_profile
FROM stg_leads AS l
LEFT JOIN stg_deals AS d
    ON d.mql_id = l.mql_id;     -- one lead : zero or one deal
