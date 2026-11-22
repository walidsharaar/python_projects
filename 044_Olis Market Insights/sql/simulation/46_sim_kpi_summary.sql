-- SIMULATED DATA. sim_kpi_summary
-- Grain: one row per KPI. Same shape as mart_kpi_summary (value, numerator,
-- denominator), so the dashboard can show both with the same KPI tile.

CREATE OR REPLACE TABLE sim_kpi_summary AS
SELECT 'sim_booking_rate_2025' AS kpi_key, 'rate' AS unit,
       SUM(bookings) / SUM(sessions) AS value, SUM(bookings) AS numerator, SUM(sessions) AS denominator
FROM sim_channel_monthly WHERE year(month) = 2025

UNION ALL
-- GEO: share of all 2025 bookings that came from AI answers (ChatGPT, Perplexity, ...)
SELECT 'sim_ai_referral_booking_share_2025', 'rate',
       SUM(bookings) FILTER (WHERE channel = 'ai_referral') / SUM(bookings),
       SUM(bookings) FILTER (WHERE channel = 'ai_referral'), SUM(bookings)
FROM sim_channel_monthly WHERE year(month) = 2025

UNION ALL
-- Paid channels only. Not CAC: no salaries, tools or agency fees in the data.
SELECT 'sim_cost_per_booking_paid_2025', 'eur',
       SUM(spend_eur) / SUM(bookings), SUM(spend_eur), SUM(bookings)
FROM sim_channel_monthly WHERE year(month) = 2025 AND spend_eur > 0

UNION ALL
SELECT 'sim_enterprise_win_rate', 'rate',
       SUM(won) / SUM(won + lost), SUM(won), SUM(won + lost)
FROM sim_winloss_industry

UNION ALL
SELECT 'sim_slow_response_share', 'rate',
       SUM(share_of_opportunities) FILTER (WHERE response_bucket = 'over_24h'),
       NULL, NULL
FROM sim_response_time

UNION ALL
SELECT 'sim_loss_reason_missing_share', 'rate',
       SUM(lost_deals) FILTER (WHERE loss_reason = 'not_recorded') / SUM(lost_deals),
       SUM(lost_deals) FILTER (WHERE loss_reason = 'not_recorded'), SUM(lost_deals)
FROM sim_loss_reasons;
