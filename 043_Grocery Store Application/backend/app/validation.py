import re
from decimal import Decimal, InvalidOperation

from .errors import ValidationError

ROLES = ('admin', 'cashier')
USERNAME_PATTERN = re.compile(r'^[a-z0-9._-]{3,50}$')
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_ICON_LENGTH = 16
MAX_NAME_LENGTH = 255
MAX_SEARCH_LENGTH = 100
MAX_ORDER_ITEMS = 100
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
# Largest value that fits NUMERIC(10, 2)
MAX_AMOUNT = Decimal('99999999.99')


def _require(payload, field):
    if not isinstance(payload, dict):
        raise ValidationError("Request body must be a JSON object")
    if field not in payload or payload[field] in (None, ''):
        raise ValidationError(f"'{field}' is required")
    return payload[field]


def parse_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field}' must be a non-empty string")
    value = value.strip()
    if len(value) > MAX_NAME_LENGTH:
        raise ValidationError(f"'{field}' must be at most {MAX_NAME_LENGTH} characters")
    return value


def parse_id(value, field):
    # Accept "3" as well as 3: ids often come from <select> values or URLs
    if isinstance(value, bool):
        raise ValidationError(f"'{field}' must be a positive integer")
    try:
        parsed = int(str(value).strip())
    except ValueError:
        raise ValidationError(f"'{field}' must be a positive integer") from None
    if parsed <= 0:
        raise ValidationError(f"'{field}' must be a positive integer")
    return parsed


def parse_amount(value, field, allow_zero=False):
    if isinstance(value, bool):
        raise ValidationError(f"'{field}' must be a number")
    try:
        parsed = Decimal(str(value).strip())
    except InvalidOperation:
        raise ValidationError(f"'{field}' must be a number") from None
    if not parsed.is_finite():
        raise ValidationError(f"'{field}' must be a number")
    if parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValidationError(f"'{field}' must be greater than {'or equal to ' if allow_zero else ''}0")
    if parsed > MAX_AMOUNT:
        raise ValidationError(f"'{field}' is too large")
    if parsed.as_tuple().exponent < -2:
        raise ValidationError(f"'{field}' must have at most 2 decimal places")
    return parsed


def _parse_int_arg(args, name, default, minimum, maximum):
    raw = args.get(name, default)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValidationError(f"'{name}' must be an integer") from None
    if not minimum <= value <= maximum:
        raise ValidationError(f"'{name}' must be between {minimum} and {maximum}")
    return value


def parse_icon(value):
    """Optional emoji shown for a product; empty means "use the name's initials"."""
    if value is None or value == '':
        return None
    if not isinstance(value, str) or len(value.strip()) > MAX_ICON_LENGTH:
        raise ValidationError(f"'icon' must be a short text (at most {MAX_ICON_LENGTH} characters)")
    return value.strip() or None


def parse_product(payload):
    product = {
        'name': parse_text(_require(payload, 'name'), 'name'),
        'uom_id': parse_id(_require(payload, 'uom_id'), 'uom_id'),
        'price_per_unit': parse_amount(_require(payload, 'price_per_unit'), 'price_per_unit', allow_zero=True),
    }
    product['icon'] = parse_icon(payload.get('icon'))
    return product


# --- Users and authentication ---

def parse_username(value):
    if not isinstance(value, str) or not USERNAME_PATTERN.match(value.strip().lower()):
        raise ValidationError("'username' must be 3-50 characters: letters, digits, '.', '_' or '-'")
    return value.strip().lower()


def parse_password(value, field='password'):
    if not isinstance(value, str) or not MIN_PASSWORD_LENGTH <= len(value) <= MAX_PASSWORD_LENGTH:
        raise ValidationError(f"'{field}' must be {MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters long")
    return value


def parse_role(value):
    if value not in ROLES:
        raise ValidationError(f"'role' must be one of: {', '.join(ROLES)}")
    return value


def parse_login(payload):
    username = _require(payload, 'username')
    password = _require(payload, 'password')
    if not isinstance(username, str) or not isinstance(password, str) or len(password) > MAX_PASSWORD_LENGTH:
        raise ValidationError("Enter your username and password")
    return username.strip().lower(), password


def parse_new_user(payload):
    return {
        'username': parse_username(_require(payload, 'username')),
        'full_name': parse_text(_require(payload, 'full_name'), 'full_name'),
        'role': parse_role(_require(payload, 'role')),
        'password': parse_password(_require(payload, 'password')),
    }


def parse_user_update(payload):
    is_active = _require(payload, 'is_active') if isinstance(payload, dict) and 'is_active' in payload else True
    if not isinstance(is_active, bool):
        raise ValidationError("'is_active' must be true or false")
    password = payload.get('password') if isinstance(payload, dict) else None
    return {
        'full_name': parse_text(_require(payload, 'full_name'), 'full_name'),
        'role': parse_role(_require(payload, 'role')),
        'is_active': is_active,
        # Optional: only set when an admin resets the password
        'password': parse_password(password) if password else None,
    }


def parse_password_change(payload):
    current = _require(payload, 'current_password')
    if not isinstance(current, str):
        raise ValidationError("'current_password' is required")
    return current, parse_password(_require(payload, 'new_password'), 'new_password')


def parse_order(payload):
    customer_name = parse_text(_require(payload, 'customer_name'), 'customer_name')

    raw_items = _require(payload, 'items')
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("'items' must be a non-empty list")
    if len(raw_items) > MAX_ORDER_ITEMS:
        raise ValidationError(f"An order can have at most {MAX_ORDER_ITEMS} items")

    # Prices and totals are never taken from the client: they come from the database
    items = []
    for index, item in enumerate(raw_items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            raise ValidationError(f"'{prefix}' must be an object")
        items.append({
            'product_id': parse_id(_require(item, 'product_id'), f"{prefix}.product_id"),
            'quantity': parse_amount(_require(item, 'quantity'), f"{prefix}.quantity"),
        })

    return customer_name, items


def parse_order_query(args):
    search = args.get('q', '').strip()
    if len(search) > MAX_SEARCH_LENGTH:
        raise ValidationError(f"'q' must be at most {MAX_SEARCH_LENGTH} characters")
    return {
        'limit': _parse_int_arg(args, 'limit', DEFAULT_PAGE_SIZE, 1, MAX_PAGE_SIZE),
        'offset': _parse_int_arg(args, 'offset', 0, 0, 10_000_000),
        'search': search or None,
    }


def parse_days(args):
    return _parse_int_arg(args, 'days', 30, 1, 366)
