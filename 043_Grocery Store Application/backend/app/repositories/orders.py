from decimal import Decimal, ROUND_HALF_UP

from ..errors import NotFoundError, ValidationError

CENTS = Decimal('0.01')

# Orders joined with their line items; {orders} is a subquery selecting which orders to load
_SELECT_ORDERS_WITH_ITEMS = (
    "SELECT o.order_id, o.customer_name, o.total_price AS order_total, o.created_at, "
    "o.created_by, staff.full_name AS created_by_name, "
    "d.order_detail_id, d.product_id, d.quantity, d.unit_price, d.total_price AS line_total, "
    "p.name AS product_name, p.icon AS product_icon, u.uom_name "
    "FROM ({orders}) o "
    "LEFT JOIN users staff ON staff.user_id = o.created_by "
    "LEFT JOIN order_details d ON d.order_id = o.order_id "
    "LEFT JOIN products p ON p.product_id = d.product_id "
    "LEFT JOIN uom u ON u.uom_id = p.uom_id "
    "ORDER BY o.created_at DESC, o.order_id DESC, d.order_detail_id"
)


def _group_orders(rows):
    orders = {}
    for row in rows:
        order = orders.get(row['order_id'])
        if order is None:
            order = orders[row['order_id']] = {
                'id': row['order_id'],
                'customer_name': row['customer_name'],
                'total': row['order_total'],
                'created_at': row['created_at'],
                'created_by': row['created_by'],
                'created_by_name': row['created_by_name'],
                'items': [],
            }
        if row['order_detail_id'] is not None:
            order['items'].append({
                'product_id': row['product_id'],
                'product_name': row['product_name'],
                'product_icon': row['product_icon'],
                'uom_name': row['uom_name'],
                'quantity': row['quantity'],
                # Price at the time of the order, not the product's current price
                'unit_price': row['unit_price'],
                'total': row['line_total'],
            })
    return list(orders.values())


def _escape_like(text):
    return text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def list_orders(connection, limit, offset, search=None):
    """Newest orders first. `search` matches the customer name, or the order number ("12" or "#12")."""
    where, params = "", []
    if search:
        where = "WHERE customer_name ILIKE %s OR order_id::text = %s"
        params = [f"%{_escape_like(search)}%", search.lstrip('#')]

    total = connection.execute(f"SELECT count(*) AS total FROM orders {where}", params).fetchone()['total']
    page = f"SELECT * FROM orders {where} ORDER BY created_at DESC, order_id DESC LIMIT %s OFFSET %s"
    rows = connection.execute(_SELECT_ORDERS_WITH_ITEMS.format(orders=page), [*params, limit, offset])
    return _group_orders(rows), total


def get_order(connection, order_id):
    rows = connection.execute(
        _SELECT_ORDERS_WITH_ITEMS.format(orders="SELECT * FROM orders WHERE order_id = %s"), (order_id,)
    ).fetchall()
    if not rows:
        raise NotFoundError(f"Order {order_id} does not exist")
    return _group_orders(rows)[0]


def create_order(connection, customer_name, items, created_by):
    """Create an order and its line items in one transaction. Prices come from the products table."""
    product_ids = list({item['product_id'] for item in items})
    rows = connection.execute(
        "SELECT product_id, price_per_unit FROM products WHERE product_id = ANY(%s)", (product_ids,)
    ).fetchall()
    prices = {row['product_id']: row['price_per_unit'] for row in rows}

    missing = sorted(set(product_ids) - prices.keys())
    if missing:
        raise ValidationError(f"Unknown product id(s): {', '.join(map(str, missing))}")

    lines = []
    for item in items:
        unit_price = prices[item['product_id']]
        line_total = (unit_price * item['quantity']).quantize(CENTS, rounding=ROUND_HALF_UP)
        lines.append((item['product_id'], item['quantity'], unit_price, line_total))
    grand_total = sum((line[3] for line in lines), Decimal('0.00'))

    with connection.transaction():
        order_id = connection.execute(
            "INSERT INTO orders (customer_name, total_price, created_by) VALUES (%s, %s, %s) RETURNING order_id",
            (customer_name, grand_total, created_by)
        ).fetchone()['order_id']

        with connection.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO order_details (order_id, product_id, quantity, unit_price, total_price) "
                "VALUES (%s, %s, %s, %s, %s)",
                [(order_id, *line) for line in lines]
            )

    return order_id
