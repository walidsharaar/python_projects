import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_parloa_dataset(n_records=1000):
    np.random.seed(42)
    
    # 1. Interactions Table (Agentic AI Performance)
    start_date = datetime(2024, 1, 1)
    data = {
        'interaction_id': [f"INT-{i:06d}" for i in range(n_records)],
        'timestamp': [start_date + timedelta(minutes=np.random.randint(0, 525600)) for i in range(n_records)],
        'customer_id': [f"CUST-{np.random.randint(1000, 5000)}" for _ in range(n_records)],
        'channel': np.random.choice(['Voice', 'Chat', 'WhatsApp', 'Messenger'], n_records, p=[0.4, 0.3, 0.2, 0.1]),
        'intent': np.random.choice(['Refund', 'Booking', 'Status Check', 'Technical Support', 'Payment'], n_records),
        'duration_seconds': np.random.gamma(shape=2, scale=60, size=n_records), # AHT proxy
        'is_contained': np.random.choice([0, 1], n_records, p=[0.3, 0.7]), # KPI: Containment Rate
        'nps_score': np.random.randint(0, 11, n_records),
        'cost_per_interaction': np.random.uniform(0.10, 0.50, n_records)
    }
    
    df_interactions = pd.DataFrame(data)
    
    # 2. Financial/SaaS Metrics (FP&A Alignment)
    clients = ['Booking.com', 'HealthEquity', 'Allianz', 'SAP', 'TUI']
    fin_data = {
        'client_name': clients,
        'contract_value_mrr': [25000, 45000, 60000, 35000, 50000],
        'interaction_quota': [100000, 250000, 500000, 150000, 300000],
        'actual_usage': [95000, 260000, 480000, 140000, 290000],
        'retention_risk_score': np.random.uniform(0.1, 0.9, 5)
    }
    df_clients = pd.DataFrame(fin_data)
    
    return df_interactions, df_clients

if __name__ == "__main__":
    df_int, df_cli = generate_parloa_dataset()
    df_int.to_csv('parloa_interactions.csv', index=False)
    df_cli.to_csv('parloa_clients.csv', index=False)
    print("Synthetic data generated successfully.")