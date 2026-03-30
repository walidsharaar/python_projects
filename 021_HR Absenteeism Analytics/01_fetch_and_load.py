import pandas as pd
import numpy as np
from ucimlrepo import fetch_ucirepo
from sqlalchemy import create_engine, event, text, types
import os

# 1. Using absolute path for consistency and setup directory if it doesn't exist
PROJECT_DIR = r"D:\Projects\Python\python_projects\021_HR Absenteeism Analytics"
DATA_DIR = os.path.join(PROJECT_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"Created directory: {DATA_DIR}")

# 2. Database connection configuration 
DB_CONFIG = {
    "driver":   "ODBC Driver 18 for SQL Server",
    "server":   "localhost",
    "database": "AbsenteeismDB",
    "use_windows_auth": True,  # Set to False if using 'sa'
    "username": "sa",
    "password": "YourStrong!Passw0rd"
}

# Build Connection Strings
if DB_CONFIG["use_windows_auth"]:
    base_url = f"mssql+pyodbc://{DB_CONFIG['server']}/master?driver={DB_CONFIG['driver']}&trusted_connection=yes&TrustServerCertificate=yes"
    target_url = f"mssql+pyodbc://{DB_CONFIG['server']}/{DB_CONFIG['database']}?driver={DB_CONFIG['driver']}&trusted_connection=yes&TrustServerCertificate=yes"
else:
    base_url = f"mssql+pyodbc://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['server']}/master?driver={DB_CONFIG['driver']}&TrustServerCertificate=yes"
    target_url = f"mssql+pyodbc://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['server']}/{DB_CONFIG['database']}?driver={DB_CONFIG['driver']}&TrustServerCertificate=yes"

# 3. Ensure Database Exists (Creates if not present)
print("Checking SQL Server connection...")
temp_engine = create_engine(base_url)
try:
    with temp_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        exists = conn.execute(text(f"SELECT database_id FROM sys.databases WHERE name = '{DB_CONFIG['database']}'")).fetchone()
        if not exists:
            print(f"Creating database {DB_CONFIG['database']}...")
            conn.execute(text(f"CREATE DATABASE {DB_CONFIG['database']}"))
finally:
    temp_engine.dispose()

# 4. Fetch Dataset from UCI Repository
print("Fetching dataset from UCI (ID: 445)...")
dataset = fetch_ucirepo(id=445) 
df = pd.concat([dataset.data.features, dataset.data.targets], axis=1)

# Clean Column Names: Spaces/Slashes/Dashes -> Underscores
df.columns = [col.replace(' ', '_').replace('/', '_').replace('-', '_') for col in df.columns]

# Performance Tip: Standardize Nulls for SQL
df = df.replace({np.nan: None}) 
print(f"Dataset ready. Shape: {df.shape}")

# 5. Load Data into SQL Server 
engine = create_engine(target_url)

@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    if executemany:
        cursor.fast_executemany = True

# Define specific SQL types for key columns (Saves space/increases query speed)
# You can add more columns here as needed
sql_dtypes = {
    'ID': types.Integer(),
    'Age': types.Integer(),
    'Absenteeism_time_in_hours': types.Integer()
}

print(f"Loading data into [{DB_CONFIG['database']}]...")
try:
    # Use engine.begin() for automatic transaction handling (Commit/Rollback)
    with engine.begin() as connection:
        df.to_sql(
            'AbsenteeismRaw', 
            connection, 
            if_exists='replace', 
            index=False,
            chunksize=500,       # Pushes rows in smaller memory chunks
            dtype=sql_dtypes     # Enforces schema types
        )
    print("Success! SQL Table 'AbsenteeismRaw' is populated.")
except Exception as e:
    print(f" SQL Error: {e}")

#6. Save a local backup of the raw dataset as CSV
csv_path = os.path.join(DATA_DIR, "absenteeism_raw.csv")
df.to_csv(csv_path, index=False)
print(f" Backup saved to: {csv_path}")