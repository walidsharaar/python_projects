import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# SQL Server Local Connection String
# Adjust Server name, Database name, and Driver to match your local MS SQL Server setup
SQL_SERVER = os.getenv("SQL_SERVER", "localhost\\SQLEXPRESS")
SQL_DATABASE = os.getenv("SQL_DATABASE", "Ohly_Bioprocess_Analytics")
SQL_DRIVER = "ODBC Driver 17 for SQL Server"

# SQLAlchemy Connection URI using Windows Authentication (Trusted_Connection)
DATABASE_URI = (
    f"mssql+pyodbc://@{SQL_SERVER}/{SQL_DATABASE}"
    f"?driver={SQL_DRIVER.replace(' ', '+')}&Trusted_Connection=yes"
)

KAGGLE_DATASET = "adityanarayankonwar/fermentation-optimization"
RAW_FILE_NAME = "Aggregated_data_with_1000_runs.xlsx"