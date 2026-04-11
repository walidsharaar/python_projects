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
