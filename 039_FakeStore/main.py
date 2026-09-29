import logging
import sys
from src.extract import extract_users, fetch_products
from src.load import load_data_to_postgres
from src.transform import transform_products, transform_users

# Configure central logging format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("etl_execution.log", mode="a"),
    ],
)

logger = logging.getLogger("ETL_Orchestrator")


def run_etl():
    """Runs the complete ETL pipeline process wrapped in error handling."""
    logger.info("==========================================")
    logger.info("Starting FakeStore ETL Pipeline Execution")
    logger.info("==========================================")

    try:
        # Step 1: Extraction
        product_df = fetch_products()
        user_df = extract_users()

        # Step 2: Transformation
        transformed_product_df = transform_products(product_df)
        transformed_user_df = transform_users(user_df)

        # Step 3: Loading
        load_data_to_postgres(transformed_product_df, "products")
        load_data_to_postgres(transformed_user_df, "users")

        logger.info("🎉 ETL process completed successfully with zero errors.")

    except Exception as e:
        logger.critical(
            f"🔥 Pipeline failed during execution. Cause: {e}", exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    run_etl()