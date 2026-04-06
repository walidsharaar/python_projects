import pyodbc
from configuration import DB_SETTINGS

class DatabaseManager:
    def __init__(self):
        self.conn_str = f"DRIVER={DB_SETTINGS['driver']};SERVER={DB_SETTINGS['server']};Trusted_Connection=yes;"
        self.db_name = DB_SETTINGS['database']

    def get_connection(self, include_db=True):
        full_conn_str = self.conn_str
        if include_db:
            full_conn_str += f"DATABASE={self.db_name};"
        return pyodbc.connect(full_conn_str, autocommit=True)

    def initialize_db(self):
        """Ensures database and tables exist."""
        # Create DB if missing
        conn = self.get_connection(include_db=False)
        conn.cursor().execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.db_name}') CREATE DATABASE {self.db_name}")
        conn.close()

        # Create Vocabulary table
        conn = self.get_connection()
        conn.cursor().execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[Vocabulary]') AND type in (N'U'))
            CREATE TABLE Vocabulary (
                id INT PRIMARY KEY IDENTITY(1,1),
                german NVARCHAR(500),
                english NVARCHAR(500),
                box INT DEFAULT 1,
                next_review DATETIME DEFAULT GETDATE()
            )
        """)
        conn.close()