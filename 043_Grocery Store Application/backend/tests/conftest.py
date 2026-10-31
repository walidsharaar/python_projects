import os
import sys

import pytest

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

TEST_DATABASE_URL = os.getenv('TEST_DATABASE_URL')
if TEST_DATABASE_URL:
    # Must be set before app.config is imported; load_dotenv never overrides existing variables
    os.environ['DATABASE_URL'] = TEST_DATABASE_URL
else:
    os.environ.setdefault('DATABASE_URL', 'postgresql://unused/unused')

ADMIN = {'username': 'admin', 'password': 'admin-pass-123', 'full_name': 'Ada Admin', 'role': 'admin'}
CASHIER = {'username': 'cashier', 'password': 'cashier-pass-123', 'full_name': 'Carl Cashier', 'role': 'cashier'}


@pytest.fixture(scope='session')
def app():
    from app import create_app

    flask_app = create_app()
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture(scope='session')
def password_hashes():
    # Hashing is deliberately slow, so do it once per test run
    from app import auth
    return {user['username']: auth.hash_password(user['password']) for user in (ADMIN, CASHIER)}


@pytest.fixture
def database(password_hashes):
    """A freshly created and seeded database with one admin and one cashier."""
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run API tests (the database will be wiped)")

    import psycopg
    import init_db

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        connection.execute("DROP TABLE IF EXISTS order_details, orders, products, uom, users CASCADE")
        init_db.run_sql_file(connection, 'schema.sql')
        init_db.run_sql_file(connection, 'seed.sql')
        for user in (ADMIN, CASHIER):
            connection.execute(
                "INSERT INTO users (username, full_name, role, password_hash) VALUES (%s, %s, %s, %s)",
                (user['username'], user['full_name'], user['role'], password_hashes[user['username']]))


def sign_in(client, user):
    response = client.post('/api/v1/auth/login', json={'username': user['username'], 'password': user['password']})
    assert response.status_code == 200, response.get_json()
    return client


@pytest.fixture
def anon(app, database):
    return app.test_client()


@pytest.fixture
def client(app, database):
    """Signed in as the admin."""
    return sign_in(app.test_client(), ADMIN)


@pytest.fixture
def cashier(app, database):
    return sign_in(app.test_client(), CASHIER)
