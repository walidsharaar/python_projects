from decimal import Decimal

import pytest

from app import validation
from app.errors import ValidationError


def test_parse_product_accepts_string_values():
    product = validation.parse_product({'name': ' Banana ', 'uom_id': '1', 'price_per_unit': '0.45'})
    assert product == {'name': 'Banana', 'uom_id': 1, 'price_per_unit': Decimal('0.45'), 'icon': None}
    assert validation.parse_product({'name': 'Banana', 'uom_id': 1, 'price_per_unit': 1, 'icon': ' 🍌 '})['icon'] == '🍌'


@pytest.mark.parametrize('payload', [
    {'uom_id': 1, 'price_per_unit': 1},
    {'name': '', 'uom_id': 1, 'price_per_unit': 1},
    {'name': 'x' * 256, 'uom_id': 1, 'price_per_unit': 1},
    {'name': 'Banana', 'uom_id': 'abc', 'price_per_unit': 1},
    {'name': 'Banana', 'uom_id': 0, 'price_per_unit': 1},
    {'name': 'Banana', 'uom_id': True, 'price_per_unit': 1},
    {'name': 'Banana', 'uom_id': 1, 'price_per_unit': -1},
    {'name': 'Banana', 'uom_id': 1, 'price_per_unit': 'NaN'},
    {'name': 'Banana', 'uom_id': 1, 'price_per_unit': '1.234'},
    {'name': 'Banana', 'uom_id': 1, 'price_per_unit': '100000000'},
    ['not', 'an', 'object'],
    None,
])
def test_parse_product_rejects_bad_input(payload):
    with pytest.raises(ValidationError):
        validation.parse_product(payload)


def test_parse_order_ignores_client_prices():
    customer_name, items = validation.parse_order({
        'customer_name': 'Dana',
        'total': 0.01,
        'items': [{'product_id': '2', 'quantity': '1.5', 'unit_price': 0.01}],
    })
    assert customer_name == 'Dana'
    assert items == [{'product_id': 2, 'quantity': Decimal('1.5')}]


@pytest.mark.parametrize('items', [[], 'x', [{'product_id': 1}], [{'product_id': 1, 'quantity': 0}], ['x']])
def test_parse_order_rejects_bad_items(items):
    with pytest.raises(ValidationError):
        validation.parse_order({'customer_name': 'Dana', 'items': items})


def test_parse_order_query_defaults_and_limits():
    assert validation.parse_order_query({}) == {'limit': 50, 'offset': 0, 'search': None}
    assert validation.parse_order_query({'q': '  Ali ', 'limit': '5'})['search'] == 'Ali'
    for args in ({'limit': '0'}, {'limit': '501'}, {'offset': '-1'}, {'limit': 'abc'}, {'q': 'x' * 101}):
        with pytest.raises(ValidationError):
            validation.parse_order_query(args)
