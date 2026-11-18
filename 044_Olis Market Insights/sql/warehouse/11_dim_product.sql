-- dim_product
-- Grain: one row per product_id.

CREATE OR REPLACE TABLE dim_product AS
SELECT
    product_id,
    product_category_name_english AS category,
    product_photos_qty            AS photos,
    product_weight_g              AS weight_g
FROM stg_products;
