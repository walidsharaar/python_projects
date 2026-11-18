-- dim_customer
-- Grain: one row per customer_id.
-- Careful: in Olist a customer_id is created for every ORDER.
-- The real person is customer_unique_id. Use it for repeat customers.

CREATE OR REPLACE TABLE dim_customer AS
SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix AS zip_prefix,
    customer_city            AS city,
    customer_state           AS state
FROM stg_customers;
