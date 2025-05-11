# phone_management_api/app/schemas/user_schema.py
from marshmallow import fields, validate
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
        load_instance = True
        fields = ("id", "username", "role")