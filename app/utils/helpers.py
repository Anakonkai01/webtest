# phone_management_api/app/utils/helpers.py
from flask import abort
from app.extensions import db # Import db từ extensions
from app.models.user import User # Import model User
from app.models.cart import Cart # Import model Cart

def get_or_create_user_cart(user_id):
    """
    Hàm tiện ích để lấy hoặc tạo giỏ hàng cho người dùng (buyer).
    Commit session nếu cart mới được tạo.
    """
    user = User.query.get(user_id)
    if not user:
        # Lỗi này không nên xảy ra nếu user_id từ JWT là hợp lệ
        abort(404, description="Người dùng không tồn tại.")

    if user.role != 'buyer':
        abort(403, description="Chỉ người dùng có vai trò 'buyer' mới có thể có giỏ hàng.")

    cart = user.cart # Truy cập qua relationship 'cart' đã định nghĩa trên User model

    if not cart:
        cart = Cart(user_id=user_id, user=user) # Gán user object cho relationship
        db.session.add(cart)
        try:
            db.session.commit() # Commit ngay để cart có ID nếu các thao tác sau cần
        except Exception as e:
            db.session.rollback()
            # Ghi log lỗi ở đây nếu cần
            # app.logger.error(f"Lỗi khi tạo giỏ hàng cho user {user_id}: {e}")
            abort(500, description="Không thể tạo giỏ hàng cho người dùng.")
    return cart