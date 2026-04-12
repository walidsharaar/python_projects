# libraries

import pandas as pd
import pyodbc
import nltk
import re
import urllib
from abc import ABC, abstractmethod
from sqlalchemy import create_engine, text
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timedelta

#Configuration for database connection
DB_CONFIG = {
    "SERVER": 'localhost',
    "DATABASE": 'MarketingAnalyticsDB',
    "DRIVER": 'ODBC Driver 17 for SQL Server'
}

class DatabaseConnector:
  
    def __init__(self):
        self.server = DB_CONFIG["SERVER"]
        self.database = DB_CONFIG["DATABASE"]
        self.connection_string = (
            f'DRIVER={{{DB_CONFIG["DRIVER"]}}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'Trusted_Connection=yes;'
        )

    @staticmethod
    def get_engine():
        
        connection_string = (
            f"DRIVER={{{DB_CONFIG['DRIVER']}}};"
            f"SERVER={DB_CONFIG['SERVER']};"
            f"DATABASE={DB_CONFIG['DATABASE']};"
            f"Trusted_Connection=yes;"
        )
        params = urllib.parse.quote_plus(connection_string)
        url = f"mssql+pyodbc:///?odbc_connect={params}"
        return create_engine(url, fast_executemany=True)

    def init_db(self):
        try:
            print("Connecting to master to verify database...")
            conn_master = pyodbc.connect(
                f'DRIVER={{{DB_CONFIG["DRIVER"]}}};SERVER={self.server};DATABASE=master;Trusted_Connection=yes;',
                autocommit=True
            )
            cursor = conn_master.cursor()
            cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '{self.database}') CREATE DATABASE {self.database}")
            conn_master.close()

            print(f"Connecting to {self.database} to verify source tables and columns...")
            conn = pyodbc.connect(self.connection_string, autocommit=True)
            cursor = conn.cursor()
            
            
            tables_to_create = {
                "customers": {"schema": "CustomerID INT PRIMARY KEY, CustomerName NVARCHAR(255), GeographyID INT, Email NVARCHAR(255), LastUpdated DATETIME DEFAULT GETDATE()", "pk": "CustomerID"},
                "products": {"schema": "ProductID INT PRIMARY KEY, ProductName NVARCHAR(255), Category NVARCHAR(255), Price FLOAT, LastUpdated DATETIME DEFAULT GETDATE()", "pk": "ProductID"},
                "customer_reviews": {"schema": "ReviewID INT PRIMARY KEY, CustomerID INT, ProductID INT, ReviewDate DATE, ReviewText NVARCHAR(MAX), Rating INT, LastUpdated DATETIME DEFAULT GETDATE()", "pk": "ReviewID"},
                "engagement_data": {"schema": "EngagementID INT PRIMARY KEY, ContentID INT, ContentType NVARCHAR(255), ViewsClicksCombined NVARCHAR(255), LastUpdated DATETIME DEFAULT GETDATE()", "pk": "EngagementID"},
                "customer_journey": {"schema": "JourneyID INT PRIMARY KEY, CustomerID INT, ProductID INT, VisitDate DATE, Stage NVARCHAR(255), Action NVARCHAR(255), LastUpdated DATETIME DEFAULT GETDATE()", "pk": "JourneyID"},
                "geography": {"schema": "GeographyID INT PRIMARY KEY, Country NVARCHAR(255), City NVARCHAR(255), LastUpdated DATETIME DEFAULT GETDATE()", "pk": "GeographyID"}
            }

            for table_name, info in tables_to_create.items():
                
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[{table_name}]') AND type in (N'U'))
                    CREATE TABLE {table_name} ({info['schema']})
                """)
                
                
                cursor.execute(f"""
                    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[{table_name}]') AND name = 'LastUpdated')
                    ALTER TABLE {table_name} ADD LastUpdated DATETIME DEFAULT GETDATE()
                """)

                
                pk_col = info['pk']
                trigger_name = f"trg_UpdateLastUpdated_{table_name}"
                
                cursor.execute(f"IF EXISTS (SELECT * FROM sys.objects WHERE name = '{trigger_name}' AND type = 'TR') DROP TRIGGER {trigger_name}")
                
                cursor.execute(f"""
                    EXEC('
                        CREATE TRIGGER {trigger_name}
                        ON {table_name}
                        AFTER UPDATE
                        AS
                        BEGIN
                            UPDATE {table_name}
                            SET LastUpdated = GETDATE()
                            FROM {table_name} t
                            INNER JOIN inserted i ON t.{pk_col} = i.{pk_col}
                        END
                    ')
                """)
            
            
            print("Syncing timestamps for incremental detection...")
            for table in tables_to_create.keys():
                cursor.execute(f"UPDATE {table} SET LastUpdated = GETDATE() WHERE LastUpdated IS NULL")

            conn.close()
            print(f"Database '{self.database}' and incremental triggers verified.")
        except Exception as e:
            print(f"Database Initialization Error: {e}")

    @staticmethod
    def create_schema(engine, schema_name):
        """Ensures the Medallion schemas exist."""
        with engine.connect() as conn:
            conn.execute(text(f"IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = '{schema_name}') EXEC('CREATE SCHEMA {schema_name}')"))
            conn.commit()


class DataLayer(ABC):
    def __init__(self, engine):
        self.engine = engine
        self.processed_at = datetime.now()

    def get_last_processed_timestamp(self, schema, table):
        """
        Dynamically fetches the latest ETL_Inserted_At from the target table 
        to ensure true incremental extraction.
        """
        try:
            query = f"SELECT MAX(ETL_Inserted_At) FROM {schema}.{table}"
            with self.engine.connect() as conn:
                result = conn.execute(text(query)).scalar()
                return result if result else datetime(1900, 1, 1)
        except Exception:
            # Table might not exist yet
            return datetime(1900, 1, 1)

    @abstractmethod
    def process(self):
        pass

    def write_incremental(self, df, table_name, schema, pk_col):
        """
        Writes data incrementally using MERGE (Upsert).
        Ensures strict de-duplication on pk_col to prevent SQL Server MERGE collisions.
        Returns the number of rows processed.
        """
        if df.empty:
            print(f"No new/modified data for [{schema}].[{table_name}]")
            return 0

       
        initial_count = len(df)
        df = df.sort_values(by=pk_col).drop_duplicates(subset=[pk_col], keep='last')
        final_count = len(df)
        
        if initial_count > final_count:
            print(f"Internal De-duplication: Removed {initial_count - final_count} duplicates for [{schema}].[{table_name}]")

        df = df.copy() # Avoid SettingWithCopyWarning
        df['ETL_Inserted_At'] = self.processed_at
        DatabaseConnector.create_schema(self.engine, schema)
        
        temp_table = f"temp_{table_name}"
        
        with self.engine.begin() as conn:
            # FIX: Check if target table exists and has the required columns
            conn.execute(text(f"""
                IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[{schema}].[{table_name}]') AND type in (N'U'))
                BEGIN
                    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[{schema}].[{table_name}]') AND name = 'LastUpdated')
                        ALTER TABLE [{schema}].[{table_name}] ADD LastUpdated DATETIME;
                    IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[{schema}].[{table_name}]') AND name = 'ETL_Inserted_At')
                        ALTER TABLE [{schema}].[{table_name}] ADD ETL_Inserted_At DATETIME;
                END
            """))

            # 1. Upload new records to a temporary table
            df.to_sql(temp_table, conn, if_exists='replace', index=False)
            
            # 2. SQL Merge logic (Upsert)
            cols = [c for c in df.columns if c != pk_col]
            update_stmt = ", ".join([f"target.[{c}] = source.[{c}]" for c in cols])
            insert_cols = ", ".join([f"[{c}]" for c in df.columns])
            insert_vals = ", ".join([f"source.[{c}]" for c in df.columns])

            merge_sql = f"""
                MERGE {schema}.{table_name} AS target
                USING {temp_table} AS source
                ON (target.{pk_col} = source.{pk_col})
                WHEN MATCHED THEN
                    UPDATE SET {update_stmt}
                WHEN NOT MATCHED THEN
                    INSERT ({insert_cols}) VALUES ({insert_vals});
            """
            conn.execute(text(merge_sql))
            conn.execute(text(f"DROP TABLE {temp_table}"))
            
        print(f"Incremental update complete for [{schema}].[{table_name}] ({final_count} rows)")
        return final_count

# --- BRONZE LAYER ---
class BronzeLayer(DataLayer):
    def process(self):
        print("\n --- BRONZE LAYER (Incremental Extraction) ---")
        tables = {
            'customers': 'CustomerID', 
            'products': 'ProductID', 
            'customer_reviews': 'ReviewID', 
            'engagement_data': 'EngagementID', 
            'customer_journey': 'JourneyID', 
            'geography': 'GeographyID'
        }
        bronze_data = {}
        total_rows = 0
        
        for table, pk in tables.items():
            try:
                # Dynamic watermark: Get the last time we ingested THIS specific table
                last_run = self.get_last_processed_timestamp('bronze', table)
                
                # Extract rows changed since the last successful Bronze ingestion
                query = text(f"SELECT * FROM dbo.{table} WHERE LastUpdated > :last_run")
                df = pd.read_sql(query, self.engine, params={"last_run": last_run})
                
                rows_synced = self.write_incremental(df, table, 'bronze', pk)
                total_rows += rows_synced
                
                # For downstream layers, we fetch what's currently "new" in Bronze
                # FIX: Wrap query in text() to handle parameters correctly
                bronze_data[table] = pd.read_sql(text(f"SELECT * FROM bronze.{table} WHERE ETL_Inserted_At = :now"), 
                                                self.engine, params={"now": self.processed_at})
            except Exception as e:
                print(f"Extraction failed for {table}: {e}")
            
        print(f"Bronze Layer Total: {total_rows} rows processed.")
        return bronze_data

# --- SILVER LAYER ---
class SilverLayer(DataLayer):
    def __init__(self, engine, bronze_data):
        super().__init__(engine)
        self.data = bronze_data
        nltk.download('vader_lexicon', quiet=True)
        self.sia = SentimentIntensityAnalyzer()

    def _clean_text(self, text_val):
        return re.sub(r'\s+', ' ', str(text_val)).strip()

    def process(self):
        print("\n--- SILVER LAYER (Incremental Transformation) ---")
        total_rows = 0
        silver_results = {}
        
        # Helper to check if we have new data from Bronze
        def has_new_data(key):
            return key in self.data and not self.data[key].empty

        if has_new_data('customer_reviews'):
            df = self.data['customer_reviews'].copy()
            df['ReviewText'] = df['ReviewText'].apply(self._clean_text)
            total_rows += self.write_incremental(df, 'customer_reviews', 'silver', 'ReviewID')

        if has_new_data('engagement_data'):
            df = self.data['engagement_data'].copy()
            df[['Views', 'Clicks']] = df['ViewsClicksCombined'].str.split('-', expand=True).fillna(0).astype(int)
            df['ContentType'] = df['ContentType'].str.upper().replace('SOCIALMEDIA', 'SOCIAL MEDIA')
            total_rows += self.write_incremental(df, 'engagement_data', 'silver', 'EngagementID')

        pks = {'customers': 'CustomerID', 'products': 'ProductID', 'geography': 'GeographyID', 'customer_journey': 'JourneyID'}
        for key, pk in pks.items():
            if has_new_data(key):
                total_rows += self.write_incremental(self.data[key], key, 'silver', pk)

        print(f"Silver Layer Total: {total_rows} rows processed.")
        
        # Fetch newly transformed silver data for Gold
        # FIX: Wrap query in text()
        for k in self.data.keys():
            silver_results[k] = pd.read_sql(text(f"SELECT * FROM silver.{k} WHERE ETL_Inserted_At = :now"), 
                                           self.engine, params={"now": self.processed_at})
        return silver_results

# --- GOLD LAYER ---
class GoldLayer(DataLayer):
    def __init__(self, engine, silver_data):
        super().__init__(engine)
        self.data = silver_data
        self.sia = SentimentIntensityAnalyzer()

    def process(self):
        print("\n --- GOLD LAYER (Incremental Enrichment) ---")
        total_rows = 0
        
        def has_new_data(key):
            return key in self.data and not self.data[key].empty

        if has_new_data('customers'):
            geo = pd.read_sql(text("SELECT GeographyID, Country, City FROM silver.geography"), self.engine)
            gold_cust = self.data['customers'].merge(geo, on='GeographyID', how='left')
            gold_cust = gold_cust.loc[:, ~gold_cust.columns.duplicated()]
            total_rows += self.write_incremental(gold_cust, 'dim_customers', 'gold', 'CustomerID')

        if has_new_data('customer_reviews'):
            df = self.data['customer_reviews'].copy()
            df['SentimentScore'] = df['ReviewText'].apply(lambda x: self.sia.polarity_scores(str(x))['compound'])
            df['SentimentCategory'] = df['SentimentScore'].apply(
                lambda s: 'Positive' if s > 0.05 else ('Negative' if s < -0.05 else 'Neutral')
            )
            total_rows += self.write_incremental(df, 'fact_customer_reviews', 'gold', 'ReviewID')

        fact_pks = {'engagement_data': 'EngagementID', 'customer_journey': 'JourneyID'}
        for key, pk in fact_pks.items():
            if has_new_data(key):
                target_table = f"fact_{key.replace('_data', '')}"
                total_rows += self.write_incremental(self.data[key], target_table, 'gold', pk)

        print(f"Gold Layer Total: {total_rows} rows processed.")
        print("\n Incremental Medallion Pipeline Complete.")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    try:
        db_manager = DatabaseConnector()
        db_manager.init_db()
        
        db_engine = DatabaseConnector.get_engine()
        
        # Incremental Chain
        bronze_output = BronzeLayer(db_engine).process()
        silver_output = SilverLayer(db_engine, bronze_output).process()
        GoldLayer(db_engine, silver_output).process()
        
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")