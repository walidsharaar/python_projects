import pandas as pd
from sqlalchemy import text, inspect

class SilverTransformer:
    """
    Class responsible for transforming data from the Bronze (raw) layer 
    to the Silver (cleaned/standardized) layer.
    Supports incremental loading to optimize performance.
    """
    def __init__(self, db_engine):
        self.engine = db_engine
        self.source_table = "bronze_global_store"
        self.target_table = "silver_global_store"

    def transform(self):
        """
        Extracts only new records from Bronze, cleans them, and appends to Silver.
        """
        try:
            inspector = inspect(self.engine)
            
            # 1. Incremental Check: Identify records in Bronze not yet in Silver
            if inspector.has_table(self.target_table):
                print(f"Table {self.target_table} exists. Checking for new records from Bronze...")
                
                with self.engine.connect() as conn:
                    # Get unique fingerprints from the existing Silver table
                    existing_keys_query = text(f"SELECT row_id, order_id, order_date FROM {self.target_table}")
                    existing_keys_df = pd.read_sql(existing_keys_query, conn)
                    
                    existing_keys = set(
                        existing_keys_df['row_id'].astype(str) + "_" + 
                        existing_keys_df['order_id'].astype(str) + "_" + 
                        existing_keys_df['order_date'].astype(str)
                    )
                    
                    # Extract ALL data from Bronze to compare
                    bronze_df = pd.read_sql(f"SELECT * FROM {self.source_table}", con=self.engine)
                    
                    # Create fingerprints for Bronze data
                    bronze_keys = (
                        bronze_df['row_id'].astype(str) + "_" + 
                        bronze_df['order_id'].astype(str) + "_" + 
                        bronze_df['order_date'].astype(str)
                    )
                    
                    # Filter: Only keep records NOT in the existing_keys set
                    df = bronze_df[~bronze_keys.isin(existing_keys)]
            else:
                print(f"Table {self.target_table} does not exist. Performing full transformation.")
                df = pd.read_sql(f"SELECT * FROM {self.source_table}", con=self.engine)

            if df.empty:
                print("No new records found in Bronze. Silver layer is already up-to-date.")
                return True

            print(f"Cleaning {len(df)} new records for Silver Layer...")
            
            # 2. Deduplication (within the new batch)
            df = df.drop_duplicates(subset=['row_id', 'order_id', 'order_date'])

            # 3. Date Conversions (Handling the DD-MM-YYYY format)
            date_cols = ['order_date', 'ship_date']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

            # 4. Numeric Standardization
            numeric_cols = ['sales', 'quantity', 'discount', 'profit', 'shipping_cost']
            for col in numeric_cols:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].replace(r'[\$,]', '', regex=True).astype(float)
                    df[col] = df[col].fillna(0.0)

            # 5. Postal Code Cleanup
            if 'postal_code' in df.columns:
                df['postal_code'] = df['postal_code'].fillna('0').astype(str).str.split('.').str[0]

            # 6. Load ONLY new cleaned data into Silver Table using 'append'
            print(f"Appending {len(df)} records into {self.target_table}...")
            df.to_sql(self.target_table, con=self.engine, if_exists='append', index=False)
            
            print(f"Silver Layer successfully updated incrementally.")
            return True

        except Exception as e:
            print(f"Failed to transform Silver layer: {e}")
            return False