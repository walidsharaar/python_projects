"""Entry point: `python server.py`, or `waitress-serve --listen=0.0.0.0:5000 server:app`."""
import logging
import sys

import psycopg
from psycopg import errors as pg_errors

from app import config, create_app

app = create_app()
logger = logging.getLogger('grocery_store')


def check_database():
    """Fail fast with a readable message instead of starting a server that can only return errors."""
    try:
        with psycopg.connect(config.DATABASE_URL, connect_timeout=5) as connection:
            connection.execute("SELECT icon FROM products LIMIT 1")
            has_admin = connection.execute("SELECT 1 FROM users WHERE role = 'admin' AND is_active").fetchone()
    except (pg_errors.UndefinedTable, pg_errors.UndefinedColumn):
        sys.exit("The database tables are missing or out of date. Run setup.bat again, or:\n"
                 "  python init_db.py --seed")
    except psycopg.OperationalError as error:
        sys.exit(f"\nCould not connect to PostgreSQL:\n  {error}\n\n{config.DB_SETUP_HELP}")

    if not has_admin:
        sys.exit("There is no administrator account yet, so nobody could sign in. Create one with:\n"
                 "  python init_db.py --create-admin      (or run setup.bat again)")


if __name__ == "__main__":
    check_database()

    if config.DEBUG:
        logger.info("Starting Flask development server on %s:%s", config.HOST, config.PORT)
        app.run(host=config.HOST, port=config.PORT, debug=True)
    else:
        from waitress import serve

        logger.info("Starting Grocery Store Management System - open http://%s:%s/", config.HOST, config.PORT)
        logger.info("API documentation: http://%s:%s/api/docs", config.HOST, config.PORT)
        serve(app, host=config.HOST, port=config.PORT)
