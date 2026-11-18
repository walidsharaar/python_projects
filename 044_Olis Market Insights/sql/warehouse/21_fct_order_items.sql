-- fct_order_items
-- Grain: one row per item in an order (order_id + order_item_id).
-- This is the ONLY table GMV is summed from.
-- Both joins go "up" (many items -> one order -> one customer),
-- so the number of rows cannot grow.

CREATE OR REPLACE TABLE fct_order_items AS
SELECT
    i.order_id,
    i.order_item_id,
    i.seller_id,
    i.product_id,
    c.customer_unique_id,
    o.order_purchase_timestamp            AS purchased_at,
    CAST(o.order_purchase_timestamp AS DATE) AS purchase_date,
    o.order_status,
    o.is_canceled,
    o.is_unavailable,
    i.price,
    i.freight_value
FROM stg_order_items AS i
JOIN stg_orders AS o
    ON o.order_id = i.order_id          -- many items : one order
JOIN dim_customer AS c
    ON c.customer_id = o.customer_id;   -- one order : one customer
