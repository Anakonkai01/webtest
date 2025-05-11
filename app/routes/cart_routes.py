# phone_management_api/app/routes/cart_routes.py
from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from datetime import datetime

from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.phone import Phone
from app.models.user import User # Cần cho get_or_create_user_cart
from app.schemas import cart_schema_output, cart_item_input_schema, cart_item_update_schema
from app.utils.decorators import buyer_required
from app.utils.helpers import get_or_create_user_cart # Import helper

cart_bp = Blueprint('cart_bp', __name__)

@cart_bp.route('/', methods=['GET'])
@jwt_required()
@buyer_required
def view_cart_route():
    current_user_id = int(get_jwt_identity())
    cart = get_or_create_user_cart(current_user_id)
    return jsonify(cart_schema_output.dump(cart)), 200

@cart_bp.route('/items', methods=['POST'])
@jwt_required()
@buyer_required
def add_item_to_cart_route():
    current_user_id = int(get_jwt_identity())
    cart = get_or_create_user_cart(current_user_id)

    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu đầu vào.")
    try:
        data = cart_item_input_schema.load(json_data)
    except ValidationError as err:
        return jsonify(errors=err.messages), 400

    phone = Phone.query.get(data['phone_id'])
    if not phone:
        abort(404, description=f"Sản phẩm với ID {data['phone_id']} không tồn tại.")

    quantity_to_add = data['quantity']

    # Kiểm tra tồn kho trước
    if phone.stock_quantity < quantity_to_add:
         abort(400, description=f"Không đủ số lượng tồn kho cho sản phẩm '{phone.model_name}'. Yêu cầu: {quantity_to_add}, chỉ còn: {phone.stock_quantity}.")

    cart_item = CartItem.query.filter_by(cart_id=cart.id, phone_id=phone.id).first()

    if cart_item: # Sản phẩm đã có, cập nhật số lượng
        new_quantity = cart_item.quantity + quantity_to_add
        # Kiểm tra lại tồn kho với tổng số lượng mới
        if phone.stock_quantity < new_quantity:
            abort(400, description=f"Không đủ số lượng tồn kho để thêm. Tổng số lượng yêu cầu ({new_quantity}) vượt quá số lượng còn lại ({phone.stock_quantity}).")
        cart_item.quantity = new_quantity
    else: # Sản phẩm chưa có, tạo mới (đã kiểm tra stock_quantity >= quantity_to_add ở trên)
        cart_item = CartItem(cart_id=cart.id, phone_id=phone.id, quantity=quantity_to_add)
        db.session.add(cart_item)

    cart.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(cart_schema_output.dump(cart)), 200 # Trả về giỏ hàng đã cập nhật

@cart_bp.route('/items/<int:cart_item_id>', methods=['PUT'])
@jwt_required()
@buyer_required
def update_cart_item_route(cart_item_id):
    current_user_id = int(get_jwt_identity())
    # Không dùng get_or_create_user_cart vì nếu cart không tồn tại thì item cũng không thể tồn tại
    cart = Cart.query.filter_by(user_id=current_user_id).first()
    if not cart:
        abort(404, description="Không tìm thấy giỏ hàng cho người dùng này.")

    cart_item = CartItem.query.filter_by(id=cart_item_id, cart_id=cart.id).first()
    if not cart_item:
        abort(404, description=f"Mục hàng với ID {cart_item_id} không tìm thấy trong giỏ của bạn.")

    json_data = request.get_json()
    if not json_data:
        abort(400, description="Cần cung cấp 'quantity' để cập nhật.")
    try:
        data = cart_item_update_schema.load(json_data) # Chỉ validate trường quantity
    except ValidationError as err:
        return jsonify(errors=err.messages), 400

    new_quantity = data['quantity']

    if new_quantity <= 0: # Nếu muốn xóa item khi quantity là 0 hoặc âm
        db.session.delete(cart_item)
        msg = f"Mục hàng ID {cart_item_id} đã được xóa do số lượng là {new_quantity}."
    else:
        phone = cart_item.phone # Phone object đã được load qua relationship
        if not phone: # Phòng trường hợp phone bị xóa trong khi vẫn còn trong giỏ
             abort(500, description="Lỗi: Sản phẩm liên quan đến mục trong giỏ không còn tồn tại.")
        if phone.stock_quantity < new_quantity:
            abort(400, description=f"Không đủ số lượng tồn kho cho sản phẩm '{phone.model_name}'. Yêu cầu: {new_quantity}, chỉ còn: {phone.stock_quantity}.")
        cart_item.quantity = new_quantity
        msg = f"Đã cập nhật số lượng cho mục hàng ID {cart_item_id}."

    cart.updated_at = datetime.utcnow()
    db.session.commit()
    # Tải lại cart để đảm bảo total_price được tính toán lại chính xác sau khi item thay đổi
    updated_cart = Cart.query.get(cart.id)
    return jsonify(message=msg, cart=cart_schema_output.dump(updated_cart)), 200

@cart_bp.route('/items/<int:cart_item_id>', methods=['DELETE'])
@jwt_required()
@buyer_required
def remove_cart_item_route(cart_item_id):
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()
    if not cart:
         abort(404, description="Không tìm thấy giỏ hàng.")

    cart_item = CartItem.query.filter_by(id=cart_item_id, cart_id=cart.id).first()
    if not cart_item:
        abort(404, description=f"Mục hàng với ID {cart_item_id} không tìm thấy trong giỏ của bạn.")

    db.session.delete(cart_item)
    cart.updated_at = datetime.utcnow()
    db.session.commit()
    updated_cart = Cart.query.get(cart.id)
    return jsonify(message=f"Mục hàng ID {cart_item_id} đã được xóa khỏi giỏ.", cart=cart_schema_output.dump(updated_cart)), 200

@cart_bp.route('/', methods=['DELETE'])
@jwt_required()
@buyer_required
def clear_cart_route():
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()

    if cart and cart.items.first(): # Kiểm tra xem cart có items không
        # Do cascade='all, delete-orphan' trên Cart.items,
        # việc xóa các item hoặc xóa cart sẽ tự động xóa các CartItem liên quan.
        # Cách an toàn hơn là xóa trực tiếp CartItem.
        CartItem.query.filter_by(cart_id=cart.id).delete()
        cart.updated_at = datetime.utcnow() # Cập nhật thời gian cho cart
        db.session.commit()
        # Tải lại cart (giờ đã trống) để trả về thông tin chính xác
        cleared_cart = Cart.query.get(cart.id)
        return jsonify(message="Giỏ hàng đã được xóa sạch.", cart=cart_schema_output.dump(cleared_cart)), 200

    # Nếu không có cart hoặc cart đã trống
    return jsonify(message="Giỏ hàng đã trống hoặc không tồn tại."), 200