-- fct_orders
-- Grain: one row per order.
-- Pattern "aggregate first, then join": we sum the items per order
-- in a CTE, so the join to orders is one-to-one and nothing is doubled.

CREATE OR REPLACE TABLE fct_orders AS
WITH items_per_order AS (
    SELECT
        order_id,
        COUNT(*)                  AS n_items,
        COUNT(DISTINCT seller_id) AS n_sellers,
        SUM(price)                AS items_value,
        SUM(freight_value)        AS freight_value
    FROM stg_order_items
    GROUP BY order_id
)
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.state                                   AS customer_state,
    o.order_status,
    o.order_purchase_timestamp                AS purchased_at,
    CAST(o.order_purchase_timestamp AS DATE)  AS purchase_date,
    o.order_delivered_customer_date           AS delivered_at,
    o.order_estimated_delivery_date           AS estimated_delivery_at,
    o.is_canceled,
    o.is_unavailable,
    o.dq_impossible_dates,
    o.dq_delivered_without_date,
    -- some orders have no items at all; they get 0, not missing
    COALESCE(i.n_items, 0)        AS n_items,
    COALESCE(i.n_sellers, 0)      AS n_sellers,
    COALESCE(i.items_value, 0)    AS items_value,
    COALESCE(i.freight_value, 0)  AS freight_value
FROM stg_orders AS o
LEFT JOIN items_per_order AS i
    ON i.order_id = o.order_id                -- one order : one summary row
JOIN dim_customer AS c
    ON c.customer_id = o.customer_id;
