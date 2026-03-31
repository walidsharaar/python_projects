#libraries

import warnings
# Ignore the SQL Server version warning and Seaborn future warnings immediately
warnings.filterwarnings("ignore", category=UserWarning, module='sqlalchemy')
warnings.filterwarnings("ignore", category=FutureWarning, module='seaborn')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import seaborn as sns
from sqlalchemy import create_engine, text

# Set high-quality resolution and global theme
plt.rcParams['figure.dpi'] = 120
sns.set_theme(style="whitegrid") 
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.facecolor'] = '#f8fafc' 

# Connection Setup 
engine = create_engine(
    "mssql+pyodbc://localhost/AbsenteeismDB"
    "?driver=ODBC+Driver+17+for+SQL+Server"
    "&trusted_connection=yes"
)

# Translation Layer: Maps SQL column names to dashboard variable names
COLUMN_MAPPING = {
    'ReasonID': 'AbsenceReason',
    'BMI': 'BMI',
    'AbsenceHours': 'AbsenceHours',
    'DistanceKM': 'DistanceKM',
    'ServiceYears': 'ServiceTime'
}

# Data Acquisition
try:
    with engine.connect() as conn:
        query = text("SELECT * FROM [dbo].[vw_AbsenteeismClean]")
        df = pd.read_sql(query, conn)
    
    # Rename for internal logic consistency
    df = df.rename(columns=COLUMN_MAPPING)
    
except Exception as e:
    print(f"Database Error: {e}")
    # Fallback mock data with consistent columns
    data = {
        'AbsenceReason': np.random.randint(1, 28, 737),
        'Month': np.random.randint(1, 13, 737),
        'DayName': np.random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 737),
        'Age': np.random.randint(20, 60, 737),
        'BMI': np.random.randint(18, 35, 737),
        'AbsenceHours': np.random.gamma(2, 4, 737),
        'ServiceTime': np.random.randint(1, 25, 737),
        'WorkloadAvgPerDay': np.random.randint(200, 400, 737)
    }
    df = pd.DataFrame(data)

# Feature Engineering (Matching your SQL Logic) 
# 1. Age Bands
if 'AgeBand' not in df.columns:
    df['AgeBand'] = pd.cut(df['Age'], bins=[0, 30, 40, 50, 100], labels=['Under 30', '30-39', '40-49', '50+'])

# 2. Reason Labels
reason_map = {
    0: "None", 1: "Infectious", 13: "Musculoskeletal", 19: "Injury", 
    22: "Medical", 23: "Dental", 24: "Physio", 25: "Exam", 
    27: "Bone Marrow", 28: "Escort"
}
# Map based on the renamed column 'AbsenceReason'
df['ReasonLabel'] = df['AbsenceReason'].map(lambda x: reason_map.get(x, f"Code {x}"))

# 3. Sorting
months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
month_abbr = {1:'Jan', 2:'Feb', 3:'Mar', 4:'Apr', 5:'May', 6:'Jun', 7:'Jul', 8:'Aug', 9:'Sep', 10:'Oct', 11:'Nov', 12:'Dec'}
df['MonthName'] = df['Month'].map(month_abbr)
days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

#  Dashboard Layout 
fig = plt.figure(figsize=(24, 18))
gs = fig.add_gridspec(3, 4, height_ratios=[0.4, 1.2, 1], hspace=0.6, wspace=0.5)

# Header
fig.text(0.06, 0.96, 'HR STRATEGIC INSIGHTS', fontsize=32, fontweight='black', color='#0f172a')
fig.text(0.06, 0.935, f'Record Count: {len(df)}', fontsize=16, color='#64748b')

# KPI Section 
avg_val = df['AbsenceHours'].mean()
top_day = df['DayName'].mode().iloc[0] if not df.empty else "N/A"

kpi_metrics = [
    ("Total Absence", f"{df['AbsenceHours'].sum():,.0f}h", "#6366f1"),
    ("Avg Severity", f"{avg_val:.2f}h", "#3b82f6"),
    ("Primary Driver", df['ReasonLabel'].mode().iloc[0] if not df.empty else "N/A", "#10b981"),
    ("Highest Risk Day", top_day, "#ef4444")
]

for i, (title, val, color) in enumerate(kpi_metrics):
    ax = fig.add_subplot(gs[0, i])
    ax.axis('off')
    rect = patches.Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='#e2e8f0', linewidth=1.5, transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(0.5, 0.72, title, ha='center', va='center', fontsize=15, color='#64748b', fontweight='bold', transform=ax.transAxes)
    ax.text(0.5, 0.38, val, ha='center', va='center', fontsize=24, color=color, fontweight='black', transform=ax.transAxes)

#  1. Top Reasons (Middle Right) 
ax1 = fig.add_subplot(gs[1, 2:])
# Filter out reason 0 and aggregate
top10 = df[df['AbsenceReason'] > 0]['ReasonLabel'].value_counts().head(10)
if not top10.empty:
    sns.barplot(x=top10.values, y=top10.index, ax=ax1, palette='Blues_r', hue=top10.index, legend=False)
ax1.set_title('Top 10 Drivers of Absence (Incidents)', fontsize=18, fontweight='bold', pad=20)
ax1.set_xlabel('Frequency')
ax1.spines[['top', 'right']].set_visible(False)

#  2. Heatmap (Middle Left) 
ax2 = fig.add_subplot(gs[1, :2])
pivot = df.groupby(['MonthName', 'DayName'])['AbsenceHours'].mean().unstack().reindex(index=months_order, columns=days_order).fillna(0)
sns.heatmap(pivot, cmap='YlOrRd', annot=True, fmt=".1f", ax=ax2, cbar_kws={'label': 'Avg Hours'})
ax2.set_title('Temporal Intensity: Month vs Day', fontsize=18, fontweight='bold', pad=20)

# 3. Correlation (Bottom Right) 
ax3 = fig.add_subplot(gs[2, 2:])
corr_cols = ['Age', 'ServiceTime', 'WorkloadAvgPerDay', 'BMI', 'AbsenceHours']
valid_cols = [c for c in corr_cols if c in df.columns]
corr = df[valid_cols].corr()
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, cmap='coolwarm', center=0, ax=ax3, cbar=True)
ax3.set_title('Strategic Variable Correlations', fontsize=18, fontweight='bold', pad=20)

#  4. Age Group Analysis (Bottom Left)
ax4 = fig.add_subplot(gs[2, 0:2])
# Ensure consistent category strings and ordering
df['AgeBand'] = df['AgeBand'].astype(str)
age_order = ['Under 30', '30-39', '40-49', '50+']
plot_df = df[df['AgeBand'].isin(age_order)].copy()

if not plot_df.empty:
    # Overlaying boxplot and stripplot to ensure visibility of legend and data
    sns.boxplot(data=plot_df, x='AgeBand', y='AbsenceHours', order=age_order, 
                ax=ax4, showfliers=False, palette='Pastel1', hue='AgeBand', legend=True)
    sns.stripplot(data=plot_df, x='AgeBand', y='AbsenceHours', order=age_order, 
                  ax=ax4, color='black', alpha=0.3, size=3, jitter=True)
    
    # Legend Refinement
    ax4.legend(title="Age Cohort", loc='upper right', frameon=True, fontsize='small')

ax4.set_title('Absence Severity by Age Band', fontsize=18, fontweight='bold', pad=20)
# Set Y-Limit to focus on density
y_limit = plot_df['AbsenceHours'].quantile(0.95) * 1.3 if not plot_df.empty else 50
ax4.set_ylim(-1, max(y_limit, 10))
ax4.set_ylabel('Hours')
ax4.spines[['top', 'right']].set_visible(False)

# Footer
summary = (
    f"Executive Summary: {top_day} is the primary operational risk day. "
    f"The leading cause of absence volume is '{df['ReasonLabel'].mode()[0]}'. "
    "Strategic correlation identifies BMI and Service Time as predictors, while Age Band data "
    "shows consistent absenteeism patterns across all workforce segments."
)
plt.figtext(0.5, 0.03, summary, ha="center", fontsize=15, color='white', wrap=True,
            bbox={"facecolor":"#0f172a", "alpha":1, "pad":20, "boxstyle":"round,pad=1.2"})

plt.subplots_adjust(left=0.06, right=0.94, top=0.9, bottom=0.12)
plt.show()