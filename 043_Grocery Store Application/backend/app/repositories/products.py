from contextlib import contextmanager

from psycopg import errors as pg_errors

from ..errors import ConflictError, NotFoundError, ValidationError

_SELECT_PRODUCTS = ("SELECT p.product_id AS id, p.name, p.icon, p.uom_id, u.uom_name, p.price_per_unit, p.created_at "
                    "FROM products p "
                    "JOIN uom u ON u.uom_id = p.uom_id ")


@contextmanager
def _integrity_errors(product):
    try:
        yield
    except pg_errors.ForeignKeyViolation:
        raise ValidationError(f"Unit of measure {product['uom_id']} does not exist") from None
    except pg_errors.UniqueViolation:
        raise ConflictError(f"A product named '{product['name']}' already exists") from None


def list_products(connection):
    return connection.execute(_SELECT_PRODUCTS + "ORDER BY p.name").fetchall()


def get_product(connection, product_id):
    product = connection.execute(_SELECT_PRODUCTS + "WHERE p.product_id = %s", (product_id,)).fetchone()
    if product is None:
        raise NotFoundError(f"Product {product_id} does not exist")
    return product


def create_product(connection, product):
    with _integrity_errors(product):
        row = connection.execute(
            "INSERT INTO products (name, icon, uom_id, price_per_unit) VALUES (%s, %s, %s, %s) RETURNING product_id",
            (product['name'], product['icon'], product['uom_id'], product['price_per_unit'])
        ).fetchone()
    return row['product_id']


def update_product(connection, product_id, product):
    # Past orders keep their own unit_price, so a price change only affects new orders
    with _integrity_errors(product):
        row = connection.execute(
            "UPDATE products SET name = %s, icon = %s, uom_id = %s, price_per_unit = %s "
            "WHERE product_id = %s RETURNING product_id",
            (product['name'], product['icon'], product['uom_id'], product['price_per_unit'], product_id)
        ).fetchone()
    if row is None:
        raise NotFoundError(f"Product {product_id} does not exist")


def delete_product(connection, product_id):
    try:
        row = connection.execute(
            "DELETE FROM products WHERE product_id = %s RETURNING product_id", (product_id,)
        ).fetchone()
    except (pg_errors.RestrictViolation, pg_errors.ForeignKeyViolation):
        raise ConflictError("Product cannot be deleted because it is part of existing orders") from None
    if row is None:
        raise NotFoundError(f"Product {product_id} does not exist")
