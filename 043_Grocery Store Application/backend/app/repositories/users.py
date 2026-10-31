from psycopg import errors as pg_errors

from ..errors import ConflictError, NotFoundError

# Never include password_hash in anything that is sent to a client
_PUBLIC_COLUMNS = "user_id AS id, username, full_name, role, is_active, last_login_at, created_at"


def list_users(connection):
    return connection.execute(f"SELECT {_PUBLIC_COLUMNS} FROM users ORDER BY is_active DESC, full_name").fetchall()


def get_user(connection, user_id):
    user = connection.execute(f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE user_id = %s", (user_id,)).fetchone()
    if user is None:
        raise NotFoundError(f"User {user_id} does not exist")
    return user


def get_session_record(connection, user_id):
    return connection.execute(
        f"SELECT {_PUBLIC_COLUMNS}, password_hash FROM users WHERE user_id = %s", (user_id,)
    ).fetchone()


def get_auth_record(connection, username):
    return connection.execute(
        f"SELECT {_PUBLIC_COLUMNS}, password_hash, "
        "COALESCE(locked_until > now(), false) AS is_locked, "
        "EXTRACT(EPOCH FROM locked_until - now()) AS lock_seconds "
        "FROM users WHERE username = %s",
        (username,)
    ).fetchone()


def has_active_admin(connection, excluding_user_id=None):
    return connection.execute(
        "SELECT EXISTS (SELECT 1 FROM users WHERE role = 'admin' AND is_active AND user_id IS DISTINCT FROM %s) AS found",
        (excluding_user_id,)
    ).fetchone()['found']


def create_user(connection, user, password_hash):
    try:
        row = connection.execute(
            "INSERT INTO users (username, full_name, role, password_hash) VALUES (%s, %s, %s, %s) RETURNING user_id",
            (user['username'], user['full_name'], user['role'], password_hash)
        ).fetchone()
    except pg_errors.UniqueViolation:
        raise ConflictError(f"The username '{user['username']}' is already taken") from None
    return row['user_id']


def update_user(connection, user_id, user, password_hash=None):
    row = connection.execute(
        "UPDATE users SET full_name = %s, role = %s, is_active = %s, "
        "password_hash = COALESCE(%s, password_hash), "
        # A password reset by an admin also lifts a sign-in lock
        "failed_logins = CASE WHEN %s::text IS NULL THEN failed_logins ELSE 0 END, "
        "locked_until = CASE WHEN %s::text IS NULL THEN locked_until ELSE NULL END "
        "WHERE user_id = %s RETURNING user_id",
        (user['full_name'], user['role'], user['is_active'], password_hash, password_hash, password_hash, user_id)
    ).fetchone()
    if row is None:
        raise NotFoundError(f"User {user_id} does not exist")


def set_password(connection, user_id, password_hash):
    connection.execute("UPDATE users SET password_hash = %s WHERE user_id = %s", (password_hash, user_id))


def record_failed_login(connection, user_id, max_attempts, lock_minutes):
    # After max_attempts wrong passwords in a row the account is locked for lock_minutes
    connection.execute(
        "UPDATE users SET "
        "locked_until = CASE WHEN failed_logins + 1 >= %(max)s THEN now() + make_interval(mins => %(mins)s) ELSE locked_until END, "
        "failed_logins = CASE WHEN failed_logins + 1 >= %(max)s THEN 0 ELSE failed_logins + 1 END "
        "WHERE user_id = %(id)s",
        {'max': max_attempts, 'mins': lock_minutes, 'id': user_id}
    )


def record_successful_login(connection, user_id):
    connection.execute(
        "UPDATE users SET failed_logins = 0, locked_until = NULL, last_login_at = now() WHERE user_id = %s", (user_id,)
    )
