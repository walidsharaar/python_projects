import pandas as pd
import os
from sqlalchemy import text, inspect

class BronzeIngestor:
    def __init__(self, file_path, db_engine):
        self.file_path = file_path
        self.engine = db_engine
        self.table_name = "bronze_global_store"

    def load_to_sql(self):
        try:
            try:
                df = pd.read_csv(self.file_path, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(self.file_path, encoding='ISO-8859-1')
            
            df.columns = [col.lower().replace(" ", "_").replace("-", "_") for col in df.columns]

            inspector = inspect(self.engine)
            if inspector.has_table(self.table_name):
                with self.engine.connect() as conn:
                    existing_query = text(f"SELECT row_id, order_id, order_date FROM {self.table_name}")
                    existing_df = pd.read_sql(existing_query, conn)
                
                existing_keys = set(
                    existing_df['row_id'].astype(str) + "_" + 
                    existing_df['order_id'].astype(str) + "_" + 
                    existing_df['order_date'].astype(str)
                )
                
                df_keys = (
                    df['row_id'].astype(str) + "_" + 
                    df['order_id'].astype(str) + "_" + 
                    df['order_date'].astype(str)
                )
                new_records_df = df[~df_keys.isin(existing_keys)]
            else:
                new_records_df = df

            if not new_records_df.empty:
                print(f"Ingesting {len(new_records_df)} new records...")
                new_records_df.to_sql(self.table_name, con=self.engine, if_exists='append', index=False)
            return True
        except Exception as e:
            print(f"Bronze Error: {e}")
            return False