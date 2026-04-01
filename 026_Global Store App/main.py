import os
import sys
import pandas as pd

# Add the pipeline directory to the system path to ensure modules are found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.db_connector import SQLServerConnector
from pipeline.bronze_layer import BronzeIngestor
from pipeline.silver_layer import SilverTransformer
from pipeline.gold_layer import GoldTransformer

def get_csv_row_count(csv_path):
    """
    Helper to quickly get CSV row count without loading full data into memory.
    Used for the initial high-level check in the main loop.
    """
    try:
        count = 0
        for chunk in pd.read_csv(csv_path, chunksize=10000, usecols=[0], encoding='ISO-8859-1'):
            count += len(chunk)
        return count
    except Exception as e:
        print(f"Error counting CSV rows: {e}")
        return -1

def table_exists_and_matches(engine, table_name, expected_count):
    """
    Checks if the SQL table exists and if the record count matches the source.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return False
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
            return result == expected_count
    except Exception:
        return False

def main():
    # 1. Configuration
    # Adjust these settings to match your local SQL Server instance
    SERVER_NAME = 'localhost' 
    DATABASE_NAME = 'GlobalStoreDB'
    
    # Pathing logic - ensure dataset is in the 'dataset' folder at project root
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "dataset", "dataset.csv")

    # 2. Initialize Database Connection
    db = SQLServerConnector(SERVER_NAME, DATABASE_NAME)
    engine = db.get_engine()
    
    if not db.test_connection():
        print("\n[!] Connection sequence failed. Please verify SQL Server is running.")
        return

    # Check the source dataset
    print("Scanning local dataset...")
    expected_count = get_csv_row_count(csv_path)
    if expected_count == -1:
        print("[!] Could not read source CSV. Pipeline aborted.")
        return

    # 3. Bronze Layer (Ingestion)
    print("\n--- [STEP 1] Bronze Layer Status ---")
    if table_exists_and_matches(engine, "bronze_global_store", expected_count):
        print(">>> Bronze table is up-to-date. Skipping ingestion.")
    else:
        print(">>> Delta detected. Processing Bronze Ingestion...")
        ingestor = BronzeIngestor(csv_path, engine)
        if not ingestor.load_to_sql():
            print("Pipeline halted at Bronze stage.")
            return

    # 4. Silver Layer (Cleaning)
    print("\n--- [STEP 2] Silver Layer Status ---")
    if table_exists_and_matches(engine, "silver_global_store", expected_count):
        print(">>> Silver table is up-to-date. Skipping transformation.")
    else:
        print(">>> Delta detected. Processing Silver Transformation...")
        transformer = SilverTransformer(engine)
        if not transformer.transform():
            print("Pipeline halted at Silver stage.")
            return

    # 5. Gold Layer (Star Schema)
    print("\n--- [STEP 3] Gold Layer Status ---")
    # We check the Fact table for the record count
    if table_exists_and_matches(engine, "fact_sales", expected_count):
        print(">>> Gold Star Schema is up-to-date. Skipping transformation.")
    else:
        print(">>> Delta detected. Processing Gold Transformation...")
        gold_transformer = GoldTransformer(engine)
        if gold_transformer.transform():
            print("\n✅ Pipeline execution successful. All layers are synchronized.")
        else:
            print("Pipeline failed at Gold stage.")

if __name__ == "__main__":
    main()