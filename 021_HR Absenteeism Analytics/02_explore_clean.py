import pandas as pd
from sqlalchemy import create_engine, text
import numpy as np

# 1. Database Connection 
connection_url = (
    "mssql+pyodbc://localhost/AbsenteeismDB?"
    "driver=ODBC+Driver+18+for+SQL+Server&"
    "trusted_connection=yes&"
    "TrustServerCertificate=yes"
)
engine = create_engine(connection_url)

def run_query(sql, label=""):
    """Helper to run a SQL query and print a formatted table."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        if label:
            print(f"\n{'='*60}")
            print(f"   {label}")
            print(f"{'='*60}")
            print(df.to_string(index=False))
        return df
    except Exception as e:
        print(f"Error running query [{label}]: {e}")
        return pd.DataFrame()

def run_statement(sql):
    """Helper to execute DDL/DML statements (Create, Update, etc.)."""
    try:
        with engine.begin() as conn:
            conn.execute(text(sql))
    except Exception as e:
        print(f"SQL Execution Error: {e}")

print("\n Advanced Cleaning \n")

#  1. Exploration
run_query("SELECT COUNT(*) AS TotalRows FROM AbsenteeismRaw", "1a. Total Raw Count")

# 2.Create view with transformations, mappings, and categorizations for better analysis and dashboarding
print(f"\n{'='*60}")
print("   Creating/Updating vw_AbsenteeismClean...")
print(f"{'='*60}")

view_sql = """
CREATE OR ALTER VIEW vw_AbsenteeismClean AS
SELECT
    -- Reason Mapping
    Reason_for_absence AS ReasonID,
    CASE 
        WHEN Reason_for_absence = 0 THEN 'No Reason'
        WHEN Reason_for_absence BETWEEN 1 AND 21 THEN 'Medical (ICD)'
        WHEN Reason_for_absence IN (22, 23, 25, 28) THEN 'Routine/Consultation'
        WHEN Reason_for_absence = 27 THEN 'Physiotherapy'
        WHEN Reason_for_absence = 26 THEN 'Unjustified'
        ELSE 'Other'
    END AS ReasonCategory,

    -- Time & Seasonality
    Month_of_absence AS Month,
    CASE 
        WHEN Month_of_absence IN (12, 1, 2) THEN 'Winter Peaks'
        WHEN Month_of_absence IN (3, 4, 5)  THEN 'Spring Transition'
        WHEN Month_of_absence IN (6, 7, 8)  THEN 'Summer Holidays'
        ELSE 'Autumn Steady'
    END AS SeasonalityGroup,
    Day_of_the_week AS DayNumber,
    CASE Day_of_the_week
        WHEN 2 THEN 'Monday'   WHEN 3 THEN 'Tuesday' WHEN 4 THEN 'Wednesday'
        WHEN 5 THEN 'Thursday' WHEN 6 THEN 'Friday'  WHEN 7 THEN 'Saturday' 
        WHEN 1 THEN 'Sunday'
    END AS DayName,
    CASE Seasons
        WHEN 1 THEN 'Summer' WHEN 2 THEN 'Autumn'
        WHEN 3 THEN 'Winter' WHEN 4 THEN 'Spring'
    END AS SeasonName,

    -- Demographics & Groups
    Age,
    CASE 
        WHEN Age < 30 THEN 'Junior (<30)'
        WHEN Age BETWEEN 30 AND 45 THEN 'Mid-Level (30-45)'
        ELSE 'Senior (>45)'
    END AS AgeGroup,
    
    -- Commute & Expense
    Transportation_expense AS TransportationExpense,
    CASE 
        WHEN Transportation_expense < 150 THEN 'Low Cost'
        WHEN Transportation_expense BETWEEN 150 AND 250 THEN 'Moderate'
        ELSE 'High Cost'
    END AS ExpenseBand,
    Distance_from_Residence_to_Work AS DistanceKM,
    CASE 
        WHEN Distance_from_Residence_to_Work < 15 THEN 'Short (<15km)'
        WHEN Distance_from_Residence_to_Work BETWEEN 15 AND 35 THEN 'Medium (15-35km)'
        ELSE 'Long (>35km)'
    END AS DistanceCategory,

    -- Workload & Performance
    Service_time AS ServiceYears,
    Work_load_Average_day_ AS WorkloadAvgPerDay,
    CASE 
        WHEN Work_load_Average_day_ < 240000 THEN 'Low Pressure'
        WHEN Work_load_Average_day_ BETWEEN 240000 AND 280000 THEN 'Steady'
        ELSE 'High Pressure'
    END AS WorkloadIntensity,
    Hit_target AS HitTarget,
    CASE 
        WHEN Hit_target >= 95 THEN 'Target Met'
        ELSE 'Below Target'
    END AS PerformanceStatus,

    -- Lifestyle & Social
    Disciplinary_failure AS IsDisciplinaryFailure,
    Education,
    Son AS NumberOfChildren,
    Social_drinker AS IsSocialDrinker,
    Social_smoker AS IsSocialSmoker,
    Pet AS NumberOfPets,
    Body_mass_index AS BMI,

    -- Targets
    Absenteeism_time_in_hours AS AbsenceHours,
    CASE 
        WHEN Absenteeism_time_in_hours = 0   THEN 'Zero'
        WHEN Absenteeism_time_in_hours <= 8  THEN 'Low (1-8h)'
        WHEN Absenteeism_time_in_hours <= 24 THEN 'Medium (9-24h)'
        ELSE 'High (24h+)'
    END AS AbsenceCategory

FROM AbsenteeismRaw
WHERE Month_of_absence > 0;
"""

run_statement(view_sql)

# 3. Reconciliation & Sample Preview
run_query("""
    SELECT 
        (SELECT COUNT(*) FROM AbsenteeismRaw WHERE Month_of_absence > 0) AS ExpectedRows,
        (SELECT COUNT(*) FROM vw_AbsenteeismClean) AS ActualViewRows,
        CASE 
            WHEN (SELECT COUNT(*) FROM AbsenteeismRaw WHERE Month_of_absence > 0) = (SELECT COUNT(*) FROM vw_AbsenteeismClean) 
            THEN ' MATCH' ELSE ' MISMATCH' 
        END AS IntegrityStatus
""", "4a. Data Integrity Reconciliation")

run_query("""
    SELECT TOP 5 
        DayName, AgeGroup, DistanceCategory, WorkloadIntensity, AbsenceHours 
    FROM vw_AbsenteeismClean
""", "4b.Sample Preview")

print("\n Success! Your view is now optimized for dashboarding.")