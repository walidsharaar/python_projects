import pandas as pd
from sqlalchemy import text

class SilverTransformer:
    """
    Class responsible for transforming data from the Bronze (raw) layer 
    to the Silver (cleaned/standardized) layer.
    """
    def __init__(self, db_engine):
        self.engine = db_engine
        self.source_table = "bronze_global_store"
        self.target_table = "silver_global_store"

    def transform(self):
        """
        Extracts from Bronze, cleans, and loads into Silver.
        """
        try:
            print(f"Reading data from {self.source_table}...")
            # Extract raw data from SQL
            df = pd.read_sql(f"SELECT * FROM {self.source_table}", con=self.engine)
            
            if df.empty:
                print("Source table is empty. Aborting transformation.")
                return False

            print("Cleaning data for Silver Layer...")
            
            # 1. Deduplication
            initial_count = len(df)
            df = df.drop_duplicates()
            if len(df) < initial_count:
                print(f"Removed {initial_count - len(df)} duplicate records.")

            # 2. Date Conversions (Handling the DD-MM-YYYY format)
            date_cols = ['order_date', 'ship_date']
            for col in date_cols:
                if col in df.columns:
                    # Using dayfirst=True to match the sample data provided
                    df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

            # 3. Numeric Standardization
            # Ensure these are floats even if they were ingested as strings
            numeric_cols = ['sales', 'quantity', 'discount', 'profit', 'shipping_cost']
            for col in numeric_cols:
                if col in df.columns:
                    if df[col].dtype == 'object':
                        df[col] = df[col].replace(r'[\$,]', '', regex=True).astype(float)
                    df[col] = df[col].fillna(0.0)

            # 4. Postal Code Cleanup (Cast to string to avoid losing leading zeros)
            if 'postal_code' in df.columns:
                df['postal_code'] = df['postal_code'].fillna('0').astype(str).str.split('.').str[0]

            # 5. Load cleaned data into Silver Table
            print(f"Loading {len(df)} records into {self.target_table}...")
            df.to_sql(self.target_table, con=self.engine, if_exists='replace', index=False)
            
            print(f"Silver Layer successfully updated in SQL Server.")
            return True

        except Exception as e:
            print(f"Failed to transform Silver layer: {e}")
            return False