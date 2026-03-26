# Day 13: The Debugging Challenge (Data Pipeline Edition)
# Goal: Find and fix 5 intentional bugs to make the pipeline functional.
# Concepts: Scope, Indexing, Type Conversion, and Logic errors.

import random

# --- GLOBAL CONFIGURATION ---
TAX_RATE = 0.05 

def calculate_total(prices):
    """Calculates total price including global tax rate."""
    total = 0
    for price in prices:
        # BUG 1: Type Error (Check how 'price' is handled)
        total += price
    
    # BUG 2: Scope Error (Can we access 'tax_amount' outside or use TAX_RATE correctly?)
    total_with_tax = total * (1 + TAX_RATE)
    return total_with_tax

def get_status(score):
    """Returns status based on score thresholds."""
    # BUG 3: Logical/Comparison Error (Check the boundaries)
    if score > 100:
        return "High Volume"
    elif score > 50:
        return "Medium Volume"
    else:
        return "Low Volume"

def run_pipeline():
    print("--- Starting Data Pipeline Audit ---")
    
    # Raw Data: A list of dictionaries representing transactions
    raw_data = [
        {"id": 1, "price": "100", "status": "pending"},
        {"id": 2, "price": "250", "status": "completed"},
        {"id": 3, "price": "50", "status": "completed"},
    ]
    
    processed_prices = []
    
    # BUG 4: Iteration/Index Error 
    # (The range is often a trap for beginners)
    for i in range(1, len(raw_data)):
        item = raw_data[i]
        if item["status"] == "completed":
            processed_prices.append(item["price"])

    # Calculate final metrics
    final_total = calculate_total(processed_prices)
    
    # BUG 5: Output/Formatting Error
    # (Trying to print the total with a description)
    print("Pipeline Complete. Total Processed: " + final_total)
    
    volume_desc = get_status(final_total)
    print(f"Volume Category: {volume_desc}")

if __name__ == "__main__":
    run_pipeline()
