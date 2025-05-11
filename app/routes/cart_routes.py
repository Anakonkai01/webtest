# phone_management_api/app/routes/cart_routes.py
from flask import Blueprint, request, jsonify, abort, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.phone import Phone
from app.schemas import cart_schema_output, cart_item_input_schema, cart_item_update_schema
from app.utils.decorators import buyer_required
from app.utils.helpers import get_or_create_user_cart

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
    
    data = cart_item_input_schema.load(json_data)

    phone_id_to_add = data['phone_id']
    quantity_to_add = data['quantity']

    phone = Phone.query.get(phone_id_to_add)
    if not phone:
        abort(404, description=f"Sản phẩm với ID {phone_id_to_add} không tồn tại.")

    if phone.stock_quantity == 0 :
         abort(400, description=f"Sản phẩm '{phone.model_name}' đã hết hàng.")

    cart_item = CartItem.query.filter_by(cart_id=cart.id, phone_id=phone.id).first()

    if cart_item:
        new_quantity = cart_item.quantity + quantity_to_add
        if phone.stock_quantity < new_quantity:
            can_add = phone.stock_quantity - cart_item.quantity
            if can_add <=0 :
                 abort(400, description=f"Không thể thêm '{phone.model_name}'. Đã có {cart_item.quantity} trong giỏ. Tồn kho chỉ còn {phone.stock_quantity}.")
            else:
                 abort(400, description=f"Không đủ số lượng tồn kho cho sản phẩm '{phone.model_name}'. Bạn có thể thêm tối đa {can_add} sản phẩm nữa.")
        cart_item.quantity = new_quantity
    else: 
        if phone.stock_quantity < quantity_to_add:
            abort(400, description=f"Không đủ số lượng tồn kho cho sản phẩm '{phone.model_name}'. Yêu cầu: {quantity_to_add}, chỉ còn: {phone.stock_quantity}.")
        cart_item = CartItem(cart_id=cart.id, phone_id=phone.id, quantity=quantity_to_add)
        db.session.add(cart_item)

    cart.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(cart_schema_output.dump(cart)), 200

@cart_bp.route('/items/<int:cart_item_id>', methods=['PUT'])
@jwt_required()
@buyer_required
def update_cart_item_route(cart_item_id):
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()
    if not cart:
        abort(404, description="Không tìm thấy giỏ hàng cho người dùng này. Không thể cập nhật item.")

    cart_item = CartItem.query.filter_by(id=cart_item_id, cart_id=cart.id).first()
    if not cart_item:
        abort(404, description=f"Mục hàng với ID {cart_item_id} không tìm thấy trong giỏ của bạn.")

    json_data = request.get_json()
    if not json_data:
        abort(400, description="Cần cung cấp 'quantity' để cập nhật.")
    
    data = cart_item_update_schema.load(json_data)
    new_quantity = data['quantity']

    message = ""
    if new_quantity <= 0:
        db.session.delete(cart_item)
        message = f"Mục hàng ID {cart_item_id} đã được xóa khỏi giỏ hàng do số lượng cập nhật là {new_quantity}."
    else:
        phone = cart_item.phone
        if not phone: 
             db.session.rollback()
             current_app.logger.error(f"Lỗi nghiêm trọng: Sản phẩm ID {cart_item.phone_id} không tìm thấy cho cart_item ID {cart_item.id}")
             abort(500, description="Lỗi: Sản phẩm liên quan đến mục trong giỏ không còn tồn tại trong hệ thống.")
        
        if phone.stock_quantity < new_quantity:
            abort(400, description=f"Không đủ số lượng tồn kho cho sản phẩm '{phone.model_name}'. Yêu cầu: {new_quantity}, chỉ còn: {phone.stock_quantity}.")
        cart_item.quantity = new_quantity
        message = f"Đã cập nhật số lượng cho mục hàng ID {cart_item_id} thành {new_quantity}."

    cart.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(message=message, cart=cart_schema_output.dump(cart)), 200

@cart_bp.route('/items/<int:cart_item_id>', methods=['DELETE'])
@jwt_required()
@buyer_required
def remove_cart_item_route(cart_item_id):
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()
    if not cart:
         abort(404, description="Không tìm thấy giỏ hàng. Không thể xóa item.")

    cart_item = CartItem.query.filter_by(id=cart_item_id, cart_id=cart.id).first()
    if not cart_item:
        abort(404, description=f"Mục hàng với ID {cart_item_id} không tìm thấy trong giỏ của bạn.")

    db.session.delete(cart_item)
    cart.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify(message=f"Mục hàng ID {cart_item_id} đã được xóa khỏi giỏ.", cart=cart_schema_output.dump(cart)), 200

@cart_bp.route('/', methods=['DELETE'])
@jwt_required()
@buyer_required
def clear_cart_route():
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()

    if cart and cart.items.first():
        for item in cart.items.all():
            db.session.delete(item)
            
        cart.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(message="Giỏ hàng đã được dọn sạch.", cart=cart_schema_output.dump(cart)), 200
    elif cart: 
        return jsonify(message="Giỏ hàng đã trống.", cart=cart_schema_output.dump(cart)), 200
    else: 
        abort(404, description="Không tìm thấy giỏ hàng để xóa.")