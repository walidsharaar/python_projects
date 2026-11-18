-- mart_buyer_retention
-- Grain: one row per cohort month x month number.
--   cohort_month: month of a customer's first (non-canceled) purchase
--   month_number: months since then (0 = the month of the first purchase)
--
-- Only OBSERVABLE cells exist. A missing cell means "the data ends before
-- this month", which is not the same as 0 % (0 % rows are kept on purpose).
-- Data end: the last full month before the effective end of the order items
-- (3 Sep 2018 -> last full month is Aug 2018).

CREATE OR REPLACE TABLE mart_buyer_retention AS
WITH data_end AS (
    SELECT CAST(date_trunc('month', MAX(purchased_at)) AS DATE) AS first_incomplete_month
    FROM fct_order_items
),
purchases AS (
    SELECT DISTINCT
        customer_unique_id,                                  -- the real person
        CAST(date_trunc('month', purchased_at) AS DATE) AS purchase_month
    FROM fct_orders
    WHERE NOT is_canceled
      AND purchased_at < (SELECT first_incomplete_month FROM data_end)
),
first_purchase AS (
    SELECT customer_unique_id, MIN(purchase_month) AS cohort_month
    FROM purchases
    GROUP BY customer_unique_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS customers
    FROM first_purchase
    GROUP BY cohort_month
),
-- Every cell that can be observed, so that "nobody came back" appears as 0
grid AS (
    SELECT c.cohort_month, c.customers, m.month_number
    FROM cohort_size AS c
    CROSS JOIN range(0, 24) AS m(month_number)
    WHERE c.cohort_month + to_months(m.month_number::INT)
          < (SELECT first_incomplete_month FROM data_end)
),
active AS (
    SELECT
        f.cohort_month,
        date_diff('month', f.cohort_month, p.purchase_month) AS month_number,
        COUNT(DISTINCT p.customer_unique_id)                 AS active_customers
    FROM purchases AS p
    JOIN first_purchase AS f USING (customer_unique_id)      -- many months : one first purchase
    GROUP BY ALL
)
SELECT
    g.cohort_month,
    g.month_number,
    g.customers                                   AS cohort_customers,
    COALESCE(a.active_customers, 0)               AS active_customers,
    COALESCE(a.active_customers, 0) / g.customers AS retention_rate
FROM grid AS g
LEFT JOIN active AS a USING (cohort_month, month_number)
ORDER BY g.cohort_month, g.month_number;
