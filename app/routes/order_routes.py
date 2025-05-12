# app/routes/order_routes.py
from flask import Blueprint, request, jsonify, abort, current_app, url_for
from sqlalchemy import desc, asc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime
from marshmallow import ValidationError

from app.extensions import db
from app.models.order import (
    Order, OrderItem, ALLOWED_ORDER_STATUSES, ORDER_STATUS_PENDING, 
    ORDER_STATUS_CANCELLED, ORDER_STATUS_SHIPPED, ORDER_STATUS_DELIVERED, 
    ORDER_STATUS_PROCESSING, ORDER_STATUS_FAILED
)
from app.models.cart import Cart, CartItem # CartItem needed for create_order
from app.models.phone import Phone
from app.schemas import (
    order_schema_output, # Use this for single order object
    # orders_schema_output, # Not strictly needed if using order_schema_output(many=True)
    order_create_schema_input, order_status_update_schema_input
)
from app.utils.decorators import buyer_required, seller_or_admin_required

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route('/', methods=['POST'])
@jwt_required()
@buyer_required
def create_order_route():
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()
    if not cart or cart.is_empty(): abort(400, description="Giỏ hàng trống.")

    json_data = request.get_json()
    try:
        order_input_data = order_create_schema_input.load(json_data if json_data else {})
    except ValidationError as err: abort(400, description=err.messages)
    shipping_address = order_input_data['shipping_address']

    items_to_order_details = []
    calculated_total_amount = 0.0

    try:
        with db.session.begin_nested():
            for cart_item in cart.items.all():
                phone = Phone.query.with_for_update().get(cart_item.phone_id) # Lock row for update
                if not phone: raise ValueError(f"Sản phẩm ID {cart_item.phone_id} không tồn tại.")
                if phone.stock_quantity < cart_item.quantity:
                    raise ValueError(f"Không đủ tồn kho cho '{phone.model_name}'. Yêu cầu: {cart_item.quantity}, còn: {phone.stock_quantity}.")
                items_to_order_details.append({"phone_instance": phone, "quantity": cart_item.quantity, "price_at_purchase": float(phone.price)})
                calculated_total_amount += float(cart_item.quantity) * float(phone.price)
            
            new_order = Order(user_id=current_user_id, total_amount=round(calculated_total_amount, 2), status=ORDER_STATUS_PENDING, shipping_address=shipping_address)
            db.session.add(new_order)
            db.session.flush() 

            for item_detail in items_to_order_details:
                phone_to_update = item_detail["phone_instance"]
                db.session.add(OrderItem(order_id=new_order.id, phone_id=phone_to_update.id, quantity=item_detail["quantity"], price_at_purchase=item_detail["price_at_purchase"]))
                phone_to_update.stock_quantity -= item_detail["quantity"]
                db.session.add(phone_to_update) # Mark for update

            CartItem.query.filter_by(cart_id=cart.id).delete(synchronize_session='fetch') # Adjust synchronize_session
            cart.updated_at = datetime.utcnow()
            db.session.add(cart)
        db.session.commit()
    except ValueError as ve: db.session.rollback(); abort(400, description=str(ve))
    except Exception as e: db.session.rollback(); current_app.logger.error(f"Lỗi tạo đơn hàng: {str(e)}"); abort(500, description="Lỗi máy chủ khi tạo đơn hàng.")

    # order_schema_output.dump will include HATEOAS links
    return jsonify(order_schema_output.dump(new_order)), 201


@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders_list_route():
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    query = Order.query

    if current_user_role == 'buyer':
        query = query.filter(Order.user_id == current_user_id)
    elif current_user_role == 'seller':
        query = query.join(OrderItem, Order.id == OrderItem.order_id)\
                     .join(Phone, OrderItem.phone_id == Phone.id)\
                     .filter(Phone.user_id == current_user_id).distinct()

    status_filter = request.args.get('status')
    if status_filter:
        if status_filter not in ALLOWED_ORDER_STATUSES: abort(400, description=f"Trạng thái lọc '{status_filter}' không hợp lệ.")
        query = query.filter(Order.status == status_filter)

    sort_by = request.args.get('sort_by', 'created_at')
    order_dir = request.args.get('order', 'desc').lower()
    # ... (sort logic giữ nguyên) ...
    order_sort_columns = {'created_at': Order.created_at, 'updated_at': Order.updated_at, 'total_amount': Order.total_amount, 'status': Order.status, 'id': Order.id}
    sort_column = order_sort_columns.get(sort_by)
    if not sort_column: abort(400, description=f"Trường sắp xếp đơn hàng '{sort_by}' không hợp lệ.")
    if order_dir not in ['asc', 'desc']: abort(400, description="Thứ tự sắp xếp không hợp lệ.")
    query = query.order_by(desc(sort_column) if order_dir == 'desc' else asc(sort_column))

    # ... (pagination logic giữ nguyên) ...
    try:
        page = request.args.get('page', 1, type=int); per_page = request.args.get('per_page', current_app.config.get('DEFAULT_ORDER_PER_PAGE', 5), type=int)
        if page <= 0 or per_page <= 0: abort(400, description="'page' và 'per_page' phải dương.")
        if per_page > 100: per_page = 100 # Max limit
    except: abort(400, description="'page'/'per_page' không hợp lệ.")
    paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    response_data = {
        "data": order_schema_output.dump(paginated_orders.items, many=True), # Use many=True
        "meta": {
            "page": paginated_orders.page, "per_page": paginated_orders.per_page,
            "total_pages": paginated_orders.pages, "total_items": paginated_orders.total,
            "filters_applied": {k: v for k, v in request.args.items() if k not in ['page', '_external']}
        },
        "_links": {}
    }
    current_request_args = request.args.copy()
    response_data["_links"]["self"] = {"href": url_for(request.endpoint, _external=False, **current_request_args), "method": "GET"}
    if paginated_orders.has_next:
        next_args = current_request_args.copy(); next_args['page'] = paginated_orders.next_num
        response_data["_links"]["next"] = {"href": url_for(request.endpoint, _external=False, **next_args), "method": "GET"}
    if paginated_orders.has_prev:
        prev_args = current_request_args.copy(); prev_args['page'] = paginated_orders.prev_num
        response_data["_links"]["prev"] = {"href": url_for(request.endpoint, _external=False, **prev_args), "method": "GET"}
    # Add create link if user is a buyer (context-dependent, might be better on cart response)
    # if current_user_role == 'buyer':
    #     response_data["_links"]["create_order"] = {
    #         "href": url_for('orders_bp.create_order_route', _external=False), "method": "POST",
    #         "description": "Create a new order from cart."}
    return jsonify(response_data), 200


@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")
    # ... (logic kiểm tra quyền giữ nguyên) ...
    if current_user_role == 'buyer' and order.user_id != current_user_id: abort(403)
    elif current_user_role == 'seller':
        if not OrderItem.query.join(Phone).filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first(): abort(403)
    # order_schema_output.dump will include HATEOAS links
    return jsonify(order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@seller_or_admin_required # Decorator handles role check
def update_order_status_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'seller': # Seller can only update their orders
        if not OrderItem.query.join(Phone).filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first():
            abort(403, description="Bạn không có quyền cập nhật trạng thái cho đơn hàng này.")

    json_data = request.get_json();
    if not json_data: abort(400, description="Không có dữ liệu đầu vào.")
    try:
        data = order_status_update_schema_input.load(json_data)
    except ValidationError as err: abort(400, description=err.messages)
    new_status = data['status']

    if order.status in [ORDER_STATUS_DELIVERED, ORDER_STATUS_CANCELLED]:
         abort(400, description=f"Không thể thay đổi trạng thái của đơn hàng đã '{order.status}'.")
    if current_user_role == 'seller' and new_status not in [ORDER_STATUS_PROCESSING, ORDER_STATUS_SHIPPED, order.status, ORDER_STATUS_CANCELLED]: # Seller can also cancel
         abort(403, description=f"Người bán không được phép cập nhật đơn hàng sang trạng thái '{new_status}'.")
    
    stock_reverted_message = ""
    try:
        with db.session.begin_nested():
            if new_status == ORDER_STATUS_CANCELLED and order.status not in [ORDER_STATUS_CANCELLED, ORDER_STATUS_DELIVERED, ORDER_STATUS_FAILED]:
                for item in order.items:
                    phone = item.phone
                    if phone: phone.stock_quantity += item.quantity; db.session.add(phone)
                stock_reverted_message = " Tồn kho đã được hoàn lại."
            order.status = new_status
            order.updated_at = datetime.utcnow()
            db.session.add(order) # Mark order for update
        db.session.commit()
    except Exception as e: db.session.rollback(); abort(500, description="Lỗi máy chủ khi cập nhật trạng thái.")
    
    # order_schema_output.dump will include HATEOAS links
    return jsonify(message=f"Cập nhật trạng thái thành công.{stock_reverted_message}", order=order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    can_cancel = False
    if current_user_role == 'admin': can_cancel = True
    elif current_user_role == 'buyer' and order.user_id == current_user_id and order.status in [ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING]:
        can_cancel = True
    # Seller có thể cancel qua route update_status nếu logic cho phép
    
    if not can_cancel: abort(403, description="Không thể hủy đơn hàng này.")
    if order.status == ORDER_STATUS_CANCELLED: return jsonify(message="Đơn hàng đã hủy.", order=order_schema_output.dump(order)), 400 # Bad request if already cancelled
    if order.status == ORDER_STATUS_DELIVERED: abort(400, "Không thể hủy đơn đã giao.")
        
    try:
        with db.session.begin_nested():
            for item in order.items:
                phone = item.phone
                if phone: phone.stock_quantity += item.quantity; db.session.add(phone)
            order.status = ORDER_STATUS_CANCELLED
            order.updated_at = datetime.utcnow()
            db.session.add(order)
        db.session.commit()
    except Exception as e: db.session.rollback(); abort(500, description="Lỗi máy chủ khi hủy đơn.")

    # order_schema_output.dump will include HATEOAS links
    return jsonify(message="Đơn hàng đã hủy, tồn kho đã cập nhật.", order=order_schema_output.dump(order)), 200