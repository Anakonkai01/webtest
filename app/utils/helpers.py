# phone_management_api/app/utils/helpers.py
from flask import abort, current_app # Thêm current_app
import traceback # Thêm traceback để log lỗi chi tiết

from app.extensions import db
from app.models.user import User # Import model User
from app.models.cart import Cart # Import model Cart

def get_or_create_user_cart(user_id):
    """
    Hàm tiện ích để lấy hoặc tạo giỏ hàng cho người dùng (buyer).
    Commit session nếu cart mới được tạo.
    """
    # Log lúc bắt đầu hàm và kiểu dữ liệu của user_id
    current_app.logger.info(f"Gọi get_or_create_user_cart với user_id: {user_id} (kiểu: {type(user_id)})")

    # Đảm bảo user_id là integer nếu nó đến từ JWT (thường là string)
    try:
        processed_user_id = int(user_id)
    except ValueError:
        current_app.logger.error(f"user_id '{user_id}' không thể chuyển đổi sang integer.")
        abort(400, description="Định dạng user ID không hợp lệ.")

    user = User.query.get(processed_user_id)
    if not user:
        current_app.logger.error(f"Không tìm thấy User với ID {processed_user_id} trong CSDL.")
        # Lỗi này không nên xảy ra nếu user_id từ JWT là hợp lệ và user tồn tại
        abort(404, description=f"Người dùng với ID {processed_user_id} không tồn tại.")

    current_app.logger.info(f"Tìm thấy User: {user.username} (ID: {user.id}, Role: {user.role})")

    if user.role != 'buyer':
        current_app.logger.warning(f"User {user.username} (ID: {user.id}) có vai trò '{user.role}', không phải 'buyer'. Không thể có giỏ hàng.")
        abort(403, description="Chỉ người dùng có vai trò 'buyer' mới có thể có giỏ hàng.")

    # Truy cập giỏ hàng qua relationship từ đối tượng User
    # SQLAlchemy sẽ tự động thực hiện truy vấn nếu cần
    cart = user.cart 

    if not cart:
        current_app.logger.info(f"Không tìm thấy giỏ hàng cho user ID {user.id} ({user.username}). Đang tạo giỏ hàng mới...")
        # Tạo giỏ hàng mới và liên kết với user_id
        cart = Cart(user_id=user.id) 
        # Không cần gán cart.user = user một cách tường minh ở đây
        # vì backref hoặc back_populates và user_id đã đủ để SQLAlchemy thiết lập mối quan hệ.
        # Tuy nhiên, nếu bạn muốn tường minh, có thể thêm: cart.user = user
        
        db.session.add(cart)
        try:
            current_app.logger.info(f"Chuẩn bị commit giỏ hàng mới cho user ID {user.id}...")
            db.session.commit() # CỐ GẮNG COMMIT Ở ĐÂY
            current_app.logger.info(f"ĐÃ TẠO và commit giỏ hàng mới ID {cart.id} cho user ID {user.id} ({user.username}).")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"LỖI EXCEPTION khi commit giỏ hàng mới cho user ID {user.id} ({user.username}): {str(e)}")
            current_app.logger.error(traceback.format_exc()) # Log traceback đầy đủ để biết chi tiết lỗi CSDL
            abort(500, description="Không thể tạo giỏ hàng cho người dùng do lỗi máy chủ.") # Thông báo lỗi chung hơn
    else:
        current_app.logger.info(f"Đã tìm thấy giỏ hàng ID {cart.id} cho user ID {user.id} ({user.username}).")
        
    return cart