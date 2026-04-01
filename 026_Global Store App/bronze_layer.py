import pandas as pd
import os
from sqlalchemy import text

class BronzeIngestor:
    """
    Class responsible for feeding raw data from CSV to the 
    SQL Server database as the 'Bronze' layer.
    Supports incremental loading by checking a combination of unique columns.
    """
    def __init__(self, file_path, db_engine):
        self.file_path = file_path
        self.engine = db_engine
        self.table_name = "bronze_global_store"

    def load_to_sql(self):
        """
        Reads CSV and writes ONLY new records to SQL Server.
        Uses a combination of columns to ensure uniqueness.
        """
        try:
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"File not found: {self.file_path}")

            # Robust loading (handling encoding)
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(self.file_path, encoding='ISO-8859-1')
            
            # Standardization of column names
            df.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]

            from sqlalchemy import inspect
            inspector = inspect(self.engine)
            
            if inspector.has_table(self.table_name):
                print(f"Table {self.table_name} exists. Checking for new records...")
                
                # We use a combination of row_id and order_id to create a unique fingerprint
                # This ensures we don't miss records if row_id isn't perfectly unique globally
                with self.engine.connect() as conn:
                    existing_query = text(f"SELECT row_id, order_id FROM {self.table_name}")
                    existing_df = pd.read_sql(existing_query, conn)
                
                # Create a temporary unique key for comparison
                existing_keys = set(existing_df['row_id'].astype(str) + "_" + existing_df['order_id'].astype(str))
                df_keys = df['row_id'].astype(str) + "_" + df['order_id'].astype(str)
                
                # Filter for records not in the existing keys set
                new_records_df = df[~df_keys.isin(existing_keys)]
            else:
                print(f"Table {self.table_name} does not exist. Performing full initial load.")
                new_records_df = df

            if new_records_df.empty:
                print("No new records found in the data source. Skipping Bronze update.")
                return True

            print(f"Ingesting {len(new_records_df)} new records into {self.table_name}...")
            new_records_df.to_sql(self.table_name, con=self.engine, if_exists='append', index=False)
            
            print(f"Bronze Layer successfully updated with new data.")
            return True

        except Exception as e:
            print(f"Failed to ingest Bronze layer: {e}")
            return False