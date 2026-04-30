# ShopEasy Marketing Analytics

## Project Overview

This project is an end-to-end Business Intelligence solution designed to solve declining engagement and conversion rates for ShopEasy, an online retail brand. It utilizes a Medallion Architecture (Bronze, Silver, Gold) to process raw data from MS SQL Server into actionable insights.

## Technical Stack

- Database: Microsoft SQL Server (Local)
- Engine: Python 3.x (SQLAlchemy, Pandas, NLTK)
- Architecture: Medallion (Bronze/Silver/Gold) with OOP
- Visualization: Streamlit & Plotly
- Sentiment Analysis: NLTK VADER

## Structure
- config/: System settings and DB connections.
- src/utils/: Shared logging and health checks.
- src/bronze/: Ingestion and schema validation.
- src/silver/: Cleaning and Sentiment Scoring.
- src/gold/: Business KPI aggregations.
- dashboard/: Multi-page Streamlit application.

## Key Insights Addressed

- Conversion Funnel: Identifying drop-off points in the customer journey.
- Engagement Quality: Analyzing which content types (Video, Blog, Social) drive ROI.
- Sentiment Analysis: Correlating customer feedback with product performance.