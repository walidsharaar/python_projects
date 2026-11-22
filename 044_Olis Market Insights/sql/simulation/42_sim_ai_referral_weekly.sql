-- SIMULATED DATA. sim_ai_referral_weekly
-- Grain: one row per week (Monday).
-- Share of AI-referral sessions in all sessions. If AI traffic suddenly drops
-- while "direct" jumps by the same amount, that is a tracking problem, not a
-- real change in demand. is_incident marks the planned incident weeks.

CREATE OR REPLACE TABLE sim_ai_referral_weekly AS
SELECT
    CAST(date_trunc('week', date) AS DATE)                               AS week,
    SUM(sessions) FILTER (WHERE channel = 'ai_referral')                 AS ai_sessions,
    SUM(sessions) FILTER (WHERE channel = 'direct')                      AS direct_sessions,
    SUM(sessions) FILTER (WHERE channel = 'ai_referral')
        / SUM(sessions)                                                  AS ai_share,
    bool_or(date BETWEEN DATE '2025-06-02' AND DATE '2025-06-22')        AS is_incident
FROM sim_stg_web_traffic_daily
GROUP BY ALL
ORDER BY week;
