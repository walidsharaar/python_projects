import pytest
from conftest import ADMIN, CASHIER, sign_in

API = '/api/v1'


def login(client, username, password):
    return client.post(f'{API}/auth/login', json={'username': username, 'password': password})


def test_everything_requires_sign_in(anon):
    for method, path in [('get', '/products'), ('get', '/orders'), ('post', '/orders'), ('get', '/uoms'),
                         ('get', '/stats/summary'), ('get', '/users'), ('get', '/auth/me')]:
        response = getattr(anon, method)(f'{API}{path}', json={})
        assert response.status_code == 401, path
        assert response.content_type == 'application/problem+json'
    # Public: the UI shell, health check and docs
    assert anon.get('/').status_code == 200
    assert anon.get('/health').status_code == 200


def test_login_me_logout(anon):
    response = login(anon, 'ADMIN ', ADMIN['password'])  # usernames are case-insensitive
    assert response.status_code == 200
    profile = response.get_json()
    assert (profile['username'], profile['role'], profile['full_name']) == ('admin', 'admin', 'Ada Admin')
    assert 'password_hash' not in profile and profile['last_login_at']

    cookie = response.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Lax' in cookie

    assert anon.get(f'{API}/auth/me').get_json()['username'] == 'admin'
    assert anon.post(f'{API}/auth/logout').status_code == 204
    assert anon.get(f'{API}/auth/me').status_code == 401


def test_wrong_credentials_get_the_same_answer(anon):
    wrong_password = login(anon, 'admin', 'nope-nope-nope')
    unknown_user = login(anon, 'nobody', 'nope-nope-nope')
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert wrong_password.get_json()['detail'] == unknown_user.get_json()['detail']
    assert login(anon, '', '').status_code == 400


def test_account_locks_after_five_failed_attempts(anon, client):
    for _ in range(5):
        assert login(anon, 'cashier', 'wrong-password').status_code == 401
    locked = login(anon, 'cashier', CASHIER['password'])
    assert locked.status_code == 429
    assert 'Try again in' in locked.get_json()['detail']

    # An admin resetting the password lifts the lock
    cashier_id = next(u['id'] for u in client.get(f'{API}/users').get_json()['items'] if u['username'] == 'cashier')
    client.put(f'{API}/users/{cashier_id}', json={'full_name': 'Carl Cashier', 'role': 'cashier', 'is_active': True,
                                                   'password': 'brand-new-pass'})
    assert login(anon, 'cashier', 'brand-new-pass').status_code == 200


def test_cashier_permissions(cashier):
    assert cashier.get(f'{API}/products').status_code == 200
    assert cashier.get(f'{API}/orders').status_code == 200
    product_id = cashier.get(f'{API}/products').get_json()['items'][0]['id']

    order = cashier.post(f'{API}/orders', json={'customer_name': 'Eve', 'items': [{'product_id': product_id, 'quantity': 1}]})
    assert order.status_code == 201
    assert order.get_json()['created_by_name'] == 'Carl Cashier'

    for method, path, body in [('post', '/products', {'name': 'X', 'uom_id': 1, 'price_per_unit': 1}),
                               ('put', f'/products/{product_id}', {'name': 'X', 'uom_id': 1, 'price_per_unit': 1}),
                               ('delete', f'/products/{product_id}', None),
                               ('get', '/stats/summary', None),
                               ('get', '/users', None),
                               ('post', '/users', {'username': 'x'})]:
        response = getattr(cashier, method)(f'{API}{path}', json=body)
        assert response.status_code == 403, path


def test_user_management(app, client):
    created = client.post(f'{API}/users', json={'username': 'Nina.K', 'full_name': 'Nina K', 'role': 'cashier',
                                                 'password': 'nina-pass-123'})
    assert created.status_code == 201
    nina = created.get_json()
    assert (nina['username'], nina['role'], nina['is_active']) == ('nina.k', 'cashier', True)
    assert created.headers['Location'] == f"{API}/users/{nina['id']}"

    users = client.get(f'{API}/users').get_json()['items']
    assert {u['username'] for u in users} == {'admin', 'cashier', 'nina.k'}
    assert all('password_hash' not in u for u in users)

    assert client.post(f'{API}/users', json={'username': 'nina.k', 'full_name': 'N', 'role': 'cashier', 'password': 'x' * 8}).status_code == 409
    assert client.post(f'{API}/users', json={'username': 'a b', 'full_name': 'N', 'role': 'cashier', 'password': 'x' * 8}).status_code == 400
    assert client.post(f'{API}/users', json={'username': 'short', 'full_name': 'N', 'role': 'cashier', 'password': 'x' * 7}).status_code == 400
    assert client.post(f'{API}/users', json={'username': 'boss', 'full_name': 'N', 'role': 'owner', 'password': 'x' * 8}).status_code == 400

    # Deactivating ends Nina's open session immediately and blocks new sign-ins
    nina_client = sign_in(app.test_client(), {'username': 'nina.k', 'password': 'nina-pass-123'})
    updated = client.put(f"{API}/users/{nina['id']}", json={'full_name': 'Nina Kowalski', 'role': 'cashier', 'is_active': False})
    assert updated.status_code == 200 and updated.get_json()['full_name'] == 'Nina Kowalski'
    assert nina_client.get(f'{API}/orders').status_code == 401
    assert login(app.test_client(), 'nina.k', 'nina-pass-123').status_code == 403

    assert client.put(f'{API}/users/9999', json={'full_name': 'X', 'role': 'cashier', 'is_active': True}).status_code == 404


def test_admin_cannot_lock_themselves_out(client):
    me = client.get(f'{API}/auth/me').get_json()
    for change in ({'role': 'cashier', 'is_active': True}, {'role': 'admin', 'is_active': False}):
        response = client.put(f"{API}/users/{me['id']}", json={'full_name': me['full_name'], **change})
        assert response.status_code == 409
    assert client.get(f'{API}/users').status_code == 200


def test_password_change_signs_out_other_sessions(app, cashier):
    other_device = sign_in(app.test_client(), CASHIER)

    wrong = cashier.put(f'{API}/auth/password', json={'current_password': 'nope', 'new_password': 'new-pass-456'})
    assert wrong.status_code == 400
    assert cashier.put(f'{API}/auth/password', json={'current_password': CASHIER['password'], 'new_password': 'short'}).status_code == 400

    changed = cashier.put(f'{API}/auth/password', json={'current_password': CASHIER['password'], 'new_password': 'new-pass-456'})
    assert changed.status_code == 204
    assert cashier.get(f'{API}/auth/me').status_code == 200          # this session continues
    assert other_device.get(f'{API}/auth/me').status_code == 401     # the other one ends

    assert login(app.test_client(), 'cashier', CASHIER['password']).status_code == 401
    assert login(app.test_client(), 'cashier', 'new-pass-456').status_code == 200


@pytest.mark.parametrize('payload', [{'username': 'admin'}, ['admin'], {'username': 'admin', 'password': 'x' * 200}])
def test_login_rejects_malformed_input(anon, payload):
    assert anon.post(f'{API}/auth/login', json=payload).status_code == 400
