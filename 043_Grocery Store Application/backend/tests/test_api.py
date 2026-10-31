import pytest

API = '/api/v1'
SEED_ORDER_COUNT = 100  # 10 fixed + 90 generated in seed.sql


def product_by_name(client, name):
    return next(p for p in client.get(f'{API}/products').get_json()['items'] if p['name'] == name)


def assert_problem(response, status):
    assert response.status_code == status
    assert response.content_type == 'application/problem+json'
    body = response.get_json()
    assert body['status'] == status and body['title'] and body['detail']


def test_health(client):
    assert client.get('/health').get_json() == {'status': 'ok'}


def test_ui_and_docs_are_served(anon):
    client = anon
    assert client.get('/').status_code == 200
    assert client.get('/api/docs').status_code == 200
    spec = client.get(f'{API}/openapi.yaml')
    assert spec.status_code == 200 and b'openapi: 3.1.0' in spec.data


def test_openapi_documents_every_api_route(app):
    spec = app.test_client().get(f'{API}/openapi.yaml').get_data(as_text=True)
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith(API) and not rule.rule.endswith('openapi.yaml'):
            path = (rule.rule[len(API):].replace('<int:product_id>', '{productId}')
                    .replace('<int:order_id>', '{orderId}').replace('<int:user_id>', '{userId}'))
            assert f'  {path}:' in spec, f"{rule.rule} is missing from openapi.yaml"


def test_list_uoms(client):
    names = [u['name'] for u in client.get(f'{API}/uoms').get_json()['items']]
    assert names == ['kg', 'gram', 'piece', 'packet', 'litre']


def test_product_crud(client):
    created = client.post(f'{API}/products', json={'name': 'Kiwi', 'icon': '🥝', 'uom_id': 3, 'price_per_unit': '0.45'})
    assert created.status_code == 201
    product = created.get_json()
    assert (product['name'], product['icon'], product['uom_name'], product['price_per_unit']) == ('Kiwi', '🥝', 'piece', 0.45)
    assert created.headers['Location'] == f"{API}/products/{product['id']}"

    assert client.get(f"{API}/products/{product['id']}").get_json() == product

    updated = client.put(f"{API}/products/{product['id']}", json={'name': 'Gold Kiwi', 'uom_id': 1, 'price_per_unit': 4})
    assert updated.status_code == 200
    assert (updated.get_json()['name'], updated.get_json()['uom_name'], updated.get_json()['icon']) == ('Gold Kiwi', 'kg', None)

    deleted = client.delete(f"{API}/products/{product['id']}")
    assert deleted.status_code == 204 and deleted.data == b''
    assert_problem(client.get(f"{API}/products/{product['id']}"), 404)
    assert_problem(client.delete(f"{API}/products/{product['id']}"), 404)


def test_product_errors(client):
    assert_problem(client.post(f'{API}/products', json={'name': 'Tomato', 'uom_id': 1, 'price_per_unit': 1}), 409)
    assert_problem(client.post(f'{API}/products', json={'name': 'Fig', 'uom_id': 999, 'price_per_unit': 1}), 400)
    assert_problem(client.post(f'{API}/products', json={'name': 'Fig'}), 400)
    assert_problem(client.post(f'{API}/products', json={'name': 'Fig', 'uom_id': 1, 'price_per_unit': 1, 'icon': 'x' * 17}), 400)
    assert_problem(client.post(f'{API}/products', data='name=Fig'), 415)
    assert_problem(client.post(f'{API}/products', data='{bad json', content_type='application/json'), 400)
    assert_problem(client.put(f'{API}/products/9999', json={'name': 'Fig', 'uom_id': 1, 'price_per_unit': 1}), 404)
    assert_problem(client.patch(f'{API}/products/1', json={}), 405)
    assert_problem(client.get(f'{API}/nothing-here'), 404)
    # The pooled connection must still work after the failed transactions above
    assert client.get('/health').status_code == 200


def test_update_product_keeps_past_order_prices(client):
    tomato = product_by_name(client, 'Tomato')
    response = client.put(f"{API}/products/{tomato['id']}", json={'name': 'Tomato', 'uom_id': 1, 'price_per_unit': 9.99})
    assert response.status_code == 200

    alice = client.get(f'{API}/orders?q=Alice').get_json()['items'][0]
    line = next(i for i in alice['items'] if i['product_name'] == 'Tomato')
    assert (line['unit_price'], line['total'], alice['total']) == (1.5, 3.0, 5.2)


def test_cannot_delete_product_used_in_orders(client):
    assert_problem(client.delete(f"{API}/products/{product_by_name(client, 'Tomato')['id']}"), 409)


def test_create_order_uses_database_prices(client):
    tomato, rice = product_by_name(client, 'Tomato'), product_by_name(client, 'Rice')
    response = client.post(f'{API}/orders', json={
        'customer_name': 'Dana',
        'total': 0.01,
        'items': [
            {'product_id': tomato['id'], 'quantity': 3, 'unit_price': 0.01},
            {'product_id': rice['id'], 'quantity': '0.75'},
        ],
    })
    assert response.status_code == 201
    order = response.get_json()
    assert response.headers['Location'] == f"{API}/orders/{order['id']}"
    # 3 * 1.50 + 0.75 * 3.50 (2.625 rounds to 2.63)
    assert order['total'] == 7.13
    assert [(i['product_name'], i['unit_price'], i['total']) for i in order['items']] == [('Tomato', 1.5, 4.5), ('Rice', 3.5, 2.63)]
    assert order['items'][0]['product_icon'] == '🍅'
    assert order['created_by_name'] == 'Ada Admin'
    assert client.get(f"{API}/orders/{order['id']}").get_json() == order


def test_create_order_errors(client):
    assert_problem(client.post(f'{API}/orders', json={'customer_name': 'Dana', 'items': [{'product_id': 9999, 'quantity': 1}]}), 400)
    assert_problem(client.post(f'{API}/orders', json={'customer_name': 'Dana', 'items': []}), 400)
    assert_problem(client.get(f'{API}/orders/9999'), 404)


def test_list_orders_pagination_and_search(client):
    page = client.get(f'{API}/orders?limit=3').get_json()
    assert (page['total'], page['limit'], page['offset'], len(page['items'])) == (SEED_ORDER_COUNT, 3, 0, 3)
    assert page['items'][0]['customer_name'] == 'Alice Johnson'  # newest first

    second = client.get(f'{API}/orders?limit=3&offset=3').get_json()
    assert {o['id'] for o in page['items']}.isdisjoint(o['id'] for o in second['items'])

    by_name = client.get(f'{API}/orders?q=ali').get_json()
    assert {o['customer_name'] for o in by_name['items']} == {'Alice Johnson', 'Hassan Ali'}

    order_id = page['items'][0]['id']
    assert [o['id'] for o in client.get(f'{API}/orders?q=%23{order_id}').get_json()['items']] == [order_id]
    # LIKE wildcards are matched literally
    assert client.get(f'{API}/orders?q=%25').get_json()['total'] == 0

    assert_problem(client.get(f'{API}/orders?limit=0'), 400)


def test_stats_summary(client):
    tomato = product_by_name(client, 'Tomato')
    client.post(f'{API}/orders', json={'customer_name': 'Dana', 'items': [{'product_id': tomato['id'], 'quantity': 2}]})

    stats = client.get(f'{API}/stats/summary?days=7').get_json()
    current, daily = stats['current'], stats['daily_sales']

    assert stats['days'] == 7 and len(daily) == 7
    assert [d['date'] for d in daily] == sorted(d['date'] for d in daily)
    assert current['orders'] == sum(d['orders'] for d in daily)
    assert current['revenue'] == pytest.approx(sum(d['revenue'] for d in daily))
    assert current['average_order_value'] == pytest.approx(round(current['revenue'] / current['orders'], 2))
    assert set(stats['previous']) == {'orders', 'revenue', 'customers', 'average_order_value'}
    assert stats['product_count'] == 13

    for ranking in ('top_products', 'top_customers'):
        assert 0 < len(stats[ranking]) <= 5
        assert [r['revenue'] for r in stats[ranking]] == sorted((r['revenue'] for r in stats[ranking]), reverse=True)
    assert stats['top_products'][0]['icon']

    # Only orders made by a signed-in user count per staff member (seeded ones have none)
    assert [(s['name'], s['orders'], s['revenue']) for s in stats['sales_by_staff']] == [('Ada Admin', 1, 3.0)]

    hours = stats['busiest_hours']
    assert all(1 <= h['weekday'] <= 7 and 0 <= h['hour'] <= 23 for h in hours)
    assert sum(h['orders'] for h in hours) == current['orders']

    # A year covers every order
    assert client.get(f'{API}/stats/summary?days=366').get_json()['current']['orders'] == SEED_ORDER_COUNT + 1
    assert_problem(client.get(f'{API}/stats/summary?days=0'), 400)
