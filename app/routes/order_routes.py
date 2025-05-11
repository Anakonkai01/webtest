# phone_management_api/app/routes/order_routes.py
from flask import Blueprint, request, jsonify, abort, url_for
from sqlalchemy import desc, asc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from marshmallow import ValidationError
from datetime import datetime

from app.extensions import db
from app.models.order import Order, OrderItem, ALLOWED_ORDER_STATUSES, ORDER_STATUS_PENDING, ORDER_STATUS_CANCELLED, ORDER_STATUS_SHIPPED, ORDER_STATUS_DELIVERED, ORDER_STATUS_PROCESSING
from app.models.cart import Cart, CartItem # Cần để xóa cart sau khi đặt hàng
from app.models.phone import Phone
from app.models.user import User
from app.schemas import order_schema_output, orders_schema_output, order_create_schema_input, order_status_update_schema_input
from app.utils.decorators import buyer_required, seller_or_admin_required, admin_required

orders_bp = Blueprint('orders_bp', __name__)

@orders_bp.route('/', methods=['POST'])
@jwt_required()
@buyer_required
def create_order_route():
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()

    if not cart or cart.is_empty():
        abort(400, description="Giỏ hàng trống. Không thể tạo đơn hàng.")

    json_data = request.get_json()
    if not json_data : # Yêu cầu phải có shipping_address
         abort(400, description="Cần cung cấp địa chỉ giao hàng (shipping_address).")
    try:
        order_input_data = order_create_schema_input.load(json_data)
    except ValidationError as err:
        return jsonify(errors=err.messages), 400

    shipping_address = order_input_data['shipping_address']

    items_to_order_details = []
    calculated_total_amount = 0

    # Bước 1: Kiểm tra tồn kho và chuẩn bị dữ liệu item (chưa thay đổi CSDL)
    for cart_item in cart.items.all():
        phone = cart_item.phone
        if not phone:
            abort(400, description=f"Sản phẩm ID {cart_item.phone_id} trong giỏ không còn tồn tại.")
        if phone.stock_quantity < cart_item.quantity:
            abort(400, description=f"Không đủ tồn kho cho '{phone.model_name}'. Yêu cầu: {cart_item.quantity}, còn: {phone.stock_quantity}.")

        items_to_order_details.append({
            "phone_model": phone, # Giữ lại phone model để cập nhật stock sau
            "quantity": cart_item.quantity,
            "price_at_purchase": phone.price
        })
        calculated_total_amount += cart_item.quantity * phone.price

    calculated_total_amount = round(calculated_total_amount, 2)

    # Bước 2: Tạo Order, OrderItems và cập nhật stock (trong 1 transaction)
    try:
        new_order = Order(
            user_id=current_user_id,
            total_amount=calculated_total_amount,
            status=ORDER_STATUS_PENDING,
            shipping_address=shipping_address
        )
        db.session.add(new_order)
        db.session.flush() # Để new_order có ID

        for item_detail in items_to_order_details:
            phone_to_update = item_detail["phone_model"]
            order_item = OrderItem(
                order_id=new_order.id,
                phone_id=phone_to_update.id,
                quantity=item_detail["quantity"],
                price_at_purchase=item_detail["price_at_purchase"]
            )
            db.session.add(order_item)

            phone_to_update.stock_quantity -= item_detail["quantity"]
            # Không cần db.session.add(phone_to_update) nếu nó đã được lấy từ session
            # và SQLAlchemy đang theo dõi nó. Nhưng để chắc chắn, có thể add.

        # Xóa cart items
        CartItem.query.filter_by(cart_id=cart.id).delete()
        cart.updated_at = datetime.utcnow()
        # db.session.add(cart) # Không cần thiết nếu chỉ cập nhật updated_at

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # app.logger.error(f"Lỗi khi tạo đơn hàng: {e}") # Ghi log nếu bạn có setup logger
        abort(500, description=f"Lỗi máy chủ khi tạo đơn hàng. {str(e)}")

    return jsonify(order_schema_output.dump(new_order)), 201

@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders_list_route():
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    query = Order.query

    if current_user_role == 'buyer':
        query = query.filter_by(user_id=current_user_id)
    elif current_user_role == 'seller':
        query = query.join(OrderItem, Order.id == OrderItem.order_id)\
                     .join(Phone, OrderItem.phone_id == Phone.id)\
                     .filter(Phone.user_id == current_user_id).distinct()
    # Admin xem tất cả

    status_filter = request.args.get('status')
    if status_filter:
        if status_filter not in ALLOWED_ORDER_STATUSES:
            abort(400, description=f"Trạng thái lọc không hợp lệ: {status_filter}.")
        query = query.filter(Order.status == status_filter)

    sort_by = request.args.get('sort_by', 'created_at')
    order_dir = request.args.get('order', 'desc').lower()
    order_sort_columns = {
        'created_at': Order.created_at, 'updated_at': Order.updated_at,
        'total_amount': Order.total_amount, 'status': Order.status, 'id': Order.id
    }
    sort_column = order_sort_columns.get(sort_by)
    if not sort_column: abort(400, description=f"Trường sắp xếp đơn hàng không hợp lệ: {sort_by}")
    if order_dir not in ['asc', 'desc']: abort(400, description="Thứ tự sắp xếp không hợp lệ.")
    query = query.order_by(desc(sort_column) if order_dir == 'desc' else asc(sort_column))

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page <= 0 or per_page <= 0: abort(400, description="page/per_page phải >0.");
        if per_page > 100: per_page = 100
    except: abort(400, "page/per_page phải là số nguyên.");

    paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
    current_args = request.args.copy(); filters_applied = {k: v for k, v in current_args.items() if k != 'page'}
    next_url, prev_url = None, None
    if paginated_orders.has_next:
        next_params = current_args.copy(); next_params['page'] = paginated_orders.next_num
        next_url = url_for('orders_bp.get_orders_list_route', _external=False, **next_params)
    if paginated_orders.has_prev:
        prev_params = current_args.copy(); prev_params['page'] = paginated_orders.prev_num
        prev_url = url_for('orders_bp.get_orders_list_route', _external=False, **prev_params)

    return jsonify({
        "data": orders_schema_output.dump(paginated_orders.items),
        "meta": {"page": paginated_orders.page, "per_page": paginated_orders.per_page,
                 "total_pages": paginated_orders.pages, "total_items": paginated_orders.total,
                 "next_page_url": next_url, "prev_page_url": prev_url, "filters_applied": filters_applied }
    }), 200

@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'buyer' and order.user_id != current_user_id:
        abort(403, description="Bạn không có quyền xem đơn hàng này.")
    elif current_user_role == 'seller':
        is_seller_order = db.session.query(OrderItem.id)\
            .join(Phone, OrderItem.phone_id == Phone.id)\
            .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first()
        if not is_seller_order:
            abort(403, description="Đơn hàng này không chứa sản phẩm của bạn.")
    return jsonify(order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@seller_or_admin_required # Seller chỉ nên cập nhật status cho đơn hàng có sản phẩm của mình
def update_order_status_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'seller':
        is_seller_order = db.session.query(OrderItem.id)\
            .join(Phone, OrderItem.phone_id == Phone.id)\
            .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first()
        if not is_seller_order:
            abort(403, description="Bạn không có quyền cập nhật trạng thái đơn hàng này.")

    json_data = request.get_json()
    if not json_data: abort(400, description="Không có dữ liệu đầu vào.")
    try:
        data = order_status_update_schema_input.load(json_data)
    except ValidationError as err: return jsonify(errors=err.messages), 400
    new_status = data['status']

    # Thêm logic kiểm tra chuyển đổi trạng thái hợp lệ
    if order.status == ORDER_STATUS_DELIVERED and new_status != ORDER_STATUS_DELIVERED:
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã giao.")
    if order.status == ORDER_STATUS_CANCELLED and new_status != ORDER_STATUS_CANCELLED:
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã hủy.")

    # Seller có thể chỉ được phép chuyển sang một số trạng thái nhất định (ví dụ: processing, shipped)
    if current_user_role == 'seller' and new_status not in [ORDER_STATUS_PROCESSING, ORDER_STATUS_SHIPPED, order.status]:
         abort(403, description=f"Seller không được phép cập nhật sang trạng thái '{new_status}'.")


    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/cancel', methods=['POST']) # POST cho hành động cụ thể
@jwt_required()
def cancel_order_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    can_cancel = False
    if current_user_role == 'admin':
        can_cancel = True
    elif current_user_role == 'buyer' and order.user_id == current_user_id:
        if order.status in [ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING]: # Chỉ hủy được khi chưa giao
            can_cancel = True
        else:
            abort(403, description=f"Không thể hủy đơn hàng ở trạng thái '{order.status}'.")
    if not can_cancel and current_user_role != 'admin': # Double check
         abort(403, description="Bạn không có quyền hủy đơn hàng này.")


    if order.status == ORDER_STATUS_CANCELLED:
        return jsonify(message="Đơn hàng này đã được hủy trước đó.", order=order_schema_output.dump(order)), 400 # Bad request
    if order.status in [ORDER_STATUS_SHIPPED, ORDER_STATUS_DELIVERED] and current_user_role != 'admin': # Admin có thể có quyền đặc biệt
         abort(400, description=f"Không thể hủy đơn hàng đã '{order.status}'.")

    try:
        for item in order.items:
            phone = item.phone
            if phone:
                phone.stock_quantity += item.quantity
                # db.session.add(phone) # Không cần add nếu phone đã được tracked
        order.status = ORDER_STATUS_CANCELLED
        order.updated_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # app.logger.error(f"Lỗi hủy đơn hàng: {e}")
        abort(500, description=f"Lỗi máy chủ khi hủy đơn hàng. {str(e)}")

    return jsonify(message="Đơn hàng đã được hủy thành công.", order=order_schema_output.dump(order)), 200