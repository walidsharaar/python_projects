import pandas as pd
from sqlalchemy import text, inspect

class GoldTransformer:
    def __init__(self, db_engine):
        self.engine = db_engine
        self.source_table = "silver_global_store"

    def transform(self):
        try:
            print("Processing Gold Layer...")
            df = pd.read_sql(f"SELECT * FROM {self.source_table}", con=self.engine)
            inspector = inspect(self.engine)

            # Fact Incremental Check
            if inspector.has_table("fact_sales"):
                with self.engine.connect() as conn:
                    existing = pd.read_sql(text("SELECT row_id, order_id, order_date FROM fact_sales"), conn)
                    exist_keys = set(existing['row_id'].astype(str) + "_" + existing['order_id'].astype(str) + "_" + existing['order_date'].astype(str))
                    df_keys = df['row_id'].astype(str) + "_" + df['order_id'].astype(str) + "_" + df['order_date'].astype(str)
                    new_df = df[~df_keys.isin(exist_keys)]
            else:
                new_df = df

            # 1. Dim_Product (Replace to ensure attributes are current)
            dim_product = df[['product_id', 'product_name', 'category', 'sub_category']].drop_duplicates('product_id')
            dim_product.to_sql("dim_product", con=self.engine, if_exists='replace', index=False)

            # 2. Dim_Location
            loc_cols = ['city', 'state', 'country', 'market', 'region']
            dim_location = df[loc_cols].drop_duplicates().reset_index(drop=True)
            dim_location.insert(0, 'location_key', dim_location.index + 1)
            dim_location.to_sql("dim_location", con=self.engine, if_exists='replace', index=False)

            # 3. Fact_Sales (Append Only New)
            if not new_df.empty:
                fact_sales = new_df.merge(dim_location, on=loc_cols, how='left')
                fact_cols = ['row_id', 'order_id', 'order_date', 'customer_id', 'product_id', 'location_key', 'sales', 'profit']
                fact_sales = fact_sales[[c for c in fact_cols if c in fact_sales.columns]]
                fact_sales.to_sql("fact_sales", con=self.engine, if_exists='append', index=False)
            
            print("Gold Layer updated.")
            return True
        except Exception as e:
            print(f"Gold Error: {e}")
            return False