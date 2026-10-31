from decimal import Decimal, ROUND_HALF_UP

RANK_LIMIT = 5

# The period is the last `days` calendar days including today; the previous period is
# the same number of days right before it, used for "vs. previous period" comparisons.
_PERIOD_START = "(current_date - %(days)s::int + 1)::timestamptz"
_PREVIOUS_START = "(current_date - 2 * %(days)s::int + 1)::timestamptz"


def _with_average(totals):
    orders = totals['orders']
    average = (totals['revenue'] / orders).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if orders else Decimal('0')
    return {**totals, 'average_order_value': average}


def get_summary(connection, days):
    params = {'days': days, 'limit': RANK_LIMIT}

    totals = connection.execute(
        "SELECT "
        f"count(*) FILTER (WHERE created_at >= {_PERIOD_START}) AS orders, "
        f"COALESCE(sum(total_price) FILTER (WHERE created_at >= {_PERIOD_START}), 0) AS revenue, "
        f"count(DISTINCT lower(customer_name)) FILTER (WHERE created_at >= {_PERIOD_START}) AS customers, "
        f"count(*) FILTER (WHERE created_at < {_PERIOD_START}) AS previous_orders, "
        f"COALESCE(sum(total_price) FILTER (WHERE created_at < {_PERIOD_START}), 0) AS previous_revenue, "
        f"count(DISTINCT lower(customer_name)) FILTER (WHERE created_at < {_PERIOD_START}) AS previous_customers "
        f"FROM orders WHERE created_at >= {_PREVIOUS_START}",
        params
    ).fetchone()

    # One row per day, including days without sales
    daily_sales = connection.execute(
        "SELECT day::date AS date, COALESCE(sum(o.total_price), 0) AS revenue, count(o.order_id) AS orders "
        f"FROM generate_series({_PERIOD_START}, current_date, interval '1 day') AS day "
        "LEFT JOIN orders o ON o.created_at >= day AND o.created_at < day + interval '1 day' "
        "GROUP BY day ORDER BY day",
        params
    ).fetchall()

    top_products = connection.execute(
        "SELECT p.product_id AS id, p.name, p.icon, u.uom_name, sum(d.quantity) AS quantity, sum(d.total_price) AS revenue "
        "FROM order_details d "
        "JOIN orders o ON o.order_id = d.order_id "
        "JOIN products p ON p.product_id = d.product_id "
        "JOIN uom u ON u.uom_id = p.uom_id "
        f"WHERE o.created_at >= {_PERIOD_START} "
        "GROUP BY p.product_id, p.name, p.icon, u.uom_name "
        "ORDER BY revenue DESC, p.name LIMIT %(limit)s",
        params
    ).fetchall()

    top_customers = connection.execute(
        "SELECT min(customer_name) AS name, count(*) AS orders, sum(total_price) AS revenue, max(created_at) AS last_order_at "
        f"FROM orders WHERE created_at >= {_PERIOD_START} "
        "GROUP BY lower(customer_name) "
        "ORDER BY revenue DESC, name LIMIT %(limit)s",
        params
    ).fetchall()

    # Orders made before user accounts existed have no cashier and are left out
    sales_by_staff = connection.execute(
        "SELECT u.user_id AS id, u.full_name AS name, u.role, count(*) AS orders, sum(o.total_price) AS revenue "
        "FROM orders o JOIN users u ON u.user_id = o.created_by "
        f"WHERE o.created_at >= {_PERIOD_START} "
        "GROUP BY u.user_id, u.full_name, u.role "
        "ORDER BY revenue DESC",
        params
    ).fetchall()

    # weekday: 1 = Monday ... 7 = Sunday, hour: 0-23 (in the database's time zone)
    busiest_hours = connection.execute(
        "SELECT EXTRACT(ISODOW FROM created_at)::int AS weekday, EXTRACT(HOUR FROM created_at)::int AS hour, count(*) AS orders "
        f"FROM orders WHERE created_at >= {_PERIOD_START} "
        "GROUP BY 1, 2 ORDER BY 1, 2",
        params
    ).fetchall()

    product_count = connection.execute("SELECT count(*) AS count FROM products").fetchone()['count']

    return {
        'days': days,
        'current': _with_average({k: totals[k] for k in ('orders', 'revenue', 'customers')}),
        'previous': _with_average({k: totals[f'previous_{k}'] for k in ('orders', 'revenue', 'customers')}),
        'product_count': product_count,
        'daily_sales': daily_sales,
        'top_products': top_products,
        'top_customers': top_customers,
        'sales_by_staff': sales_by_staff,
        'busiest_hours': busiest_hours,
    }
