import os
from dotenv import load_dotenv
import urllib
from sqlalchemy import create_engine

# Load environment variables from a .env file in the root directory
# Example .env content:
# DB_SERVER=localhost
# DB_NAME=MarketingAnalyticsDB
# DB_DRIVER=ODBC Driver 17 for SQL Server
load_dotenv()

class Config:
    """Centralized configuration management."""
    
    # Database Configuration
    DB_SERVER = os.getenv("DB_SERVER", "localhost")
    DB_NAME = os.getenv("DB_NAME", "MarketingAnalyticsDB")
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    
    @classmethod
    def get_connection_url(cls):
        """Constructs the SQLAlchemy connection URL."""
        connection_string = (
            f"DRIVER={{{cls.DB_DRIVER}}};"
            f"SERVER={cls.DB_SERVER};"
            f"DATABASE={cls.DB_NAME};"
            f"Trusted_Connection=yes;"
        )
        params = urllib.parse.quote_plus(connection_string)
        return f"mssql+pyodbc:///?odbc_connect={params}"

    @classmethod
    def initialize_directories(cls):
        """Ensures necessary local directories exist."""
        for path in [cls.DATA_DIR, cls.LOG_DIR]:
            os.makedirs(path, exist_ok=True)
        
        for layer in ["bronze", "silver", "gold"]:
            os.makedirs(os.path.join(cls.DATA_DIR, layer), exist_ok=True)