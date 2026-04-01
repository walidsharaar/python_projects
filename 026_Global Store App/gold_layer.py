import pandas as pd
from sqlalchemy import text

class GoldTransformer:
    """
    Class responsible for transforming Silver data into a Star Schema.
    - Dimensions: Product, Customer, Location, Date
    - Fact: Sales
    """
    def __init__(self, db_engine):
        self.engine = db_engine
        self.source_table = "silver_global_store"

    def transform(self):
        """Extracts from Silver and creates Dimension and Fact tables."""
        try:
            print(f"Reading data from {self.source_table}...")
            # Load the cleaned silver data
            df = pd.read_sql(f"SELECT * FROM {self.source_table}", con=self.engine)
            
            if df.empty:
                print("Source table is empty. Aborting Gold transformation.")
                return False

            print("Generating Star Schema tables...")

            # 1. Dim_Product: Unique products and their categories
            dim_product = df[['product_id', 'product_name', 'category', 'sub_category']].drop_duplicates('product_id')
            
            # 2. Dim_Customer: Unique customers and their segments
            dim_customer = df[['customer_id', 'customer_name', 'segment']].drop_duplicates('customer_id')

            # 3. Dim_Location: Geography dimension with a generated surrogate key
            loc_cols = ['city', 'state', 'country', 'market', 'region']
            dim_location = df[loc_cols].drop_duplicates().reset_index(drop=True)
            dim_location.insert(0, 'location_key', dim_location.index + 1)

            # 4. Dim_Date: Rich time dimension derived from order_date
            df['order_date'] = pd.to_datetime(df['order_date'])
            min_date = df['order_date'].min()
            max_date = df['order_date'].max()
            
            date_range = pd.date_range(start=min_date, end=max_date)
            dim_date = pd.DataFrame({
                'date_key': date_range,
                'year': date_range.year,
                'quarter': date_range.quarter,
                'month': date_range.month,
                'day': date_range.day,
                'weekday': date_range.day_name(),
                'is_weekend': date_range.weekday >= 5
            })

            # 5. Fact_Sales: The central table linking all dimensions
            # Map the location_key back to the transactional data
            fact_sales = df.merge(dim_location, on=loc_cols, how='left')
            
            # Select final columns for the Fact table (Foreign Keys and Measures)
            fact_cols = [
                'row_id', 'order_id', 'order_date', 'customer_id', 
                'product_id', 'location_key', 'sales', 'quantity', 
                'discount', 'profit', 'shipping_cost', 'order_priority'
            ]
            fact_sales = fact_sales[[c for c in fact_cols if c in fact_sales.columns]]

            # Write all tables to SQL Server using 'replace' to ensure schema consistency
            gold_tables = {
                "dim_product": dim_product,
                "dim_customer": dim_customer,
                "dim_location": dim_location,
                "dim_date": dim_date,
                "fact_sales": fact_sales
            }

            for table_name, table_df in gold_tables.items():
                print(f"Loading {table_name} ({len(table_df)} rows)...")
                table_df.to_sql(table_name, con=self.engine, if_exists='replace', index=False)

            print("Gold Layer Star Schema successfully created.")
            return True

        except Exception as e:
            print(f"Failed to transform Gold layer: {e}")
            return False