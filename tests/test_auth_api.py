# tests/test_auth_api.py
import json

# Các test cases cho Auth API

def test_register_new_buyer_successful(client, init_database, new_user_data): # Sử dụng fixtures
    """Kiểm thử đăng ký buyer mới thành công."""
    payload = new_user_data.copy() # Tránh thay đổi fixture gốc
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)

    assert response.status_code == 201
    assert data['username'] == payload['username']
    assert data['role'] == 'buyer'
    assert 'id' in data

def test_register_new_seller_successful(client, init_database):
    """Kiểm thử đăng ký seller mới thành công."""
    payload = {'username': 'new_seller', 'password': 'password123', 'role': 'seller'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 201
    assert data['username'] == 'new_seller'
    assert data['role'] == 'seller'

def test_register_user_missing_fields(client, init_database):
    """Kiểm thử đăng ký thiếu trường username."""
    payload = {'password': 'password123', 'role': 'buyer'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 400 # Bad Request (do Marshmallow validation)
    assert 'errors' in data
    assert 'username' in data['errors'] # Hoặc thông báo lỗi cụ thể từ Marshmallow

def test_register_existing_username(client, created_buyer): # created_buyer đã tạo user 'test_buyer'
    """Kiểm thử đăng ký với username đã tồn tại."""
    payload = {'username': created_buyer.username, 'password': 'newpassword', 'role': 'buyer'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 409 # Conflict
    assert 'error' in data
    assert 'Tên người dùng đã tồn tại' in data['error']['message']

def test_register_admin_role_not_allowed(client, init_database):
    """Kiểm thử không cho phép tự đăng ký vai trò admin."""
    payload = {'username': 'wannabe_admin', 'password': 'password123', 'role': 'admin'}
    response = client.post('/auth/register',
                           data=json.dumps(payload),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 403 # Hoặc 400 tùy theo logic xử lý trong API
    # assert "Vai trò 'admin' không được phép tự đăng ký" in data['error']['message'] # Kiểm tra message cụ thể

# --- Tests for Login ---
def test_login_successful_buyer(client, created_buyer):
    """Kiểm thử đăng nhập buyer thành công."""
    response = client.post('/auth/login',
                           data=json.dumps({'username': created_buyer.username, 'password': 'buyerpass'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'access_token' in data

def test_login_successful_seller(client, created_seller):
    """Kiểm thử đăng nhập seller thành công."""
    response = client.post('/auth/login',
                           data=json.dumps({'username': created_seller.username, 'password': 'sellerpass'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 200
    assert 'access_token' in data

def test_login_non_existent_user(client, init_database):
    """Kiểm thử đăng nhập với user không tồn tại."""
    response = client.post('/auth/login',
                           data=json.dumps({'username': 'nosuchuser', 'password': 'password'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 401 # Unauthorized
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
    """Kiểm thử đăng nhập thiếu username."""
    response = client.post('/auth/login',
                           data=json.dumps({'password': 'password'}),
                           content_type='application/json')
    data = json.loads(response.data)
    assert response.status_code == 400 # Bad Request
    assert 'Thiếu tên người dùng hoặc mật khẩu' in data['error']['message'] # Hoặc lỗi từ Marshmallow nếu có schema