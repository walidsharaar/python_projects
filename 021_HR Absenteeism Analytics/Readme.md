# Absenteeism Analytics

An analytics portfolio project using **Python**, **SQL Server**, and **data visualization** — built on the UCI Absenteeism at Work dataset.

---

## Project Overview

This project analyzes employee absenteeism patterns from a Brazilian courier company (2007–2010). It covers the complete data analytics pipeline: fetching data via Python, storing and querying it in SQL Server, cleaning and analyzing it with pandas, and visualizing insights with matplotlib and seaborn.

**Dataset:** [UCI Absenteeism at Work](https://archive.ics.uci.edu/ml/datasets/Absenteeism+at+Work)  
**Records:** 740 rows, 21 columns  
**Target variable:** `AbsenteeismTimeInHours`

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.14 | Core language |
| SQL Server | Data storage and SQL analysis |
| pandas | Data cleaning and manipulation |
| numpy | Numerical operations |
| matplotlib | Charts and plots |
| seaborn | Advanced visualizations |
| pyodbc / sqlalchemy | Python ↔ SQL Server connection |
| requests | Fetching dataset via URL |
| VS Code | Development environment |


---

## Project Phases

### Phase 1 — Environment Setup ✅
- Install Python 3.14
- Configure VS Code with Python and SQL Server (mssql) extensions
- Install all required Python packages
- Create SQL Server database and table schema
- Test Python ↔ SQL Server connection with pyodbc

### Phase 2 — Fetch Data with Python
- Use the `requests` library to download the UCI dataset
- Parse the CSV and load it into the `AbsenteeismRaw` SQL Server table
- Verify row count and data integrity after load

### Phase 3 — SQL Exploration and Cleaning
- Explore raw data with T-SQL (row counts, nulls, distinct values)
- Validate data types and column ranges
- Write views for cleaned and aggregated data
- Answer business questions: top absence reasons, seasonal patterns, department trends

### Phase 4 — Python Cleaning and Analysis
- Read SQL data back into pandas via sqlalchemy
- Handle missing values and outliers
- Engineer new features (absence categories, age groups, BMI bands)
- Run correlation analysis and descriptive statistics
- Identify key drivers of high absenteeism

### Phase 5 — Visualization and Storytelling
- Bar charts: top 10 reasons for absence
- Heatmap: absenteeism by month and day of week
- Box plots: hours absent by age group and BMI
- Scatter plot: workload vs absenteeism
- Summary dashboard combining all key insights


## Requirements

```
pandas
numpy
pyodbc
sqlalchemy
requests
openpyxl
matplotlib
seaborn
```

Install all at once:
```bash
pip install pandas numpy pyodbc sqlalchemy requests openpyxl matplotlib seaborn
```

## Author

**Walid**  
Portfolio project — built as part of a structured Python + SQL data analytics learning path.

---

## License

This project is open source and available under the [MIT License](LICENSE).