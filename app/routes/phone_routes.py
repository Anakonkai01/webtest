# phone_management_api/app/routes/phone_routes.py
from flask import Blueprint, request, jsonify, current_app, url_for, abort
from sqlalchemy import asc, desc
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from marshmallow import ValidationError # <<< SỬA Ở ĐÂY

from app.extensions import db
from app.models.phone import Phone
# Bỏ ValidationError khỏi import này
from app.schemas import phone_schema, phones_schema 
from app.utils.decorators import seller_or_admin_required

phones_bp = Blueprint('phones_bp', __name__)

# ... (Route handle_get_or_options_phones giữ nguyên) ...
@phones_bp.route('/', methods=['GET', 'OPTIONS'])
def handle_get_or_options_phones():
    if request.method == 'OPTIONS':
        return jsonify(success=True), 200

    query = Phone.query
    manufacturer = request.args.get('manufacturer')
    if manufacturer:
        query = query.filter(Phone.manufacturer.ilike(f"%{manufacturer}%"))
    model_name_contains = request.args.get('model_name_contains')
    if model_name_contains:
        query = query.filter(Phone.model_name.ilike(f"%{model_name_contains}%"))
    price_min_val = None
    try:
        price_min_str = request.args.get('price_min')
        if price_min_str:
            price_min_val = float(price_min_str)
            if price_min_val < 0: 
                abort(400, description="Giá trị 'price_min' không được âm.")
            query = query.filter(Phone.price >= price_min_val)
        
        price_max_str = request.args.get('price_max')
        if price_max_str:
            price_max_val = float(price_max_str)
            if price_max_val < 0: 
                abort(400, description="Giá trị 'price_max' không được âm.")
            if price_min_val is not None and price_max_val < price_min_val:
                 abort(400, description="'price_max' phải lớn hơn hoặc bằng 'price_min'.")
            query = query.filter(Phone.price <= price_max_val)
    except ValueError:
        abort(400, description="'price_min' hoặc 'price_max' phải là một số hợp lệ.")

    sort_by_param = request.args.get('sort_by', 'id').lower()
    order_param = request.args.get('order', 'asc').lower()

    allowed_sort_fields = {
        'id': Phone.id, 'model_name': Phone.model_name,
        'manufacturer': Phone.manufacturer, 'price': Phone.price,
        'stock_quantity': Phone.stock_quantity
    }
    sort_column = allowed_sort_fields.get(sort_by_param)
    if sort_column is None:
        abort(400, description=f"Trường sắp xếp không hợp lệ: '{sort_by_param}'. Các trường hợp lệ: {', '.join(allowed_sort_fields.keys())}")
    
    if order_param not in ['asc', 'desc']:
        abort(400, description="Tham số 'order' không hợp lệ. Chỉ chấp nhận 'asc' hoặc 'desc'.")
    
    query = query.order_by(desc(sort_column) if order_param == 'desc' else asc(sort_column))

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', current_app.config.get('DEFAULT_PER_PAGE', 9), type=int)
        if page <= 0: abort(400, description="'page' phải là số nguyên dương.")
        if per_page <= 0: abort(400, description="'per_page' phải là số nguyên dương.")
        if per_page > current_app.config.get('MAX_PER_PAGE', 100):
            per_page = current_app.config.get('MAX_PER_PAGE', 100)
    except ValueError: 
         abort(400, description="'page' và 'per_page' phải là số nguyên hợp lệ.")

    paginated_phones = query.paginate(page=page, per_page=per_page, error_out=False)
    current_args = request.args.copy()
    filters_applied_display = {k: v for k, v in current_args.items() if k != 'page'}
    next_url, prev_url = None, None
    base_url_for_pagination = url_for(request.endpoint, _external=False)

    if paginated_phones.has_next:
        next_url_params = current_args.copy()
        next_url_params['page'] = paginated_phones.next_num
        next_url = f"{base_url_for_pagination}?{('&'.join([f'{k}={v}' for k, v in next_url_params.items()]))}"
    if paginated_phones.has_prev:
        prev_url_params = current_args.copy()
        prev_url_params['page'] = paginated_phones.prev_num
        prev_url = f"{base_url_for_pagination}?{('&'.join([f'{k}={v}' for k, v in prev_url_params.items()]))}"

    return jsonify({
        "data": phones_schema.dump(paginated_phones.items),
        "meta": {
            "page": paginated_phones.page, 
            "per_page": paginated_phones.per_page,
            "total_pages": paginated_phones.pages, 
            "total_items": paginated_phones.total,
            "next_page_url": next_url, 
            "prev_page_url": prev_url,
            "filters_applied": filters_applied_display
        }
    }), 200

@phones_bp.route('/', methods=['POST'])
@jwt_required()
@seller_or_admin_required
def create_phone_route():
    current_user_id = int(get_jwt_identity())
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu đầu vào.")
    try:
        data = phone_schema.load(json_data) 
    except ValidationError as err: # Bắt lỗi từ marshmallow
        abort(400, description=err.messages)

    new_phone = Phone(
        model_name=data['model_name'],
        manufacturer=data['manufacturer'],
        price=data['price'],
        stock_quantity=data['stock_quantity'],
        specifications=data.get('specifications'), 
        user_id=current_user_id
    )
    try:
        db.session.add(new_phone)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi lưu sản phẩm vào CSDL: {str(e)}")
        abort(500, description="Lỗi máy chủ khi lưu sản phẩm.")
    return jsonify(phone_schema.dump(new_phone)), 201

# ... (Các route get_phone_route, update_phone_route, delete_phone_route cũng cần sửa tương tự nếu có dùng .load() và bắt ValidationError)

@phones_bp.route('/<int:phone_id>', methods=['GET'])
def get_phone_route(phone_id):
    phone = Phone.query.get_or_404(phone_id, description=f"Không tìm thấy điện thoại với ID: {phone_id}")
    return jsonify(phone_schema.dump(phone)), 200

@phones_bp.route('/<int:phone_id>', methods=['PUT', 'OPTIONS']) 
@jwt_required()
def update_phone_route(phone_id):
    if request.method == 'OPTIONS':
        return jsonify(success=True) 

    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")
    
    phone = Phone.query.get_or_404(phone_id, description=f"Không tìm thấy điện thoại với ID: {phone_id} để cập nhật.")

    can_update = False
    if current_user_role == 'admin':
        can_update = True
    elif current_user_role == 'seller' and phone.user_id == current_user_id:
        can_update = True

    if not can_update:
        abort(403, description="Bạn không có quyền cập nhật thông tin điện thoại này.")

    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu được cung cấp để cập nhật.")
    try:
        validated_data = phone_schema.load(json_data, partial=True, unknown='EXCLUDE')
    except ValidationError as err: # Bắt lỗi từ marshmallow
        abort(400, description=err.messages)
    if not validated_data:
         abort(400, description="Không có trường hợp lệ nào được cung cấp để cập nhật.")
    updated_fields_count = 0
    for key, value in validated_data.items():
        if hasattr(phone, key) and getattr(phone, key) != value:
            if key == 'user_id' or key == 'added_by_user_id': 
                continue
            setattr(phone, key, value)
            updated_fields_count +=1
    if updated_fields_count > 0:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Lỗi khi cập nhật sản phẩm ID {phone_id}: {str(e)}")
            abort(500, description="Lỗi máy chủ khi cập nhật sản phẩm.")
        return jsonify(phone_schema.dump(phone)), 200
    else:
        return jsonify(message="Không có thay đổi nào được thực hiện.", data=phone_schema.dump(phone)), 200


@phones_bp.route('/<int:phone_id>', methods=['DELETE', 'OPTIONS']) 
@jwt_required()
def delete_phone_route(phone_id):
    if request.method == 'OPTIONS':
        return jsonify(success=True)

    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")

    phone = Phone.query.get_or_404(phone_id, description=f"Không tìm thấy điện thoại với ID: {phone_id} để xóa.")

    can_delete = False
    if current_user_role == 'admin':
        can_delete = True
    elif current_user_role == 'seller' and phone.user_id == current_user_id:
        can_delete = True

    if not can_delete:
        abort(403, description="Bạn không có quyền xóa điện thoại này.")
    
    try:
        db.session.delete(phone)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi xóa sản phẩm ID {phone_id}: {str(e)}")
        abort(500, description="Lỗi máy chủ khi xóa sản phẩm.")
    return jsonify(message="Đã xóa điện thoại thành công."), 200