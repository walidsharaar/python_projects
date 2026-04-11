# Enterprise Users Engagement & Retention Project

## 1. Executive Summary

ABC is an end-to-end B2B SaaS analytics solution designed to centralize data management for enterprise product creators. This repository demonstrates a robust Data Engineering and BI pipeline that transforms raw transactional data into actionable insights focused on user engagement, retention, and conversion optimization.
The project addresses the critical business question: "How does user engagement impact retention and conversions over time?"

## Key Features

- Data Gathering Layer: Simulated integration of enterprise customer data following a BigQuery-optimized schema.
- Data Transformation Layer: SQL-based logic for cohort analysis, churn risk scoring, and engagement segmentation.
- Data Visualization Layer: A high-fidelity Streamlit dashboard providing descriptive, diagnostic, and predictive analytics.
- Predictive Analytics: Integrated ML-based Churn Risk scoring to identify at-risk users before they drop off.

## 3. Data Schema & Source

- The platform is built to interface with Google BigQuery.
- Table Path: big-query-348313.Churn.Churn
- Fields include:
```
CustomerId, Surname, CreditScore, Geography, Gender, Age, Tenure, Balance, NumOfProducts, HasCrCard, IsActiveMember, EstimatedSalary, Exited.
```

## 4. Technical Architecture

- Extraction: Fetching high-volume enterprise data (1000+ records) from BigQuery.
- Processing: Standardizing columns and calculating derived metrics (e.g., Trial-to-Paid conversion funnels).
- Visualization: - Strategic Overview: KPI tracking for C-level stakeholders.
- Engagement Analytics: Feature adoption tracking (Free vs. Paid tiers).
- Predictive Churn: Predictive modeling for Customer Success teams.
- Client Portal: Self-service analytics for enterprise end-users.


## 5. SQL Analytics Preview

- The project includes a library of advanced SQL queries designed for BigQuery, including:
- Churn Correlation: Analyzing IsActiveMember impact on retention.
- Salary Bracketing: Identifying high-value cohorts at risk of churn.