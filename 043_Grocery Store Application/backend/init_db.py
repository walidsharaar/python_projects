"""Set up the PostgreSQL database for the Grocery Store app.

Usage (from the backend folder):
    python init_db.py                       # create the tables
    python init_db.py --seed                # create the tables + sample data
    python init_db.py --create-db --seed    # first run: also create the database user and database
                                            # from DATABASE_URL (asks for the PostgreSQL admin password)
    python init_db.py --reset --seed        # DELETE the app's tables and all their data, then recreate them
    python init_db.py --create-admin        # add another administrator, or reset an administrator's password

When no administrator exists yet, it asks for one (or reads ADMIN_USERNAME / ADMIN_FULL_NAME / ADMIN_PASSWORD).
It also writes a strong random SECRET_KEY into .env when the current one is missing or too short.
"""
import argparse
import getpass
import os
import secrets
import sys

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app import auth, config, validation
from app.errors import ValidationError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, '..', '.env')
APP_TABLES = ('order_details', 'orders', 'products', 'uom', 'users')

# What the code needs from tables that already exist (created by an older version of schema.sql)
REQUIRED_COLUMNS = {
    'uom': {'uom_id', 'uom_name'},
    'products': {'product_id', 'name', 'uom_id', 'price_per_unit', 'created_at'},
    'orders': {'order_id', 'customer_name', 'total_price', 'created_at'},
    'order_details': {'order_detail_id', 'order_id', 'product_id', 'quantity', 'unit_price', 'total_price'},
}
REQUIRED_UNIQUE_COLUMNS = {'uom': 'uom_name', 'products': 'name'}

RELATION_KINDS = {'r': 'TABLE', 'p': 'TABLE', 'v': 'VIEW', 'm': 'MATERIALIZED VIEW', 'S': 'SEQUENCE'}


def run_sql_file(connection, file_name):
    with open(os.path.join(BASE_DIR, file_name), encoding='utf-8') as sql_file:
        connection.execute(sql_file.read())
    print(f"Applied {file_name}")


def transfer_ownership(connection, user):
    """Give the app's user ownership of tables someone else created (e.g. 'postgres' via pgAdmin)."""
    connection.execute(sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(user)))

    relations = connection.execute(
        "SELECT c.relname, c.relkind FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p', 'v', 'm', 'S') "
        "AND pg_get_userbyid(c.relowner) <> %s "
        # Sequences behind SERIAL/IDENTITY columns change owner together with their table
        "AND NOT EXISTS (SELECT 1 FROM pg_depend d WHERE d.objid = c.oid AND d.deptype IN ('a', 'i'))",
        (user,)
    ).fetchall()

    for name, kind in relations:
        connection.execute(sql.SQL("ALTER {} {} OWNER TO {}").format(
            sql.SQL(RELATION_KINDS[kind]), sql.Identifier('public', name), sql.Identifier(user)))
    if relations:
        print(f"Made '{user}' the owner of {len(relations)} existing table(s)/object(s)")


def create_database(admin_user):
    """Create (or update the password of) the app's user, and create or take over its database."""
    target = conninfo_to_dict(config.DATABASE_URL)
    user, password, dbname = target.get('user'), target.get('password'), target.get('dbname')
    if not (user and password and dbname):
        sys.exit("DATABASE_URL in .env must contain a user, a password and a database name, e.g.\n"
                 "  DATABASE_URL=postgresql://grocery_user:<password>@localhost:5432/grocery_db")

    admin_password = (os.getenv('POSTGRES_ADMIN_PASSWORD')
                      or getpass.getpass(f"Password of the PostgreSQL admin user '{admin_user}': "))

    def admin_conninfo(database):
        return make_conninfo(config.DATABASE_URL, user=admin_user, password=admin_password, dbname=database)

    with psycopg.connect(admin_conninfo('postgres'), autocommit=True) as connection:
        role_exists = connection.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (user,)).fetchone()
        statement = "ALTER ROLE {} WITH LOGIN PASSWORD {}" if role_exists else "CREATE ROLE {} WITH LOGIN PASSWORD {}"
        connection.execute(sql.SQL(statement).format(sql.Identifier(user), sql.Literal(password)))
        print(f"{'Updated password of' if role_exists else 'Created'} database user '{user}'")

        if connection.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,)).fetchone():
            connection.execute(sql.SQL("ALTER DATABASE {} OWNER TO {}").format(sql.Identifier(dbname), sql.Identifier(user)))
            print(f"Database '{dbname}' already exists, '{user}' is now its owner")
        else:
            connection.execute(sql.SQL("CREATE DATABASE {} OWNER {}").format(sql.Identifier(dbname), sql.Identifier(user)))
            print(f"Created database '{dbname}'")

    with psycopg.connect(admin_conninfo(dbname), autocommit=True) as connection:
        transfer_ownership(connection, user)


def find_schema_problems(connection):
    """Describe how existing tables differ from what the app needs (empty list = fine or no tables yet)."""
    rows = connection.execute(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = ANY(%s)",
        (list(APP_TABLES),)
    ).fetchall()
    existing = {}
    for table, column in rows:
        existing.setdefault(table, set()).add(column)

    problems = []
    for table, required in REQUIRED_COLUMNS.items():
        if table in existing and required - existing[table]:
            problems.append(f"table '{table}' is missing column(s): {', '.join(sorted(required - existing[table]))}")

    for table, column in REQUIRED_UNIQUE_COLUMNS.items():
        if table not in existing:
            continue
        unique = connection.execute(
            "SELECT 1 FROM pg_index i "
            "JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0] "
            "WHERE i.indrelid = %s::regclass AND i.indisunique AND i.indnatts = 1 AND a.attname = %s",
            (f'public.{table}', column)
        ).fetchone()
        if not unique:
            problems.append(f"'{table}.{column}' is not unique")

    return problems


def confirm_reset(problems):
    print("\nThe existing tables were created by an older version of the schema:")
    for problem in problems:
        print(f"  - {problem}")
    print(f"\nTo continue, the tables {', '.join(APP_TABLES)} must be deleted and created again.")
    print("ALL DATA IN THESE TABLES (products, orders) WILL BE LOST.")
    try:
        answer = input("Type 'yes' to delete and recreate them: ")
    except EOFError:
        # No one to answer (e.g. input redirected): treat as "no"
        return False
    return answer.strip().lower() == 'yes'


def reset_tables(connection):
    connection.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
        sql.SQL(', ').join(sql.Identifier('public', table) for table in APP_TABLES)))
    print(f"Deleted tables: {', '.join(APP_TABLES)}")


def ensure_secret_key():
    """Write a strong random SECRET_KEY into .env when it is missing or too short."""
    if len(config.SECRET_KEY) >= config.MIN_SECRET_KEY_LENGTH or not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, encoding='utf-8-sig') as env_file:
        lines = env_file.read().splitlines()

    new_line = f"SECRET_KEY={secrets.token_urlsafe(48)}"
    for index, line in enumerate(lines):
        if line.strip().startswith('SECRET_KEY='):
            lines[index] = new_line
            break
    else:
        lines.append(new_line)

    with open(ENV_FILE, 'w', encoding='utf-8') as env_file:
        env_file.write('\n'.join(lines) + '\n')
    print("Generated a new SECRET_KEY in .env (signs the login sessions)")


def ask_new_password():
    while True:
        password = getpass.getpass(f"  Password (at least {validation.MIN_PASSWORD_LENGTH} characters, typing is hidden): ")
        if len(password) < validation.MIN_PASSWORD_LENGTH:
            print("  Too short, please try again.")
        elif getpass.getpass("  Repeat the password: ") != password:
            print("  The passwords do not match, please try again.")
        else:
            return password


def create_admin(connection, force=False):
    """Create the first administrator (or, with force, add one / reset one's password)."""
    has_admin = connection.execute("SELECT EXISTS (SELECT 1 FROM users WHERE role = 'admin' AND is_active)").fetchone()[0]
    if has_admin and not force:
        return

    print("\nCreate the administrator account you will use to sign in to the app.")
    try:
        username = validation.parse_username(
            os.getenv('ADMIN_USERNAME') or input("  Username [admin]: ").strip() or 'admin')
        full_name = validation.parse_text(
            os.getenv('ADMIN_FULL_NAME') or input("  Full name [Administrator]: ").strip() or 'Administrator', 'full_name')
        password = validation.parse_password(os.getenv('ADMIN_PASSWORD') or ask_new_password())
    except EOFError:
        sys.exit("\nNo administrator was created (no one to answer). Run this in a terminal:\n"
                 "  python init_db.py --create-admin")
    except ValidationError as error:
        sys.exit(f"\nNo administrator was created: {error.message}")

    connection.execute(
        "INSERT INTO users (username, full_name, role, password_hash) VALUES (%s, %s, 'admin', %s) "
        "ON CONFLICT (username) DO UPDATE SET full_name = EXCLUDED.full_name, role = 'admin', is_active = TRUE, "
        "password_hash = EXCLUDED.password_hash, failed_logins = 0, locked_until = NULL",
        (username, full_name, auth.hash_password(password))
    )
    print(f"Administrator '{username}' is ready. Sign in with this username and password.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--seed', action='store_true', help="also load sample data from seed.sql")
    parser.add_argument('--create-db', action='store_true',
                        help="create the database user and database from DATABASE_URL first")
    parser.add_argument('--admin-user', default='postgres', help="PostgreSQL admin user for --create-db (default: postgres)")
    parser.add_argument('--reset', action='store_true',
                        help="delete the app's tables and ALL their data before creating them again")
    parser.add_argument('--create-admin', action='store_true',
                        help="add an administrator or reset an administrator's password")
    args = parser.parse_args()

    ensure_secret_key()
    try:
        if args.create_db:
            create_database(args.admin_user)

        with psycopg.connect(config.DATABASE_URL) as connection:
            if args.reset:
                reset_tables(connection)
            else:
                problems = find_schema_problems(connection)
                if problems:
                    if not confirm_reset(problems):
                        sys.exit("\nNothing was changed. To recreate the tables later run:\n"
                                 "  python init_db.py --reset --seed")
                    reset_tables(connection)

            run_sql_file(connection, 'schema.sql')
            if args.seed:
                run_sql_file(connection, 'seed.sql')
            # Keep the tables even if creating the administrator below is cancelled
            connection.commit()
            create_admin(connection, force=args.create_admin)
    except psycopg.errors.InsufficientPrivilege as error:
        sys.exit(f"\nThe database user has no permission for this:\n  {error}\n\n"
                 "Run 'python init_db.py --create-db --seed' (or setup.bat): it makes the app's user\n"
                 "the owner of the database and its tables.")
    except psycopg.OperationalError as error:
        sys.exit(f"\nCould not connect to PostgreSQL:\n  {error}\n\n{config.DB_SETUP_HELP}")

    print("Database is ready.")


if __name__ == '__main__':
    main()
