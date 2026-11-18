-- mart_seller_activation_curve
-- Grain: one row per month won x window (30, 60, 90 days).
-- Question: of the sellers won in a month, how many sold within N days?
--
-- A seller only counts for a window if the whole window lies before the
-- effective data end. Otherwise we cannot know yet, and counting them as
-- "not activated" would make recent months look bad (right-censoring).

CREATE OR REPLACE TABLE mart_seller_activation_curve AS
WITH data_end AS (
    SELECT MAX(purchased_at) AS last_item_at FROM fct_order_items
)
SELECT
    CAST(date_trunc('month', s.won_date) AS DATE)            AS won_month,
    w.window_days,
    COUNT(*)                                                  AS won_sellers,
    COUNT(*) FILTER (WHERE s.won_date + to_days(w.window_days::INT)
                           <= (SELECT last_item_at FROM data_end))
                                                              AS observable_sellers,
    COUNT(*) FILTER (WHERE s.won_date + to_days(w.window_days::INT)
                           <= (SELECT last_item_at FROM data_end)
                       AND s.is_activated
                       AND s.days_to_first_sale <= w.window_days)
                                                              AS activated_in_window,
    activated_in_window / NULLIF(observable_sellers, 0)       AS activation_rate
FROM fct_seller_activation AS s
CROSS JOIN (VALUES (30), (60), (90)) AS w(window_days)
GROUP BY ALL
ORDER BY won_month, window_days;
