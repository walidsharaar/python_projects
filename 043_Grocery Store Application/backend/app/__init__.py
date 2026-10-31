import atexit
import logging
import mimetypes
import os
import secrets
from datetime import date, timedelta
from decimal import Decimal

from flask import Flask, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from . import config
from .api import bp as api_bp
from .db import close_pool, get_connection
from .errors import register_error_handlers

# On Windows these come from the registry, which sometimes maps .js to text/plain;
# browsers refuse to run JavaScript modules served with the wrong type
mimetypes.add_type('text/javascript', '.js')
mimetypes.add_type('text/css', '.css')

logger = logging.getLogger(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
UI_DIR = os.path.abspath(os.path.join(APP_DIR, '..', '..', 'ui'))

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'same-origin',
}


class AppJSONProvider(DefaultJSONProvider):
    @staticmethod
    def default(o):
        # Money values are NUMERIC in Postgres; send them as JSON numbers
        if isinstance(o, Decimal):
            return float(o)
        # Covers datetime too (a subclass of date)
        if isinstance(o, date):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


def create_app():
    logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s %(levelname)s [%(name)s] %(message)s')

    # The UI is a static single-page app served from the same origin as the API
    app = Flask(__name__, static_folder=UI_DIR, static_url_path='')
    app.json = AppJSONProvider(app)
    app.json.sort_keys = False

    secret_key = config.SECRET_KEY
    if len(secret_key) < config.MIN_SECRET_KEY_LENGTH:
        logger.warning("SECRET_KEY in .env is missing or shorter than %s characters: using a temporary key, "
                       "so everyone is signed out when the server restarts. Run setup.bat to generate one.",
                       config.MIN_SECRET_KEY_LENGTH)
        secret_key = secrets.token_urlsafe(48)

    app.config.update(
        SECRET_KEY=secret_key,
        MAX_CONTENT_LENGTH=1024 * 1024,
        SESSION_COOKIE_NAME='freshcart_session',
        SESSION_COOKIE_HTTPONLY=True,
        # Lax: the browser does not send the cookie with cross-site POST/PUT/DELETE requests (CSRF protection).
        # The API also only accepts JSON bodies, which other sites cannot send without a CORS preflight.
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=config.SESSION_COOKIE_SECURE,
        PERMANENT_SESSION_LIFETIME=timedelta(hours=config.SESSION_LIFETIME_HOURS),
    )

    if config.CORS_ORIGINS:
        CORS(app, resources={r'/api/*': {'origins': config.CORS_ORIGINS}}, supports_credentials=True)

    app.register_blueprint(api_bp)
    register_error_handlers(app)

    @app.get('/')
    def index():
        return send_from_directory(UI_DIR, 'index.html')

    @app.get('/health')
    def health():
        with get_connection() as connection:
            connection.execute("SELECT 1")
        return {'status': 'ok'}

    @app.get('/api/docs')
    def api_docs():
        return send_from_directory(APP_DIR, 'docs.html')

    @app.get('/api/v1/openapi.yaml')
    def openapi_spec():
        return send_from_directory(APP_DIR, 'openapi.yaml', mimetype='application/yaml')

    @app.after_request
    def add_security_headers(response):
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    atexit.register(close_pool)
    return app
