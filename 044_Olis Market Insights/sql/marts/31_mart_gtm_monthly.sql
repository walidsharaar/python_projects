-- mart_gtm_monthly
-- Grain: one row per lead cohort month (month of first contact).
-- Used for trend charts. Uses the 60-day window so months are comparable.
--
-- Warning for the reader of the chart: closed deals are only recorded
-- from 5 Dec 2017 (README, H1). Early cohorts look bad because of that,
-- not because Sales was bad. deal_tracking_complete marks the fair months.

CREATE OR REPLACE TABLE mart_gtm_monthly AS
SELECT
    cohort_month,
    COUNT(*)                                        AS leads,
    SUM(is_attributed::INT)                         AS attributed_leads,
    AVG(is_attributed::INT)                         AS attributed_share,
    SUM(is_won_within_60d::INT)                     AS won_60d,
    AVG(is_won_within_60d::INT)                     AS lead_to_win_rate_60d,
    MEDIAN(sales_cycle_days) FILTER (WHERE is_won AND NOT dq_negative_sales_cycle)
                                                    AS sales_cycle_median_days,
    -- A cohort is fair only if its whole 60-day window lies after the
    -- start of deal tracking: first day of the month >= 5 Dec 2017.
    cohort_month >= DATE '2017-12-05'               AS deal_tracking_complete
FROM fct_leads
GROUP BY cohort_month
ORDER BY cohort_month;
