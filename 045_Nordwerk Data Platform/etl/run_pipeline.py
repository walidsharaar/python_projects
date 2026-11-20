"""
Run the whole Nordwerk pipeline in the right order with one command.

    setup -> bronze -> silver -> gold -> data quality

Usage (from the project folder):
    python -m etl.run_pipeline              # load and transform
    python -m etl.run_pipeline --generate   # re-create the source data first

Exit code 0 = all good, 1 = a data quality rule with status ERROR failed.
"""
import argparse
import sys
import time
from pathlib import Path

from etl import load_bronze, run_dq
from etl.run_sql import run_sql_path
from generator import company_a_b1, company_b_csv, sustainability_excel

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def step(name, func):
    """Run one pipeline step and print how long it took."""
    print(f"\n=== {name} ===")
    start = time.perf_counter()
    result = func()
    print(f"--- {name} done in {time.perf_counter() - start:.1f} s")
    return result


def generate_sources():
    company_a_b1.main()          # A first: B and the Excel file read A's data
    company_b_csv.main()
    sustainability_excel.main()


def main():
    parser = argparse.ArgumentParser(description="Nordwerk data pipeline")
    parser.add_argument("--generate", action="store_true",
                        help="re-create the simulated source data first")
    args = parser.parse_args()

    if args.generate:
        step("Generate sources", generate_sources)

    step("Setup", lambda: run_sql_path(SQL_DIR / "00_setup"))
    step("Bronze", load_bronze.main)
    step("Silver", lambda: run_sql_path(SQL_DIR / "20_silver"))
    step("Gold", lambda: run_sql_path(SQL_DIR / "30_gold"))
    step("DQ rules", lambda: run_sql_path(SQL_DIR / "40_dq"))
    dq_status = step("DQ checks", run_dq.main)

    print(f"\nPipeline finished. Data quality: {dq_status}")
    sys.exit(0 if dq_status == "success" else 1)


if __name__ == "__main__":
    main()