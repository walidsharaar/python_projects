"""Sign-in with server-checked passwords and a signed, HttpOnly session cookie; role checks."""
import hashlib
import math
from functools import wraps

from flask import g, session
from werkzeug.security import check_password_hash, generate_password_hash

from .db import get_connection
from .errors import ForbiddenError, TooManyRequestsError, UnauthorizedError
from .repositories import users

MAX_FAILED_LOGINS = 5
LOCK_MINUTES = 5
INVALID_CREDENTIALS = "Invalid username or password"

# Checked when the username does not exist, so that case takes as long as a wrong password
_DUMMY_HASH = generate_password_hash('not-a-real-password')


def hash_password(password):
    # Werkzeug's default: salted scrypt
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def _fingerprint(password_hash):
    # Stored in the session: when the password changes, all older sessions stop working
    return hashlib.sha256(password_hash.encode()).hexdigest()[:32]


def start_session(user_id, password_hash):
    session.clear()
    session.permanent = True
    session['user_id'] = user_id
    session['fingerprint'] = _fingerprint(password_hash)
    g.pop('user', None)


def end_session():
    session.clear()
    g.pop('user', None)


def authenticate(connection, username, password):
    """Return the user's auth record, or raise. Failed attempts are counted and lock the account."""
    user = users.get_auth_record(connection, username)
    if user is None:
        verify_password(_DUMMY_HASH, password)
        raise UnauthorizedError(INVALID_CREDENTIALS)

    if user['is_locked']:
        minutes = max(1, math.ceil(float(user['lock_seconds']) / 60))
        raise TooManyRequestsError(f"Too many failed sign-in attempts. Try again in {minutes} minute(s).")

    if not verify_password(user['password_hash'], password):
        users.record_failed_login(connection, user['id'], MAX_FAILED_LOGINS, LOCK_MINUTES)
        connection.commit()  # keep the counter although this request fails
        raise UnauthorizedError(INVALID_CREDENTIALS)

    if not user['is_active']:
        raise ForbiddenError("This account is disabled. Please contact an administrator.")

    users.record_successful_login(connection, user['id'])
    return user


def current_user():
    """The signed-in, active user for this request (cached), or None."""
    if 'user' in g:
        return g.user

    g.user = None
    user_id = session.get('user_id')
    if user_id:
        with get_connection() as connection:
            record = users.get_session_record(connection, user_id)
        if record and record['is_active'] and session.get('fingerprint') == _fingerprint(record.pop('password_hash')):
            g.user = record
        else:
            session.clear()
    return g.user


def require_user():
    user = current_user()
    if user is None:
        raise UnauthorizedError("Please sign in")
    return user


def require_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if require_user()['role'] not in roles:
                raise ForbiddenError("You do not have permission to do this")
            return view(*args, **kwargs)
        return wrapper
    return decorator
