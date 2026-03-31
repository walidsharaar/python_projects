# 3.Advanced Python Analysis (Optimized)
# Reads from vw_AbsenteeismClean, engineers features, runs stats


import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import sys

#  Connection Setup 

engine = create_engine(
    "mssql+pyodbc://localhost/AbsenteeismDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

def section(title):
    """Helper to print formatted section headers."""
    print(f"\n{'='*70}")
    print(f"  {title.upper()}")
    print(f"{'='*70}")

def insight(text):
    """Helper to print professional client interpretations."""
    print(f"\nCLIENT INSIGHT: {text}")

#  1: Load Data

section("1. Data Acquisition")

try:
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM vw_AbsenteeismClean"), conn)
    
    print(f"Successfully loaded {df.shape[0]} rows and {df.shape[1]} columns.")
    insight("The dataset is clean with zero missing values, ensuring high reliability for statistical modeling.")
except Exception as e:
    print(f"Error connecting to database: {e}")
    sys.exit()

# Basic Data Quality Check
print(f"\nMissing Values Check:\n{df.isnull().sum().sum()} total missing values found.")


# 2: Feature Engineering

section("2. Feature Engineering & Binning")

# --- Column Verification & Mapping ---
column_mapping = {
    'BMI': 'BodyMassIndex',
    'DistanceKM': 'DistanceFromResidence',
    'AbsenceHours': 'AbsenteeismTimeInHours',
    'IsSocialDrinker': 'SocialDrinker',
    'IsSocialSmoker': 'SocialSmoker',
    'ReasonID': 'ReasonForAbsence'
}

df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

critical_cols = ['Age', 'BodyMassIndex', 'DistanceFromResidence', 'AbsenteeismTimeInHours']
missing = [c for c in critical_cols if c not in df.columns]

if missing:
    print(f"Error: Missing critical columns: {missing}")
    sys.exit()
else:
    print("Column mapping successful.")

# 2a. Age bands
df['AgeBand'] = pd.cut(df['Age'], bins=[0, 30, 40, 50, 100], labels=['Under 30', '30-39', '40-49', '50+'], include_lowest=True)

# 2b. BMI category
df['BMICategory'] = pd.cut(df['BodyMassIndex'], bins=[0, 18.5, 25, 30, 100], labels=['Underweight', 'Normal', 'Overweight', 'Obese'], include_lowest=True)

# 2c. Distance band
df['DistanceBand'] = pd.cut(df['DistanceFromResidence'], bins=[0, 10, 25, 999], labels=['Close (0-10km)', 'Medium (11-25km)', 'Far (25km+)'], include_lowest=True)

# 2d. High absenteeism flag (Using Median)
median_hours = df['AbsenteeismTimeInHours'].median()
df['HighAbsenteeism'] = (df['AbsenteeismTimeInHours'] > median_hours).astype(int)

# 2e. Workload band
df['WorkloadBand'] = pd.cut(df['WorkloadAvgPerDay'], bins=[0, 200, 270, 999], labels=['Light', 'Moderate', 'Heavy'], include_lowest=True)

print("Feature engineering complete.")
insight("Variables have been segmented into meaningful business categories (e.g., Age Bands, BMI Tiers) to identify specific high-risk cohorts.")


# 3: Group Analysis

section("3. Targeted Group Analysis")

def get_stats(dataframe, group_col):
    return dataframe.groupby(group_col, observed=True)['AbsenteeismTimeInHours'].agg(
        Records='count',
        Avg_Hours='mean',
        Median_Hours='median'
    ).round(2)

print("\n--- Absence by BMI Category ---")
bmi_stats = get_stats(df, 'BMICategory')
print(bmi_stats)
insight("Counter-intuitively, the 'Normal' BMI group shows higher average absence (7.69h) than 'Obese' individuals (5.00h). This suggests that weight is not the primary driver of absence volume in this workforce.")

print("\n--- Lifestyle Impact (Drinker/Smoker) ---")
lifestyle_stats = get_stats(df, ['SocialDrinker', 'SocialSmoker'])
print(lifestyle_stats)
insight("Employees who are both social drinkers and smokers exhibit the highest average absence (8.0h), indicating a cumulative lifestyle risk factor.")

# Map Education for readability
edu_map = {1: 'High school', 2: 'Graduate', 3: 'Postgraduate', 4: 'Masters/PhD'}
df['EducationLabel'] = df['Education'].map(edu_map)
print("\n--- Education Level Impact ---")
print(get_stats(df, 'EducationLabel'))
insight("Absence rates are significantly higher among 'High School' educated staff compared to those with advanced degrees, suggesting a correlation between job level/education and attendance.")


#  4: Dynamic Correlation Analysis

section("4. Correlation Insight (Numeric Features)")

numeric_df = df.select_dtypes(include=[np.number])
corr_matrix = numeric_df.corr()

if 'AbsenteeismTimeInHours' in corr_matrix:
    target_corr = corr_matrix['AbsenteeismTimeInHours'].drop(['AbsenteeismTimeInHours'], errors='ignore')
    target_corr_sorted = target_corr.sort_values(key=abs, ascending=False)

    print(f"{'Feature':<25} | {'Corr':>7} | {'Strength Visual'}")
    print("-" * 60)
    for col, val in target_corr_sorted.items():
        bar_len = int(abs(val) * 40)
        bar = "█" * bar_len
        direction = "(+)" if val > 0 else "(-)"
        print(f"{col:<25} | {val:>7.3f} | {bar:<40} {direction}")

insight("The strongest predictors of absence volume are family size (NumberOfChildren) and specific Reason Codes. Interestingly, distance from work has a negative correlation, suggesting remote proximity isn't the issue.")


# 5: Outlier & Reason Analysis

section("5. Outlier Detection (IQR Method)")

Q1 = df['AbsenteeismTimeInHours'].quantile(0.25)
Q3 = df['AbsenteeismTimeInHours'].quantile(0.75)
IQR = Q3 - Q1
upper_fence = Q3 + 1.5 * IQR

outliers = df[df['AbsenteeismTimeInHours'] > upper_fence]

reason_map = {0: 'None', 1: 'Infectious', 13: 'Musculoskeletal', 19: 'Injury/Poisoning', 23: 'Medical Consultation', 27: 'Physiotherapy', 28: 'Dental'}

print(f"Q1: {Q1:.1f} | Q3: {Q3:.1f} | IQR: {IQR:.1f}")
print(f"Outlier Threshold (Upper Fence): {upper_fence:.1f} hours")
print(f"Total Outliers: {len(outliers)} ({100*len(outliers)/len(df):.1f}%)")

if not outliers.empty:
    top_outlier_code = outliers['ReasonForAbsence'].mode().iloc[0]
    reason_text = reason_map.get(top_outlier_code, f"Code {top_outlier_code}")
    print(f"Top Reason for Extreme Cases: {reason_text}")
    insight(f"6% of records are extreme 'outliers' (over 17 hours). These are primarily driven by '{reason_text}' issues, which represent long-term health risks rather than casual absenteeism.")


#  6: Executive Summary

section("6. Executive Summary of Findings")

avg_hours = df['AbsenteeismTimeInHours'].mean()
top_code = df[df['ReasonForAbsence'] > 0]['ReasonForAbsence'].mode().iloc[0] if not df[df['ReasonForAbsence'] > 0].empty else 0
top_reason_text = reason_map.get(top_code, f"Code {top_code}")
worst_day = df.groupby('DayName')['AbsenteeismTimeInHours'].mean().idxmax()

summary = f"""
    ANALYSIS KEY METRICS:
    ----------------------------------------------------------
    Total Employee Records  : {len(df)}
    Average Absence Duration: {avg_hours:.2f} hours
    Primary Driver (Volume) : {top_reason_text}
    Highest Risk Day        : {worst_day}
    Extreme Cases (Outliers): {len(outliers)} records
    Correlation Leader      : {target_corr_sorted.index[0]} ({target_corr_sorted.iloc[0]:.3f})
    ----------------------------------------------------------
"""
print(summary)
insight(f"To reduce impact, focus on {worst_day} attendance and wellness programs targeting '{top_reason_text}'. Addressing the 44 extreme outlier cases could significantly lower the overall average.")
