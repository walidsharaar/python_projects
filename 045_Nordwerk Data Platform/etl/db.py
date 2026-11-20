"""Shared database connection. Reads credentials from .env"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv() 


def get_engine(database: str | None = None):
    """Return a SQLAlchemy engine. Default database: POSTGRES_DB from .env."""
    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ["POSTGRES_PORT"]),
        database=database or os.environ["POSTGRES_DB"],
    )
    return create_engine(url)


if __name__ == "__main__":
    with get_engine().connect() as conn:
        print(conn.execute(text("SELECT version()")).scalar())