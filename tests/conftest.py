# tests/conftest.py
import pytest
import json
from app import create_app # Đảm bảo đường dẫn import này đúng với cấu trúc dự án của bạn
from app.extensions import db
from app.models.user import User
from app.models.phone import Phone
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem
from werkzeug.security import generate_password_hash

TEST_CONFIG_NAME = 'test' # Sử dụng cấu hình 'test' cho CSDL riêng

@pytest.fixture(scope='session') # Chạy 1 lần cho toàn bộ session test
def app():
    """Tạo và cấu hình một app instance mới cho mỗi test session."""
    flask_app = create_app(config_name=TEST_CONFIG_NAME)
    yield flask_app

@pytest.fixture(scope='session')
def client(app):
    """Một test client cho app."""
    return app.test_client()

@pytest.fixture(scope='session')
def runner(app):
    """Một test runner cho các lệnh CLI của Flask (nếu cần)."""
    return app.test_cli_runner()

@pytest.fixture(scope='function') # Chạy cho mỗi hàm test, đảm bảo CSDL sạch
def init_database(app):
    """Khởi tạo CSDL sạch cho mỗi test function."""
    with app.app_context():
        db.create_all()
        yield db # Cung cấp db session cho các test nếu cần
        db.session.remove()
        db.drop_all()

# --- Fixtures để tạo dữ liệu mẫu cho tests ---

@pytest.fixture(scope='function')
def new_user_data(init_database): # Phụ thuộc init_database để có CSDL
    """Trả về dữ liệu cho một user mới."""
    return {
        'username': 'test_new_user',
        'password': 'password123',
        'role': 'buyer'
    }

@pytest.fixture(scope='function')
def created_admin(init_database):
    user = User(username='test_admin', password_hash=generate_password_hash('adminpass'), role='admin')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def created_seller(init_database):
    user = User(username='test_seller', password_hash=generate_password_hash('sellerpass'), role='seller')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def created_buyer(init_database):
    user = User(username='test_buyer', password_hash=generate_password_hash('buyerpass'), role='buyer')
    db.session.add(user)
    db.session.commit()
    return user

# --- Fixtures để lấy token ---
def get_auth_token(client, username, password):
    """Helper function để đăng nhập và lấy token."""
    response = client.post('/auth/login',
                           data=json.dumps({'username': username, 'password': password}),
                           content_type='application/json')
    if response.status_code == 200:
        return json.loads(response.data)['access_token']
    return None

@pytest.fixture(scope='function')
def admin_token(client, created_admin):
    return get_auth_token(client, created_admin.username, 'adminpass')

@pytest.fixture(scope='function')
def seller_token(client, created_seller):
    return get_auth_token(client, created_seller.username, 'sellerpass')

@pytest.fixture(scope='function')
def buyer_token(client, created_buyer):
    return get_auth_token(client, created_buyer.username, 'buyerpass')


# --- Fixtures cho Phone ---
@pytest.fixture(scope='function')
def new_phone_data():
    return {
        "model_name": "Test Phone One",
        "manufacturer": "TestBrand",
        "price": 1000000,
        "stock_quantity": 10,
        "specifications": "A test phone"
    }

@pytest.fixture(scope='function')
def created_phone(init_database, new_phone_data, created_seller):
    phone = Phone(**new_phone_data, user_id=created_seller.id)
    db.session.add(phone)
    db.session.commit()
    return phone

# --- Fixtures cho Cart (nếu cần test các thao tác phức tạp hơn) ---
@pytest.fixture(scope='function')
def buyer_cart_with_item(init_database, created_buyer, created_phone):
    cart = Cart.query.filter_by(user_id=created_buyer.id).first()
    if not cart:
        cart = Cart(user_id=created_buyer.id)
        db.session.add(cart)
        db.session.commit() # Commit để cart có id

    if created_phone.stock_quantity > 0:
        cart_item = CartItem(cart_id=cart.id, phone_id=created_phone.id, quantity=1)
        db.session.add(cart_item)
        db.session.commit()
    return {'cart': cart, 'item': cart_item if 'cart_item' in locals() else None, 'phone_added': created_phone}


# --- Fixtures cho Order (nếu cần) ---
@pytest.fixture(scope='function')
def created_order(init_database, created_buyer, created_phone):
    if created_phone.stock_quantity < 1:
        pytest.skip("Không đủ tồn kho để tạo đơn hàng mẫu cho test này")

    order = Order(
        user_id=created_buyer.id,
        total_amount=created_phone.price * 1,
        status='pending',
        shipping_address='123 Test St'
    )
    db.session.add(order)
    db.session.flush() # Để order có ID trước khi tạo OrderItem

    order_item = OrderItem(
        order_id=order.id,
        phone_id=created_phone.id,
        quantity=1,
        price_at_purchase=created_phone.price
    )
    db.session.add(order_item)

    # Giảm tồn kho (API của bạn làm điều này, nhưng fixture cũng nên mô phỏng nếu test đơn vị)
    # created_phone.stock_quantity -= 1
    # db.session.add(created_phone)

    db.session.commit()
    return order