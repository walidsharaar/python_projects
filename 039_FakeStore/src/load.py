import logging
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError

logger = logging.getLogger(__name__)

# Connection Parameters
HOST = "127.0.0.1"
PORT = 5432
USER = "postgres"
PASSWORD = quote_plus("mypassword")
DATABASE = "store_db"


def load_data_to_postgres(df, table_name):
    """Loads a pandas DataFrame into PostgreSQL database with error handling.

    Args:
        df (pd.DataFrame): Data frame to write.
        table_name (str): Destination database table name.
    """
    if df.empty:
        logger.warning(
            f"Skipping database load for '{table_name}' — DataFrame is empty."
        )
        return

    # Use 'postgresql+psycopg://' (Psycopg 3) to prevent Windows encoding crashes on error messages
    connection_string = (
        f"postgresql+psycopg://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}"
    )

    try:
        logger.info(
            f"Connecting to database and loading data into '{table_name}'..."
        )
        engine = create_engine(
            connection_string,
            connect_args={
                "connect_timeout": 5,
            },
        )

        df.to_sql(table_name, engine, if_exists="replace", index=False)
        logger.info(
            f"Successfully written {len(df)} records into table '{table_name}'."
        )

    except OperationalError as op_err:
        logger.error(
            f"Could not connect to PostgreSQL database on {HOST}:{PORT}. Details: {op_err}"
        )
        raise
    except SQLAlchemyError as sql_err:
        logger.error(
            f"SQLAlchemy database error loading into '{table_name}': {sql_err}"
        )
        raise
    except Exception as err:
        logger.error(
            f"Unexpected error occurred loading table '{table_name}': {err}"
        )
        raise