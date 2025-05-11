# phone_management_api/app/schemas/user_schema.py
from marshmallow import fields, validate # Vẫn cần cho validate và fields cơ bản
from app.extensions import ma # Import Flask-Marshmallow instance (ma)
from app.models.user import User # Import model User

# UserRegisterSchema: Dùng để validate dữ liệu đầu vào khi đăng ký.
# Không trực tiếp serialize từ model User theo cách tự động hoàn toàn.
class UserRegisterSchema(ma.Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80, error="Tên người dùng phải từ 3 đến 80 ký tự.")
    )
    password = fields.Str(
        required=True,
        load_only=True,  # Quan trọng: password chỉ dùng để load (đọc vào), không bao giờ dump (xuất ra)
        validate=validate.Length(min=6, max=128, error="Mật khẩu phải từ 6 đến 128 ký tự.")
    )
    role = fields.Str(
        validate=validate.OneOf(
            User.REGISTRATION_ALLOWED_ROLES, # Lấy từ hằng số trong model User
            error=f"Vai trò không hợp lệ. Chỉ chấp nhận: {', '.join(User.REGISTRATION_ALLOWED_ROLES)}."
        ),
        load_default='buyer' # Giá trị mặc định nếu không được cung cấp khi load
    )

# UserSchema: Dùng để serialize thông tin User (output) ra JSON.
# SQLAlchemyAutoSchema sẽ tự động tạo các trường dựa trên model User.
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User # Liên kết schema này với model User
        load_instance = True # Khi deserialize, sẽ tạo một instance của model User
        # exclude = ("password_hash",) # Quan trọng: Loại trừ password_hash để không bị lộ ra ngoài API
                                     # Hoặc chỉ định fields cụ thể như bên dưới.

        # Chỉ định các trường bạn muốn hiển thị trong output JSON.
        # Nếu không có dòng này, tất cả các trường trong model User (trừ những trường trong 'exclude') sẽ được hiển thị.
        fields = ("id", "username", "role")

    # Nếu bạn muốn đảm bảo một số trường luôn là dump_only (chỉ xuất, không đọc vào khi update/create qua schema này)
    # id = ma.auto_field(dump_only=True) # SQLAlchemyAutoSchema thường tự xử lý id là dump_only
    # username = ma.auto_field(dump_only=True)
    # role = ma.auto_field(dump_only=True)
    # Với fields = ("id", "username", "role"), chúng mặc định là dump_only do không có required=True
    # và không có load_only=True. SQLAlchemyAutoSchema đủ thông minh cho trường hợp này.