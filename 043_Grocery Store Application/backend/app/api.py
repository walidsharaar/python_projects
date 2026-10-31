"""REST API v1. Request and response bodies are JSON; errors are RFC 9457 problem details.

Every endpoint requires a signed-in user except those in PUBLIC_ENDPOINTS.
Admins can do everything; cashiers can sell and look at products and orders.
"""
import logging

from flask import Blueprint, request, url_for

from . import auth, validation
from .auth import require_role
from .db import get_connection
from .errors import ConflictError, ValidationError
from .repositories import orders, products, stats, uoms, users

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__, url_prefix='/api/v1')

PUBLIC_ENDPOINTS = {'api.login', 'api.logout'}
ADMIN = 'admin'


@bp.before_request
def require_sign_in():
    if request.endpoint not in PUBLIC_ENDPOINTS and request.method != 'OPTIONS':
        auth.require_user()


def json_body():
    # Flask answers 415 for a non-JSON Content-Type and 400 for malformed JSON
    return request.get_json()


# --- Authentication ---

@bp.post('/auth/login')
def login():
    username, password = validation.parse_login(json_body())
    with get_connection() as connection:
        user = auth.authenticate(connection, username, password)
        auth.start_session(user['id'], user['password_hash'])
        profile = users.get_user(connection, user['id'])
    logger.info("User %s signed in", username)
    return profile


@bp.post('/auth/logout')
def logout():
    auth.end_session()
    return '', 204


@bp.get('/auth/me')
def get_me():
    return auth.current_user()


@bp.put('/auth/password')
def change_password():
    current_password, new_password = validation.parse_password_change(json_body())
    me = auth.current_user()
    with get_connection() as connection:
        record = users.get_auth_record(connection, me['username'])
        if not auth.verify_password(record['password_hash'], current_password):
            raise ValidationError("The current password is incorrect")
        password_hash = auth.hash_password(new_password)
        users.set_password(connection, me['id'], password_hash)
    # Other sessions of this user end; this one continues with the new fingerprint
    auth.start_session(me['id'], password_hash)
    logger.info("User %s changed their password", me['username'])
    return '', 204


# --- Users (admin) ---

@bp.get('/users')
@require_role(ADMIN)
def list_users():
    with get_connection() as connection:
        return {'items': users.list_users(connection)}


@bp.post('/users')
@require_role(ADMIN)
def create_user():
    data = validation.parse_new_user(json_body())
    with get_connection() as connection:
        user_id = users.create_user(connection, data, auth.hash_password(data['password']))
        user = users.get_user(connection, user_id)
    logger.info("Created %s user %s", data['role'], data['username'])
    return user, 201, {'Location': url_for('api.get_user', user_id=user_id)}


@bp.get('/users/<int:user_id>')
@require_role(ADMIN)
def get_user(user_id):
    with get_connection() as connection:
        return users.get_user(connection, user_id)


@bp.put('/users/<int:user_id>')
@require_role(ADMIN)
def update_user(user_id):
    data = validation.parse_user_update(json_body())
    loses_admin = data['role'] != ADMIN or not data['is_active']

    if user_id == auth.current_user()['id'] and loses_admin:
        raise ConflictError("You cannot remove your own admin rights or deactivate your own account")

    with get_connection() as connection:
        target = users.get_user(connection, user_id)
        if target['role'] == ADMIN and loses_admin and not users.has_active_admin(connection, excluding_user_id=user_id):
            raise ConflictError("At least one active administrator is required")
        password_hash = auth.hash_password(data['password']) if data['password'] else None
        users.update_user(connection, user_id, data, password_hash)
        user = users.get_user(connection, user_id)
    logger.info("Updated user %s", user['username'])
    return user


# --- Units of measure ---

@bp.get('/uoms')
def list_uoms():
    with get_connection() as connection:
        return {'items': uoms.list_uoms(connection)}


# --- Products ---

@bp.get('/products')
def list_products():
    with get_connection() as connection:
        return {'items': products.list_products(connection)}


@bp.post('/products')
@require_role(ADMIN)
def create_product():
    data = validation.parse_product(json_body())
    with get_connection() as connection:
        product_id = products.create_product(connection, data)
        product = products.get_product(connection, product_id)
    logger.info("Created product %s (%s)", product_id, data['name'])
    return product, 201, {'Location': url_for('api.get_product', product_id=product_id)}


@bp.get('/products/<int:product_id>')
def get_product(product_id):
    with get_connection() as connection:
        return products.get_product(connection, product_id)


@bp.put('/products/<int:product_id>')
@require_role(ADMIN)
def update_product(product_id):
    data = validation.parse_product(json_body())
    with get_connection() as connection:
        products.update_product(connection, product_id, data)
        product = products.get_product(connection, product_id)
    logger.info("Updated product %s (%s)", product_id, data['name'])
    return product


@bp.delete('/products/<int:product_id>')
@require_role(ADMIN)
def delete_product(product_id):
    with get_connection() as connection:
        products.delete_product(connection, product_id)
    logger.info("Deleted product %s", product_id)
    return '', 204


# --- Orders ---

@bp.get('/orders')
def list_orders():
    query = validation.parse_order_query(request.args)
    with get_connection() as connection:
        items, total = orders.list_orders(connection, query['limit'], query['offset'], query['search'])
    return {'items': items, 'total': total, 'limit': query['limit'], 'offset': query['offset']}


@bp.post('/orders')
def create_order():
    customer_name, items = validation.parse_order(json_body())
    seller = auth.current_user()
    with get_connection() as connection:
        order_id = orders.create_order(connection, customer_name, items, created_by=seller['id'])
        order = orders.get_order(connection, order_id)
    logger.info("Order %s for %s by %s, total %s", order_id, customer_name, seller['username'], order['total'])
    return order, 201, {'Location': url_for('api.get_order', order_id=order_id)}


@bp.get('/orders/<int:order_id>')
def get_order(order_id):
    with get_connection() as connection:
        return orders.get_order(connection, order_id)


# --- Statistics (admin) ---

@bp.get('/stats/summary')
@require_role(ADMIN)
def get_stats_summary():
    days = validation.parse_days(request.args)
    with get_connection() as connection:
        return stats.get_summary(connection, days)
