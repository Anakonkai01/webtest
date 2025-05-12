# phone_management_api/app/utils/helpers.py
from flask import abort, current_app 
import traceback 

from app.extensions import db
from app.models.user import User
from app.models.cart import Cart 

def get_or_create_user_cart(user_id):

    current_app.logger.info(f"Gọi get_or_create_user_cart với user_id: {user_id} (kiểu: {type(user_id)})")

    try:
        processed_user_id = int(user_id)
    except ValueError:
        current_app.logger.error(f"user_id '{user_id}' không thể chuyển đổi sang integer.")
        abort(400, description="Định dạng user ID không hợp lệ.")

    user = User.query.get(processed_user_id)
    if not user:
        current_app.logger.error(f"Không tìm thấy User với ID {processed_user_id} trong CSDL.")
        abort(404, description=f"Người dùng với ID {processed_user_id} không tồn tại.")

    current_app.logger.info(f"Tìm thấy User: {user.username} (ID: {user.id}, Role: {user.role})")

    if user.role != 'buyer':
        current_app.logger.warning(f"User {user.username} (ID: {user.id}) có vai trò '{user.role}', không phải 'buyer'. Không thể có giỏ hàng.")
        abort(403, description="Chỉ người dùng có vai trò 'buyer' mới có thể có giỏ hàng.")


    cart = user.cart 

    if not cart:
        current_app.logger.info(f"Không tìm thấy giỏ hàng cho user ID {user.id} ({user.username}). Đang tạo giỏ hàng mới...")
        cart = Cart(user_id=user.id) 

        
        db.session.add(cart)
        try:
            current_app.logger.info(f"Chuẩn bị commit giỏ hàng mới cho user ID {user.id}...")
            db.session.commit() 
            current_app.logger.info(f"ĐÃ TẠO và commit giỏ hàng mới ID {cart.id} cho user ID {user.id} ({user.username}).")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"LỖI EXCEPTION khi commit giỏ hàng mới cho user ID {user.id} ({user.username}): {str(e)}")
            current_app.logger.error(traceback.format_exc()) 
            abort(500, description="Không thể tạo giỏ hàng cho người dùng do lỗi máy chủ.") 
    else:
        current_app.logger.info(f"Đã tìm thấy giỏ hàng ID {cart.id} cho user ID {user.id} ({user.username}).")
        
    return cart