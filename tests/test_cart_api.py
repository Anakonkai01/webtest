
import json
import pytest
from app.models.cart import Cart, CartItem
from app.models.phone import Phone
from app.extensions import db


def get_db_cart(user_id):
    return Cart.query.filter_by(user_id=user_id).first()

def get_cart_item_db(cart_id, phone_id):
    return CartItem.query.filter_by(cart_id=cart_id, phone_id=phone_id).first()

def test_view_cart_empty_for_new_buyer(client, buyer_token, created_buyer):
    """Kiểm thử xem giỏ hàng của buyer mới (chưa có hành động)."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.get('/cart', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data['user_id'] == created_buyer.id
    assert len(data['items']) == 0
    assert data['total_price'] == 0
def test_view_cart_with_items(client, buyer_token, buyer_cart_with_item): # buyer_cart_with_item đã thêm 1 item
    """Kiểm thử xem giỏ hàng có item."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.get('/cart', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['items']) == 1
    assert data['items'][0]['phone']['id'] == buyer_cart_with_item['phone_added'].id
    assert data['items'][0]['quantity'] == 1
    assert data['total_price'] > 0

def test_view_cart_unauthorized_no_token(client, init_database):"""Kiểm thử xem giỏ hàng khi không có token."""
    response = client.get('/cart')
    assert response.status_code == 401

def test_view_cart_with_seller_token_forbidden(client, seller_token, init_database):
    """Kiểm thử xem giỏ hàng với seller token."""
    headers = {'Authorization': f'Bearer {seller_token}'}
    response = client.get('/cart', headers=headers)
def test_add_item_to_cart_success(client, buyer_token, created_buyer, created_phone):
    """Kiểm thử thêm sản phẩm thành công vào giỏ hàng trống."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'phone_id': created_phone.id, 'quantity': 1}
    response = client.post('/cart/items', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['items']) == 1
    assert data['items'][0]['phone']['id'] == created_phone.id
    assert data['items'][0]['quantity'] == 1

    # Kiểm tra trong DB
    db_cart = get_db_cart(created_buyer.id)
    assert db_cart is not None
    cart_item_in_db = get_cart_item_db(db_cart.id, created_phone.id)
    assert cart_item_in_db is not None
    assert cart_item_in_db.quantity == 1

def test_add_same_item_to_cart_updates_quantity(client, buyer_token, created_buyer, created_phone):
    """Kiểm thử thêm cùng sản phẩm sẽ cập nhật số lượng."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    client.post('/cart/items', data=json.dumps({'phone_id': created_phone.id, 'quantity': 1}), content_type='application/json', headers=headers)
    # Lần 2
    response = client.post('/cart/items', data=json.dumps({'phone_id': created_phone.id, 'quantity': 2}), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert len(data['items']) == 1 # Vẫn chỉ có 1 item loại đó
 assert data['items'][0]['phone']['id'] == created_phone.id
 assert data['items'][0]['quantity'] == 3

def test_add_item_to_cart_phone_not_found(client, buyer_token, init_database):
    """Kiểm thử thêm sản phẩm không tồn tại vào giỏ."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'phone_id': 99999, 'quantity': 1}
    response = client.post('/cart/items', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 404
    assert "Sản phẩm với ID 99999 không tồn tại" in data['error']['message']

def test_add_item_to_cart_insufficient_stock(client, buyer_token, created_phone):
    """Kiểm thử thêm sản phẩm với số lượng vượt quá tồn kho."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    # Giả sử created_phone.stock_quantity là 10 (từ fixture)
    payload = {'phone_id': created_phone.id, 'quantity': created_phone.stock_quantity + 1}
    response = client.post('/cart/items', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400
    assert "Không đủ số lượng tồn kho" in data['error']['message']

def test_add_item_to_cart_zero_quantity_invalid(client, buyer_token, created_phone):
    """Kiểm thử thêm sản phẩm với số lượng 0 (không hợp lệ theo schema)."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'phone_id': created_phone.id, 'quantity': 0}
    response = client.post('/cart/items', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400
    assert 'errors' in data and 'quantity' in data['errors']
def test_update_cart_item_quantity_success(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử cập nhật số lượng item trong giỏ thành công."""
    cart_item_id = buyer_cart_with_item['item'].id
    phone_stock = buyer_cart_with_item['phone_added'].stock_quantity
    new_quantity = 2
    if phone_stock < new_quantity:
        pytest.skip("Không đủ tồn kho để test cập nhật số lượng này")

    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'quantity': new_quantity}
    response = client.put(f'/cart/items/{cart_item_id}', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert f"Đã cập nhật số lượng cho mục hàng ID {cart_item_id} thành {new_quantity}" in data['message']
    updated_item_in_cart = next(item for item in data['cart']['items'] if item['id'] == cart_item_id)
    assert updated_item_in_cart['quantity'] == new_quantity

def test_update_cart_item_quantity_to_zero_deletes_item(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử cập nhật số lượng về 0 sẽ xóa item."""
    cart_item_id = buyer_cart_with_item['item'].id
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'quantity': 0}
    response = client.put(f'/cart/items/{cart_item_id}', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert f"Mục hàng ID {cart_item_id} đã được xóa khỏi giỏ hàng" in data['message']
    assert not any(item['id'] == cart_item_id for item in data['cart']['items'])


    """Kiểm thử cập nhật cart item không tồn tại."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'quantity': 5}
    response = client.put('/cart/items/99999', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 404
    assert "Mục hàng với ID 99999 không tìm thấy" in data['error']['message']

def test_update_cart_item_insufficient_stock(client, buyer_token, buyer_cart_with_item):
    """Kiểm thử cập nhật số lượng vượt quá tồn kho."""
    cart_item_id = buyer_cart_with_item['item'].id
    phone_stock = buyer_cart_with_item['phone_added'].stock_quantity
    headers = {'Authorization': f'Bearer {buyer_token}'}
    payload = {'quantity': phone_stock + 5}
    response = client.put(f'/cart/items/{cart_item_id}', data=json.dumps(payload), content_type='application/json', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 400
    assert "Không đủ số lượng tồn kho" in data['error']['message']


# --- DELETE /cart/items/{cart_item_id} ---
    """Kiểm thử xóa một item khỏi giỏ hàng."""
    cart_item_id = buyer_cart_with_item['item'].id
    initial_item_count = len(buyer_cart_with_item['cart'].items.all())

    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.delete(f'/cart/items/{cart_item_id}', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert f"Mục hàng ID {cart_item_id} đã được xóa khỏi giỏ" in data['message']
    assert len(data['cart']['items']) == initial_item_count - 1
    assert not any(item['id'] == cart_item_id for item in data['cart']['items'])


def test_remove_cart_item_not_found(client, buyer_token, init_database):
    headers = {'Authorization': f'Bearer {buyer_token}'}
    response = client.delete('/cart/items/99999', headers=headers)
    data = json.loads(response.data)
    assert response.status_code == 404
    assert "Mục hàng với ID 99999 không tìm thấy" in data['error']['message']

# --- DELETE /cart ---
def test_clear_cart_success(client, buyer_token, buyer_cart_with_item):
    headers = {'Authorization': f'Bearer {buyer_token}'}
    # Đảm bảo có gì đó trong giỏ

    response = client.delete('/cart', headers=headers)
    data = json.loads(response.data)

    assert response.status_code == 200
    assert "Giỏ hàng đã được dọn sạch" in data['message']
    assert len(data['cart']['items']) == 0
    assert data['cart']['total_price'] == 0

def test_clear_empty_cart(client, buyer_token, created_buyer):
    """Kiểm thử xóa giỏ hàng đã rỗng."""
    headers = {'Authorization': f'Bearer {buyer_token}'}
    # Kiểm tra giỏ hàng rỗng
    cart_response = client.get('/cart', headers=headers)
    cart_data = json.loads(cart_response.data)
 assert len(cart_data['items']) == 0


    response = client.delete('/cart', headers=headers)
 assert response.status_code == 200