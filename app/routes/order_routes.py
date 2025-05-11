# phone_management_api/app/routes/order_routes.py
from flask import Blueprint, request, jsonify, abort, current_app, url_for
from sqlalchemy import desc, asc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime

from app.extensions import db
from app.models.order import (
    Order, OrderItem, ALLOWED_ORDER_STATUSES, ORDER_STATUS_PENDING, 
    ORDER_STATUS_CANCELLED, ORDER_STATUS_SHIPPED, ORDER_STATUS_DELIVERED, 
    ORDER_STATUS_PROCESSING, ORDER_STATUS_FAILED # Thêm FAILED nếu có
)
from app.models.cart import Cart, CartItem
from app.models.phone import Phone
from app.schemas import (
    order_schema_output, orders_schema_output, 
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

    if not cart or cart.is_empty():
        abort(400, description="Giỏ hàng trống. Không thể tạo đơn hàng.")

    json_data = request.get_json()
    order_input_data = order_create_schema_input.load(json_data if json_data else {})
    shipping_address = order_input_data['shipping_address']

    items_to_order_details = []
    calculated_total_amount = 0.0 # Sử dụng float cho tính toán tiền tệ

    try:
        # Bắt đầu một transaction, tất cả các thao tác CSDL phải thành công hoặc rollback hết
        with db.session.begin_nested(): # Hoặc không dùng nested nếu CSDL không hỗ trợ tốt, xử lý rollback thủ công
            for cart_item in cart.items.all():
                phone = Phone.query.get(cart_item.phone_id) # Lấy thông tin sản phẩm mới nhất

                if not phone:
                    # Không nên abort ở đây nếu đang trong transaction, raise lỗi để bắt bên ngoài
                    raise ValueError(f"Sản phẩm ID {cart_item.phone_id} trong giỏ không còn tồn tại.") 
                
                if phone.stock_quantity < cart_item.quantity:
                    raise ValueError(f"Không đủ tồn kho cho '{phone.model_name}'. Yêu cầu: {cart_item.quantity}, còn: {phone.stock_quantity}.")

                items_to_order_details.append({
                    "phone_model_instance": phone, # Giữ instance để cập nhật stock
                    "quantity": cart_item.quantity,
                    "price_at_purchase": float(phone.price) # Đảm bảo là float
                })
                calculated_total_amount += float(cart_item.quantity) * float(phone.price)
            
            calculated_total_amount = round(calculated_total_amount, 2)

            new_order = Order(
                user_id=current_user_id,
                total_amount=calculated_total_amount,
                status=ORDER_STATUS_PENDING,
                shipping_address=shipping_address
            )
            db.session.add(new_order)
            db.session.flush() 

            for item_detail in items_to_order_details:
                phone_to_update = item_detail["phone_model_instance"]
                order_item = OrderItem(
                    order_id=new_order.id,
                    phone_id=phone_to_update.id,
                    quantity=item_detail["quantity"],
                    price_at_purchase=item_detail["price_at_purchase"]
                )
                db.session.add(order_item)
                phone_to_update.stock_quantity -= item_detail["quantity"]
                db.session.add(phone_to_update)

            CartItem.query.filter_by(cart_id=cart.id).delete(synchronize_session=False) # Thêm synchronize_session
            cart.updated_at = datetime.utcnow()
        
        db.session.commit() # Commit transaction chính
    except ValueError as ve: # Bắt lỗi value từ kiểm tra logic
        db.session.rollback()
        abort(400, description=str(ve))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi nghiêm trọng khi tạo đơn hàng cho user {current_user_id}: {str(e)}")
        abort(500, description="Lỗi máy chủ khi tạo đơn hàng. Vui lòng thử lại.")

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
        if status_filter not in ALLOWED_ORDER_STATUSES:
            abort(400, description=f"Trạng thái lọc '{status_filter}' không hợp lệ.")
        query = query.filter(Order.status == status_filter)

    sort_by = request.args.get('sort_by', 'created_at')
    order_dir = request.args.get('order', 'desc').lower()
    order_sort_columns = {
        'created_at': Order.created_at, 'updated_at': Order.updated_at,
        'total_amount': Order.total_amount, 'status': Order.status, 'id': Order.id
    }
    sort_column = order_sort_columns.get(sort_by)
    if not sort_column: 
        abort(400, description=f"Trường sắp xếp đơn hàng '{sort_by}' không hợp lệ.")
    if order_dir not in ['asc', 'desc']: 
        abort(400, description="Thứ tự sắp xếp không hợp lệ, chỉ chấp nhận 'asc' hoặc 'desc'.")
    query = query.order_by(desc(sort_column) if order_dir == 'desc' else asc(sort_column))

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', current_app.config.get('DEFAULT_PER_PAGE', 10), type=int)
        if page <= 0: abort(400, description="'page' phải là số nguyên dương.")
        if per_page <= 0: abort(400, description="'per_page' phải là số nguyên dương.")
        if per_page > current_app.config.get('MAX_PER_PAGE', 100):
            per_page = current_app.config.get('MAX_PER_PAGE', 100)
    except: 
        abort(400, description="'page' và 'per_page' phải là số nguyên hợp lệ.")

    paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    current_args_display = request.args.copy()
    filters_applied = {k: v for k, v in current_args_display.items() if k != 'page'}
    next_url, prev_url = None, None
    if paginated_orders.has_next:
        next_params = current_args_display.copy(); next_params['page'] = paginated_orders.next_num
        next_url = url_for(request.endpoint, _external=False, **next_params)
    if paginated_orders.has_prev:
        prev_params = current_args_display.copy(); prev_params['page'] = paginated_orders.prev_num
        prev_url = url_for(request.endpoint, _external=False, **prev_params)

    return jsonify({
        "data": orders_schema_output.dump(paginated_orders.items),
        "meta": {"page": paginated_orders.page, "per_page": paginated_orders.per_page,
                 "total_pages": paginated_orders.pages, "total_items": paginated_orders.total,
                 "next_page_url": next_url, "prev_page_url": prev_url, 
                 "filters_applied": filters_applied }
    }), 200

@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'buyer' and order.user_id != current_user_id:
        abort(403, description="Bạn không có quyền xem chi tiết đơn hàng này.")
    elif current_user_role == 'seller':
        is_seller_order = OrderItem.query.join(Phone, OrderItem.phone_id == Phone.id)\
                                     .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first()
        if not is_seller_order:
            abort(403, description="Đơn hàng này không chứa sản phẩm nào của bạn.")
    
    return jsonify(order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@seller_or_admin_required
def update_order_status_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'seller':
        is_seller_order = OrderItem.query.join(Phone, OrderItem.phone_id == Phone.id)\
                                     .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id).first()
        if not is_seller_order:
            abort(403, description="Bạn không có quyền cập nhật trạng thái cho đơn hàng này.")

    json_data = request.get_json()
    if not json_data: 
        abort(400, description="Không có dữ liệu đầu vào để cập nhật trạng thái.")
    
    data = order_status_update_schema_input.load(json_data)
    new_status = data['status']

    if order.status == ORDER_STATUS_DELIVERED :
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã được giao thành công.")
    if order.status == ORDER_STATUS_CANCELLED :
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã bị hủy.")

    if current_user_role == 'seller' and new_status not in [ORDER_STATUS_PROCESSING, ORDER_STATUS_SHIPPED, order.status]:
         abort(403, description=f"Người bán không được phép cập nhật đơn hàng sang trạng thái '{new_status}'.")
    
    # QUAN TRỌNG: Xử lý hoàn kho nếu admin/seller cập nhật status thành CANCELLED qua endpoint này
    stock_reverted_message = ""
    if new_status == ORDER_STATUS_CANCELLED and order.status not in [ORDER_STATUS_CANCELLED, ORDER_STATUS_DELIVERED, ORDER_STATUS_FAILED]:
        try:
            with db.session.begin_nested(): # Đảm bảo hoàn kho và cập nhật status là một khối
                for item in order.items:
                    phone = item.phone
                    if phone:
                        phone.stock_quantity += item.quantity
                        db.session.add(phone)
                order.status = new_status
                order.updated_at = datetime.utcnow()
                stock_reverted_message = " Tồn kho đã được hoàn lại."
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Lỗi khi hoàn kho và hủy đơn {order_id} qua update status: {str(e)}")
            abort(500, description="Lỗi khi cập nhật trạng thái và hoàn kho.")
    else:
        order.status = new_status
        order.updated_at = datetime.utcnow()
        db.session.commit()

    return jsonify(message=f"Cập nhật trạng thái đơn hàng thành công.{stock_reverted_message}", 
                   order=order_schema_output.dump(order)), 200

@orders_bp.route('/<int:order_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_order_route(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    
    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    can_cancel_globally = False
    
    if current_user_role == 'admin':
        can_cancel_globally = True
        # Admin có thể hủy nhiều trạng thái hơn, nhưng vẫn nên có giới hạn
        if order.status in [ORDER_STATUS_DELIVERED]: # Ví dụ: admin không hủy đơn đã giao trừ khi có quy trình đặc biệt
            abort(400, description=f"Admin không thể hủy đơn hàng đã ở trạng thái '{order.status}' qua endpoint này. Sử dụng quy trình đặc biệt nếu cần.")
            
    elif current_user_role == 'buyer' and order.user_id == current_user_id:
        if order.status in [ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING]: 
            can_cancel_globally = True
        else:
            abort(403, description=f"Bạn không thể hủy đơn hàng này vì nó đang ở trạng thái '{order.status}'.")
    
    if not can_cancel_globally:
         abort(403, description="Bạn không có quyền hủy đơn hàng này hoặc đơn hàng không ở trạng thái cho phép hủy.")

    if order.status == ORDER_STATUS_CANCELLED:
        return jsonify(message="Đơn hàng này đã được hủy trước đó.", order=order_schema_output.dump(order)), 400
    
    try:
        with db.session.begin_nested():
            for item in order.items:
                phone = item.phone
                if phone:
                    phone.stock_quantity += item.quantity
                    db.session.add(phone)
            
            order.status = ORDER_STATUS_CANCELLED
            order.updated_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi hủy đơn hàng {order_id}: {str(e)}")
        abort(500, description=f"Lỗi máy chủ khi cố gắng hủy đơn hàng. Thay đổi đã được hoàn tác.")

    return jsonify(message="Đơn hàng đã được hủy thành công và tồn kho đã được cập nhật.", order=order_schema_output.dump(order)), 200