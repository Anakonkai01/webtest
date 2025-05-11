# phone_management_api/app/schemas/user_schema.py
from marshmallow import Schema, fields, validate
from app.models.user import User # Import model User để tham chiếu User.REGISTRATION_ALLOWED_ROLES

class UserRegisterSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80, error="Tên người dùng phải từ 3 đến 80 ký tự."))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128, error="Mật khẩu phải từ 6 đến 128 ký tự."))
    role = fields.Str(
        validate=validate.OneOf(User.REGISTRATION_ALLOWED_ROLES, error=f"Vai trò không hợp lệ. Chỉ chấp nhận: {', '.join(User.REGISTRATION_ALLOWED_ROLES)}."),
        load_default='buyer'
    )

class UserSchema(Schema): # Dùng để serialize thông tin User (output)
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)