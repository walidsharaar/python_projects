-- mart_data_quality
-- Grain: one row per data quality check.
-- Every known gap in one place, with how many records it touches and which
-- KPIs it affects. The dashboard's data quality page reads only this table.
-- "affects" is a key; the readable text is in src/i18n/translations.json.

CREATE OR REPLACE TABLE mart_data_quality AS
SELECT 'leads_before_tracking' AS check_key, 'fct_leads' AS table_name,
       COUNT(*) FILTER (WHERE NOT deal_tracking_complete) AS records, COUNT(*) AS total_records,
       'trends' AS affects
FROM fct_leads
UNION ALL
SELECT 'unattributed_leads', 'fct_leads',
       COUNT(*) FILTER (WHERE NOT is_attributed), COUNT(*), 'channels'
FROM fct_leads
UNION ALL
SELECT 'sellers_without_full_window', 'fct_seller_activation',
       COUNT(*) FILTER (WHERE NOT has_full_90d_window), COUNT(*), 'activation'
FROM fct_seller_activation
UNION ALL
SELECT 'negative_sales_cycle', 'fct_leads',
       COUNT(*) FILTER (WHERE dq_negative_sales_cycle), COUNT(*) FILTER (WHERE is_won), 'sales_cycle'
FROM fct_leads
UNION ALL
SELECT 'missing_behaviour_profile', 'fct_leads',
       COUNT(*) FILTER (WHERE is_won AND lead_behaviour_profile IS NULL), COUNT(*) FILTER (WHERE is_won),
       'behaviour'
FROM fct_leads
UNION ALL
SELECT 'missing_declared_revenue', 'stg_deals',
       COUNT(*) FILTER (WHERE declared_monthly_revenue IS NULL), COUNT(*), 'lead_scoring'
FROM stg_deals
UNION ALL
SELECT 'impossible_dates', 'fct_orders',
       COUNT(*) FILTER (WHERE dq_impossible_dates), COUNT(*), 'delivery'
FROM fct_orders
UNION ALL
SELECT 'delivered_without_date', 'fct_orders',
       COUNT(*) FILTER (WHERE dq_delivered_without_date), COUNT(*), 'delivery'
FROM fct_orders
UNION ALL
SELECT 'orders_without_items', 'fct_orders',
       COUNT(*) FILTER (WHERE n_items = 0), COUNT(*), 'order_counts'
FROM fct_orders;
