import pyodbc
import config
import sys

class DatabaseManager:
    def __init__(self):
        # Added Connection Timeout (3 seconds) to prevent the app from freezing
        self.base_conn = (
            f"DRIVER={config.DB_CONFIG['driver']};"
            f"SERVER={config.DB_CONFIG['server']};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=3;" 
        )
        self.db_name = config.DB_CONFIG['database']

    def get_connection(self, use_db=True):
        conn_str = self.base_conn
        if use_db:
            conn_str += f"DATABASE={self.db_name};"
        return pyodbc.connect(conn_str, autocommit=True)

    def setup_database(self):
        """Attempts to set up the DB. Returns True if successful, False otherwise."""
        try:
            # 1. Connect to 'master' to create the database
            # If this fails, it means the Server name or Driver in config.py is wrong
            conn = self.get_connection(use_db=False)
            cursor = conn.cursor()
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.db_name}') CREATE DATABASE {self.db_name}")
            conn.close()

            # 2. Connect to the specific DB to create the table
            conn = self.get_connection(use_db=True)
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Vocab]') AND type in (N'U'))
                CREATE TABLE Vocab (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    german NVARCHAR(500),
                    english NVARCHAR(500),
                    box INT DEFAULT 1,
                    next_review DATETIME DEFAULT GETDATE()
                )
            """)
            conn.close()
            return True
        except Exception as e:
            # This will print the error to your terminal so you can see WHY it failed
            print(f"\n--- DATABASE CONNECTION ERROR ---")
            print(f"Error Details: {e}")
            print(f"Check your server name in config.py. Current: {config.DB_CONFIG['server']}")
            print(f"----------------------------------\n")
            return False