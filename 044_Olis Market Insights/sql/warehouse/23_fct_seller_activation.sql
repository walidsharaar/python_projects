-- fct_seller_activation
-- Grain: one row per won seller (842 rows).
-- Connects the Sales funnel (deal) with the Marketplace (orders).
--
-- Activation rule used here (README, KPI table): at least one order
-- that is not canceled. Whether 'unavailable' orders should also be
-- excluded is still open and is decided in the KPI phase.

CREATE OR REPLACE TABLE fct_seller_activation AS
WITH data_end AS (
    SELECT MAX(purchased_at) AS last_order_at FROM fct_order_items
),
first_sale AS (
    SELECT seller_id, MIN(purchased_at) AS first_sale_at
    FROM fct_order_items
    WHERE NOT is_canceled
    GROUP BY seller_id
),
gmv_90d AS (
    -- sales in the first 90 days after the deal was won
    SELECT
        d.seller_id,
        SUM(i.price)               AS gmv_90d,
        COUNT(DISTINCT i.order_id) AS orders_90d
    FROM stg_deals AS d
    JOIN fct_order_items AS i
        ON i.seller_id = d.seller_id
    WHERE NOT i.is_canceled
      AND i.purchased_at >= d.won_date
      AND i.purchased_at <  d.won_date + INTERVAL 90 DAY
    GROUP BY d.seller_id
)
SELECT
    d.seller_id,
    d.mql_id,
    d.won_date,
    l.origin,
    d.lead_type,
    d.business_segment,
    d.business_type,
    d.sdr_id,
    d.sr_id,
    f.first_sale_at,
    f.first_sale_at IS NOT NULL                       AS is_activated,
    date_diff('day', d.won_date, f.first_sale_at)     AS days_to_first_sale,
    COALESCE(g.gmv_90d, 0)                            AS gmv_90d,
    COALESCE(g.orders_90d, 0)                         AS orders_90d,
    -- Order data ends in Oct 2018. Sellers won later had less than
    -- 90 days to sell, so they must not be compared with the others.
    d.won_date + INTERVAL 90 DAY <= (SELECT last_order_at FROM data_end)
                                                      AS has_full_90d_window
FROM stg_deals AS d
LEFT JOIN first_sale AS f ON f.seller_id = d.seller_id   -- one : zero or one
LEFT JOIN gmv_90d    AS g ON g.seller_id = d.seller_id   -- one : zero or one
LEFT JOIN stg_leads  AS l ON l.mql_id    = d.mql_id;     -- one : one
