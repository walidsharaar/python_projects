import os
import pandas as pd
from db_connector import SQLServerConnector
from bronze_layer import BronzeIngestor


def get_csv_row_count(csv_path):
    """Helper to quickly get CSV row count without loading full data into memory."""
    try:
        # We use chunking to count rows efficiently for large files
        count = 0
        for chunk in pd.read_csv(csv_path, chunksize=10000, usecols=[0], encoding='ISO-8859-1'):
            count += len(chunk)
        return count
    except Exception as e:
        print(f"Error counting CSV rows: {e}")
        return -1

def table_exists_and_matches(engine, table_name, expected_count):
    """Checks if the SQL table exists and has the same number of records."""
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
    SERVER_NAME = 'localhost' 
    DATABASE_NAME = 'GlobalStoreDB'
    
    # Pathing logic
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "dataset", "dataset.csv")

    # 2. Initialize Database Connection
    db = SQLServerConnector(SERVER_NAME, DATABASE_NAME)
    engine = db.get_engine()
    
    if not db.test_connection():
        print("\n[!] Connection sequence failed.")
        return

    # Get expected count from CSV for incremental check
    print("Checking local dataset status...")
    expected_count = get_csv_row_count(csv_path)

    # 3. Trigger Bronze Ingestion (with Check)
    print("\n--- [STEP 1] Bronze Layer Status ---")
    if table_exists_and_matches(engine, "bronze_global_store", expected_count):
        print(">>> Bronze table is up-to-date. Skipping ingestion.")
    else:
        print(">>> Ingesting Raw Data (Changes detected or table missing)...")
        ingestor = BronzeIngestor(csv_path, engine)
        if not ingestor.load_to_sql():
            print("Pipeline failed at Bronze stage.")
            return
        print("Bronze Step Complete.")



if __name__ == "__main__":
    main()