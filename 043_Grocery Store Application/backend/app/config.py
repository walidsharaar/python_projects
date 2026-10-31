import os

from dotenv import load_dotenv

# .env lives in the project root, two levels above backend/app/
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '.env'))


def _get_required(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _normalize_database_url(url):
    # Accept SQLAlchemy-style URLs (postgresql+psycopg://) as well as plain libpq ones
    for prefix in ('postgresql+psycopg://', 'postgresql+psycopg2://', 'postgres://'):
        if url.startswith(prefix):
            return 'postgresql://' + url[len(prefix):]
    return url


DATABASE_URL = _normalize_database_url(_get_required('DATABASE_URL'))
DB_POOL_MIN_SIZE = int(os.getenv('DB_POOL_MIN_SIZE', '1'))
DB_POOL_MAX_SIZE = int(os.getenv('DB_POOL_MAX_SIZE', '10'))
DB_POOL_TIMEOUT = float(os.getenv('DB_POOL_TIMEOUT', '10'))

# Signs the session cookie. setup.bat / init_db.py --create-db writes a strong random one into .env
SECRET_KEY = os.getenv('SECRET_KEY', '')
MIN_SECRET_KEY_LENGTH = 32
# Set to 1 when the app is served over HTTPS, so the session cookie is never sent unencrypted
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
SESSION_LIFETIME_HOURS = int(os.getenv('SESSION_LIFETIME_HOURS', '12'))

DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '5000'))

DB_SETUP_HELP = """How to fix:
  1. Check DATABASE_URL in the .env file in the project folder:
       DATABASE_URL=postgresql://grocery_user:<password>@localhost:5432/grocery_db
  2. Let the app create that user and database for you (asks for the password of
     the PostgreSQL admin user 'postgres' that you chose when installing PostgreSQL):
       python init_db.py --create-db --seed
  3. Make sure the PostgreSQL service is running (Windows: services.msc -> postgresql-x64-18)."""

# Comma-separated list of origins allowed to call the API from another origin.
# Leave empty when the UI is served by this app (same origin).
CORS_ORIGINS = [o.strip() for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()]
