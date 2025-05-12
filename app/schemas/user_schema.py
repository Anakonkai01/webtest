# app/schemas/user_schema.py
from marshmallow import fields, validate, post_dump # Sử dụng post_dump để linh hoạt hơn
from flask import url_for
from app.extensions import ma
from app.models.user import User

class UserRegisterSchema(ma.Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80, error="Tên người dùng phải từ 3 đến 80 ký tự.")
    )
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6, max=128, error="Mật khẩu phải từ 6 đến 128 ký tự.")
    )
    role = fields.Str(
        validate=validate.OneOf(
            User.REGISTRATION_ALLOWED_ROLES,
            error=f"Vai trò không hợp lệ. Chỉ chấp nhận: {', '.join(User.REGISTRATION_ALLOWED_ROLES)}."
        ),
        load_default='buyer'
    )

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True # Hoặc False tùy nhu cầu
        # fields = ("id", "username", "role", "_links") # Bỏ fields để lấy tất cả, hoặc thêm _links

    # id, username, role sẽ được auto_field từ model

    @post_dump
    def add_user_links(self, data, **kwargs):
        user_id = data.get('id')
        user_role = data.get('role') # Lấy role từ data đã dump

        if user_id is None:
            return data

        links = {
            "self": {
                # Hiện tại chưa có route GET /users/{id}, nếu có thì dùng url_for ở đây
                # Ví dụ: "href": url_for('auth_bp.get_user_profile', user_id=user_id, _external=False),
                "href": f"/users/{user_id}", # Tạm thời để placeholder nếu chưa có route
                "method": "GET",
                "description": "Thông tin chi tiết của người dùng này (cần endpoint)."
            }
        }

        if user_role == 'buyer':
            links["cart"] = {
                "href": url_for('cart_bp.view_cart_route', _external=False),
                "method": "GET",
                "description": "Xem giỏ hàng của người mua này."
            }
            links["orders"] = {
                "href": url_for('orders_bp.get_orders_list_route', _external=False), # Sẽ tự filter theo buyer ID trong route
                "method": "GET",
                "description": "Xem danh sách đơn hàng của người mua này."
            }
        elif user_role == 'seller':
            links["products_listed"] = {
                # API GET /phones/ có thể nhận user_id để lọc sản phẩm của seller đó
                # Hoặc tạo một endpoint riêng /users/<id>/phones
                "href": url_for('phones_bp.handle_get_or_options_phones', user_id=user_id, _external=False), # Truyền user_id để route phones có thể lọc
                "method": "GET",
                "description": "Xem danh sách sản phẩm do người bán này đăng tải."
            }
            links["orders_to_manage"] = { # Seller xem các đơn hàng chứa sản phẩm của họ
                 "href": url_for('orders_bp.get_orders_list_route', _external=False), # Route này đã có logic cho seller
                 "method": "GET",
                 "description": "Xem các đơn hàng chứa sản phẩm của người bán này."
            }
        elif user_role == 'admin':
            # Admin có thể có các link đặc biệt khác, ví dụ link đến trang quản trị user
            links["all_users"] = {"href": "/admin/users", "method": "GET", "description": "Quản lý tất cả người dùng (cần endpoint)."}
            links["all_products"] = {"href": url_for('phones_bp.handle_get_or_options_phones', _external=False), "method": "GET"}
            links["all_orders"] = {"href": url_for('orders_bp.get_orders_list_route', _external=False), "method": "GET"}


        data['_links'] = links
        return data