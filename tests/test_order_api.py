# tests/test_order_api.py
import json
import pytest
from app.models.order import Order, OrderItem, ALLOWED_ORDER_STATUSES
from app.models.phone import Phone
from app.extensions import db

# === Test Cases for Order API ===

# --- POST /orders ---
def test_create_order_success(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử tạo đơn hàng thành công từ giỏ hàng có item."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    initial_phone_stock = buyer_cart_with_item['phone_added'].stock_quantity
    cart_item_quantity = buyer_cart_with_item['item'].quantity

    payload = {'shipping_address': '123 Test Order St, Testville'}
    response = client.post('/orders', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 201
    assert data['user']['id'] == buyer_cart_with_item['cart'].user_id
    assert data['shipping_address'] == payload['shipping_address']
    assert data['status'] == 'pending'
    assert len(data['items']) == 1
    assert data['items'][0]['phone']['id'] == buyer_cart_with_item['phone_added'].id
    assert data['items'][0]['quantity'] == cart_item_quantity

    # Kiểm tra giỏ hàng đã được làm trống
    cart_response = client.get('/cart', headers=headers)
    cart_data = json.loads(cart_response.data)
    assert len(cart_data['items']) == 0

    # Kiểm tra tồn kho sản phẩm đã giảm
    phone_in_db = Phone.query.get(buyer_cart_with_item['phone_added'].id)
    assert phone_in_db.stock_quantity == initial_phone_stock - cart_item_quantity

def test_create_order_empty_cart(client, buyer_token, created_buyer): # Giỏ hàng của created_buyer rỗng
    """Kiểm thử tạo đơn hàng với giỏ hàng trống."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'shipping_address': '456 Empty Cart St'}
    response = client.post('/orders', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 400
    assert "Giỏ hàng trống. Không thể tạo đơn hàng" in data['error']['message']

def test_create_order_missing_shipping_address(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử tạo đơn hàng thiếu địa chỉ giao hàng."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {} # Thiếu shipping_address
    response = client.post('/orders', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400 # Marshmallow validation
    assert 'errors' in data and 'shipping_address' in data['errors']

def test_create_order_insufficient_stock_at_checkout(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử trường hợp tồn kho không đủ tại thời điểm checkout (ví dụ: người khác mua mất)."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    phone_to_update = buyer_cart_with_item['phone_added']
    # Giảm tồn kho của sản phẩm trong giỏ xuống 0 trong DB trước khi đặt hàng
    original_stock = phone_to_update.stock_quantity
    phone_to_update.stock_quantity = 0
    db.session.add(phone_to_update)
    db.session.commit()

    payload = {'shipping_address': '789 Low Stock St'}
    response = client.post('/orders', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 400 # Lỗi do logic kiểm tra tồn kho trong route
    assert "Không đủ tồn kho cho" in data['error']['message']

    # Khôi phục tồn kho để không ảnh hưởng test khác (nếu cần, nhưng init_database sẽ drop_all)
    phone_to_update.stock_quantity = original_stock
    db.session.add(phone_to_update)
    db.session.commit()


# --- GET /orders ---
def test_get_orders_as_buyer(client, buyer_token, created_order):
    """Kiểm thử buyer lấy danh sách đơn hàng của mình."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.get('/orders', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['data']) >= 1
    assert any(order['id'] == created_order.id for order in data['data'])
    for order_data in data['data']:
        assert order_data['user']['id'] == created_order.user_id # Chỉ đơn của buyer này

def test_get_orders_as_seller(client, seller_token, created_order, created_seller):
    """
    Kiểm thử seller lấy danh sách đơn hàng chứa sản phẩm của mình.
    Fixture `created_order` có thể không chứa sản phẩm của `created_seller` này.
    Cần một fixture tốt hơn hoặc tạo order chứa SP của seller này.
    """
    # Tạo một phone bởi seller này
    phone_by_seller = Phone(model_name="SellerPhone", manufacturer="BrandS", price=100, stock_quantity=5, user_id=created_seller.id)
    db.session.add(phone_by_seller)
    db.session.commit()

    # Buyer đặt hàng sản phẩm này
    buyer_user_for_this_test = User.query.filter_by(username='test_buyer').first() # Giả sử buyer này có token buyer_token
    order_with_seller_item = Order(user_id=buyer_user_for_this_test.id, total_amount=100, status='pending', shipping_address='Seller Item Order')
    db.session.add(order_with_seller_item)
    db.session.flush()
    order_item = OrderItem(order_id=order_with_seller_item.id, phone_id=phone_by_seller.id, quantity=1, price_at_purchase=100)
    db.session.add(order_item)
    db.session.commit()


    headers = {'Authorization': f'Bearer {seller_token}'}
    response = client.get('/orders', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['data']) >= 1
    found_order = False
    for order_data in data['data']:
        if order_data['id'] == order_with_seller_item.id:
            found_order = True
            # Kiểm tra xem item trong order có phải của seller này không
            assert any(item['phone']['id'] == phone_by_seller.id for item in order_data['items'])
    assert found_order, "Đơn hàng chứa sản phẩm của seller không được tìm thấy."

def test_get_orders_as_admin(client, admin_token, created_order):
    """Kiểm thử admin lấy tất cả đơn hàng."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/orders', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['data']) >= 1 # Phải có ít nhất created_order
    assert any(order['id'] == created_order.id for order in data['data'])

def test_get_orders_filter_by_status(client, admin_token, created_order):
    """Kiểm thử lọc đơn hàng theo trạng thái."""
    # Đảm bảo created_order có status 'pending'
    assert created_order.status == 'pending'

    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/orders?status=pending', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert len(data['data']) > 0
    for order_data in data['data']:
        assert order_data['status'] == 'pending'

    response_shipped = client.get('/orders?status=shipped', headers=headers)
    data_shipped = json.loads(response_shipped.data)
    assert response_shipped.status_code == 200
    # Có thể không có đơn shipped nào nếu chỉ có created_order
    assert all(order_data['status'] == 'shipped' for order_data in data_shipped['data'])


# --- GET /orders/{order_id} ---
def test_get_order_details_as_buyer_owner(client, buyer_token, created_order):
    """Buyer xem chi tiết đơn hàng của mình."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.get(f'/orders/{created_order.id}', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['id'] == created_order.id

def test_get_order_details_as_buyer_not_owner_forbidden(client, buyer_token, created_order, init_database):
    """Buyer cố xem đơn hàng không phải của mình."""
    # Tạo một buyer khác và một order khác
    other_buyer = User(username='otherbuyer', password_hash=generate_password_hash('pass'), role='buyer')
    db.session.add(other_buyer)
    db.session.commit()
    other_order = Order(user_id=other_buyer.id, total_amount=50, status='pending', shipping_address='other')
    db.session.add(other_order)
    db.session.commit()

    headers = {'Authorization': f'Bearer {buyer_token}'} # Token của buyer gốc
    response = client.get(f'/orders/{other_order.id}', headers=headers) # Cố xem đơn của other_buyer
    assert response.status_code == 403

def test_get_order_details_as_admin(client, admin_token, created_order):
    """Admin xem chi tiết đơn hàng bất kỳ."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get(f'/orders/{created_order.id}', headers=headers)
    assert response.status_code == 200
    assert json.loads(response.data)['id'] == created_order.id

def test_get_order_details_not_found(client, admin_token, init_database):
    """Xem chi tiết đơn hàng không tồn tại."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.get('/orders/99999', headers=headers)
    assert response.status_code == 404


# --- PUT /orders/{order_id}/status ---
@pytest.mark.parametrize("new_status", ['processing', 'shipped'])
def test_update_order_status_by_seller_valid(client, seller_token, created_order, created_seller):
    """
    Seller cập nhật trạng thái đơn hàng (giả sử order này chứa SP của seller này).
    Cần đảm bảo `created_order` chứa SP của `created_seller`.
    """
    # Giả sử created_order chứa sản phẩm của created_seller. Nếu không, cần setup lại.
    # Hoặc tạo 1 order mới ở đây với SP của seller này
    phone_by_seller = created_order.items[0].phone # Giả sử phone này là của seller
    phone_by_seller.user_id = created_seller.id
    db.session.add(phone_by_seller)
    db.session.commit()


    headers = {'Authorization': f'Bearer {seller_token}'}
    payload = {'status': new_status}
    response = client.put(f'/orders/{created_order.id}/status', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['order']['status'] == new_status
    db_order = Order.query.get(created_order.id)
    assert db_order.status == new_status

def test_update_order_status_by_admin_to_delivered(client, admin_token, created_order):
    """Admin cập nhật trạng thái đơn hàng sang delivered."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    payload = {'status': 'delivered'}
    response = client.put(f'/orders/{created_order.id}/status', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['order']['status'] == 'delivered'

def test_update_order_status_by_buyer_forbidden(client, buyer_token, created_order):
    """Buyer không được cập nhật trạng thái đơn hàng."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'status': 'processing'}
    response = client.put(f'/orders/{created_order.id}/status', data=json.dumps(payload), content_type='application/json', headers=headers)
    assert response.status_code == 403 # Do decorator @seller_or_admin_required

def test_update_order_status_invalid_status(client, admin_token, created_order):
    """Cập nhật trạng thái không hợp lệ."""
    headers = {'Authorization': f'Bearer {admin_token}'}
    payload = {'status': 'invalid_status_value'}
    response = client.put(f'/orders/{created_order.id}/status', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400 # Marshmallow validation
    assert 'errors' in data and 'status' in data['errors']

def test_update_status_of_delivered_order_forbidden(client, admin_token, created_order):
    """Không cho cập nhật trạng thái của đơn đã delivered."""
    # Set order to delivered first
    created_order.status = 'delivered'
    db.session.add(created_order)
    db.session.commit()

    headers = {'Authorization': f'Bearer {admin_token}'}
    payload = {'status': 'processing'}
    response = client.put(f'/orders/{created_order.id}/status', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400
    assert "Không thể thay đổi trạng thái của đơn hàng đã được giao thành công" in data['error']['message']


# --- POST /orders/{order_id}/cancel ---
def test_cancel_order_by_buyer_owner_pending(client, buyer_token, created_order):
    """Buyer hủy đơn hàng 'pending' của mình."""
    assert created_order.status == 'pending' # Đảm bảo trạng thái ban đầu
    phone_item = created_order.items[0]
    original_stock = phone_item.phone.stock_quantity

    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.post(f'/orders/{created_order.id}/cancel', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['order']['status'] == 'cancelled'
    db_order = Order.query.get(created_order.id)
    assert db_order.status == 'cancelled'
    # Kiểm tra tồn kho được hoàn lại
    assert phone_item.phone.stock_quantity == original_stock + phone_item.quantity

def test_cancel_order_by_buyer_owner_shipped_forbidden(client, buyer_token, created_order):
    """Buyer không được hủy đơn đã 'shipped'."""
    created_order.status = 'shipped' # Giả lập đơn đã shipped
    db.session.add(created_order)
    db.session.commit()

    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.post(f'/orders/{created_order.id}/cancel', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 403
    assert "Bạn không thể hủy đơn hàng này vì nó đang ở trạng thái 'shipped'" in data['error']['message']


def test_cancel_order_by_admin(client, admin_token, created_order):
    """Admin hủy đơn hàng."""
    phone_item = created_order.items[0]
    original_stock = phone_item.phone.stock_quantity

    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post(f'/orders/{created_order.id}/cancel', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 200
    assert data['order']['status'] == 'cancelled'
    assert phone_item.phone.stock_quantity == original_stock + phone_item.quantity


def test_cancel_already_cancelled_order(client, admin_token, created_order):
    """Hủy một đơn hàng đã được hủy trước đó."""
    # Hủy lần 1
    client.post(f'/orders/{created_order.id}/cancel', headers={'Authorization': f'Bearer {admin_token}'})

    # Hủy lần 2
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post(f'/orders/{created_order.id}/cancel', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400 # API của bạn trả về 400 cho trường hợp này
    assert "Đơn hàng này đã được hủy trước đó" in data['message']