from sqlalchemy import create_engine

host = "127.0.0.1"
port = 5432
user = "postgres"
password= "mypassword"
database= "store_db"

def load_data_to_postgres(df, table_name):
    """
    Loads a DataFrame into a PostgreSQL database table.

    Args:
        df (pd.DataFrame): The DataFrame to be loaded.
        table_name (str): The name of the target table in the database.
    """
    # Create a connection string
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{database}'
    
    # Create a SQLAlchemy engine
    engine = create_engine(connection_string)
    
    # Load the DataFrame into the specified table in PostgreSQL
    df.to_sql(table_name, engine, if_exists='replace', index=False) 

    print(f"Data loaded into table '{table_name}' successfully.")
    


