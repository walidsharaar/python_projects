import pyodbc
from sqlalchemy import create_engine, text

class SQLServerConnector:
    """
    Handles connections to Microsoft SQL Server using SQLAlchemy.
    Includes logic to ensure the target database exists.
    """
    def __init__(self, server, database, driver="ODBC Driver 18 for SQL Server"):
        self.server = server
        self.database = database
        self.driver = driver
        
        # Connection string for 'master' to check/create the target DB
        self.base_url = (
            f"mssql+pyodbc://{self.server}/master?"
            f"driver={self.driver}&trusted_connection=yes&TrustServerCertificate=yes"
        )
        
        # Final target connection string
        self.target_url = (
            f"mssql+pyodbc://{self.server}/{self.database}?"
            f"driver={self.driver}&trusted_connection=yes&TrustServerCertificate=yes"
        )
        
        self._ensure_database_exists()
        self.engine = create_engine(self.target_url)

    def _ensure_database_exists(self):
        """Checks if the database exists; creates it if not."""
        print(f"Connecting to server '{self.server}' to check for database '{self.database}'...")
        temp_engine = create_engine(self.base_url)
        try:
            with temp_engine.connect() as conn:
                # Set isolation level to AUTOCOMMIT to allow CREATE DATABASE
                conn.execution_options(isolation_level="AUTOCOMMIT")
                
                query = text("SELECT database_id FROM sys.databases WHERE name = :db_name")
                exists = conn.execute(query, {"db_name": self.database}).fetchone()
                
                if not exists:
                    print(f"Database '{self.database}' not found. Creating it now...")
                    conn.execute(text(f"CREATE DATABASE [{self.database}]"))
                    print(f"Database '{self.database}' created successfully.")
                else:
                    print(f"Database '{self.database}' verified.")
        except Exception as e:
            print(f"Error during database verification: {e}")
        finally:
            temp_engine.dispose()

    def get_engine(self):
        return self.engine

    def test_connection(self):
        try:
            with self.engine.connect() as conn:
                print(f"Successfully connected to {self.database}.")
                return True
        except Exception as e:
            print(f"Connection to {self.database} failed: {e}")
            return False