
from src.extract import  fetch_products,extract_users
from src.load import  load_data_to_postgres
from src.transform import  transform_users,transform_products

def run_etl():
    """
    Runs the ETL process: Extracts data from the API, transforms it, and loads it into PostgreSQL.
    """
    # Extract data
    product_df = fetch_products()
    user_df = extract_users()

    print("Data transformation is starting." )

    # Transform data
    transformed_product_df = transform_products(product_df)
    transformed_user_df = transform_users(user_df)

    print("Loading to postgres")
    # Load data into PostgreSQL
    load_data_to_postgres(transformed_product_df, 'products')
    load_data_to_postgres(transformed_user_df, 'users')

    print("ETL process completed successfully.")

if  __name__ == "__main__":
    run_etl()

