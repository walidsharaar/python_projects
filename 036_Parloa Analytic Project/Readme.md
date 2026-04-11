# Parloa Strategic Analytics: Enterprise Agentic AI Framework

- This repository demonstrates the synthesis of high-volume conversational AI data into actionable strategic initiatives, specifically for the Data Analyst (Strategy & Analytics) role at Parloa.

## Project Overview
- A simulation of the end-to-end analytical lifecycle for agentic AI, comprising:
- Synthetic Data: Interaction logs and financial metrics reflecting enterprise conditions.
- SQL Analytics: Queries for KPI assessment and predictive feature engineering.
- Executive Dashboard: A Streamlit interface for senior stakeholder visualization.

## Strategic KPIs
- Containment Efficiency: Percentage of inquiries resolved autonomously.
- Mean Handling Latency (MHL): Optimization of workflow and API efficacy.
- Sentiment Velocity: Ensuring automation quality preserves customer experience.

## Technical Methodology & Architecture
- Stack: Python (Pandas/NumPy), SQL, Streamlit, and Plotly.
- Assets: app.py (Dashboard), data_generator.py (Data), analysis_queries.sql (Analysis), and INTERVIEW_DOCS.md (Strategic Logic).

## Impact & Insights

- FP&A Integration: Cost-per-interaction modeling to identify revenue leakage against quotas.
- Intent Mapping: Correlating intent sophistication with satisfaction to prioritize development.
- Retention Modeling: Identifying behavioral indicators of enterprise churn risk.

## Implementation
```
git clone the repo
pip install streamlit pandas plotly numpy
python data_generator.py
streamlit run app.py
```
## SQL Strategic Analytics
```
-- Parloa Interview SQL Challenge Pack
-- Focus: Performance Frameworks & Advanced Modeling

-- 1. BASIC: Containment Rate & AHT by Channel
-- Purpose: Measure operational efficiency of AI agents across platforms.
SELECT
channel,
COUNT(interaction_id) AS total_conversations,
ROUND(AVG(is_contained) * 100, 2) AS containment_rate_pct,
ROUND(AVG(duration_seconds), 2) AS avg_handling_time_sec
FROM interactions
GROUP BY 1
ORDER BY 3 DESC;

-- 2. ADVANCED: Cohort Retention Analysis (FP&A Alignment)
-- Purpose: Identify if newer cohorts of AI agents are resolving issues faster.
WITH user_first_interaction AS (
SELECT
customer_id,
MIN(DATE_TRUNC('month', timestamp)) as cohort_month
FROM interactions
GROUP BY 1
)
SELECT
c.cohort_month,
DATE_TRUNC('month', i.timestamp) as activity_month,
COUNT(DISTINCT i.customer_id) as active_users
FROM user_first_interaction c
JOIN interactions i ON c.customer_id = i.customer_id
GROUP BY 1, 2;

-- 3. STRATEGIC: Prediction Prep - Identify High-Value Escalation Patterns
-- Purpose: Feature engineering for a predictive model to prevent human agent overflow.
SELECT
intent,
AVG(duration_seconds) OVER(PARTITION BY intent) as intent_avg_duration,
CASE
WHEN is_contained = 0 AND duration_seconds > 300 THEN 'High Cost Escalation'
WHEN is_contained = 0 THEN 'Standard Escalation'
ELSE 'AI Resolved'
END as resolution_category,
COUNT(*) as volume
FROM interactions
WHERE timestamp >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2, 3;

-- 4. FP&A: Revenue Leakage vs. Usage Quotas
-- Purpose: Identify clients exceeding quotas to drive expansion revenue (Strategy).
SELECT
client_name,
contract_value_mrr,
actual_usage,
interaction_quota,
(actual_usage - interaction_quota) as overage_volume,
CASE
WHEN actual_usage > interaction_quota THEN (actual_usage - interaction_quota) * 0.05
ELSE 0
END as potential_expansion_revenue
FROM client_metrics
WHERE actual_usage > (interaction_quota * 0.9);
```