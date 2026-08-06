# End-to-End Bioprocess Fermentation Medallion ETL & Yield Analytics

An enterprise-grade Data Engineering and Business Intelligence pipeline built with Python, Microsoft SQL Server, and the Medallion Architecture pattern. This platform ingests bioprocess parameters from 5-liter bioreactor fermentation runs, processes them across three data validation tiers (Bronze, Silver and Gold), persists them into a local MS SQL Server instance, and outputs executive yield optimization dashboards.

## Project Overview & Purpose

In industrial biomanufacturing (such as yeast extracts, enzymes, and fermentation-derived health products), batch yield optimization is critical. Minor variations in operating parameters—such as a 1.5°C temperature drift, pH imbalance, or aeration drops—can suppress enzyme activity (FPU/mL), decrease batch efficiency and increase scrap costs.

This project automates the extraction, cleaning, enrichment, and visual breakdown of 1,000 fermentation runs. It bridges raw plant sensor logs and high-level decision-making for plant management, quality assurance and process engineering teams.

