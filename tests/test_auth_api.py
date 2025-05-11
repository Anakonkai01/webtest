# tests/test_auth_api.py
import json

def test_register_new_buyer_successful(client, init_database, new_user_data):
    payload = new_user_data.copy()
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)

    assert response.status_code == 201
    assert data['username'] == payload['username']
    assert data['role'] == 'buyer'
    assert 'id' in data

def test_register_new_seller_successful(client, init_database):
    payload = {'username': 'new_seller', 'password': 'password123', 'role': 'seller'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 201
    assert data['username'] == 'new_seller'
    assert data['role'] == 'seller'

def test_register_user_missing_fields(client, init_database):
    payload = {'password': 'password123', 'role': 'buyer'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 400
    assert 'errors' in data
    assert 'username' in data['errors']

def test_register_existing_username(client, created_buyer):
    payload = {'username': created_buyer.username, 'password': 'newpassword', 'role': 'buyer'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 409
    assert 'error' in data
    assert 'Tên người dùng đã tồn tại' in data['error']['message']

def test_register_admin_role_not_allowed(client, init_database):
    payload = {'username': 'wannabe_admin', 'password': 'password123', 'role': 'admin'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 403

def test_login_successful_buyer(client, created_buyer):
    response = client.post('/auth/login',
                           data=json.dumps({'username': created_buyer.username, 'password': 'buyerpass'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'access_token' in data

def test_login_successful_seller(client, created_seller):
    response = client.post('/auth/login',
                           data=json.dumps({'username': created_seller.username, 'password': 'sellerpass'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'access_token' in data

def test_login_non_existent_user(client, init_database):
    response = client.post('/auth/login',
                           data=json.dumps({'username': 'nosuchuser', 'password': 'password'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 401
    assert 'Sai tên người dùng hoặc mật khẩu' in data['error']['message']

def test_login_wrong_password(client, created_buyer):
    """Kiểm thử đăng nhập với mật khẩu sai."""
    response = client.post('/auth/login',
                           data=json.dumps({'username': created_buyer.username, 'password': 'wrongpassword'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 401
    assert 'Sai tên người dùng hoặc mật khẩu' in data['error']['message']

def test_login_missing_username(client, init_database):
    response = client.post('/auth/login',
                           data=json.dumps({'password': 'password'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 400
    assert 'Thiếu tên người dùng hoặc mật khẩu' in data['error']['message']