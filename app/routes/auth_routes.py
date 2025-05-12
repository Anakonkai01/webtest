# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.schemas import user_register_schema, user_schema # user_schema will add _links

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu đầu vào. Vui lòng cung cấp JSON body.")

    # Validation and loading using schema
    try:
        data = user_register_schema.load(json_data)
    except Exception as err: # Catch Marshmallow's ValidationError specifically if possible
        current_app.logger.warning(f"Lỗi validation khi đăng ký: {err}")
        abort(400, description=str(err)) # Or err.messages if ValidationError

    username = data['username']
    password = data['password']
    role = data['role']

    # Role validation against allowed roles in model
    if role not in User.REGISTRATION_ALLOWED_ROLES:
        abort(400, description=f"Vai trò '{role}' không được phép tự đăng ký.")
    
    # Prevent self-registration as admin via public API
    if role == 'admin':
        abort(403, description="Không thể tự đăng ký với vai trò 'admin' qua API công khai.")

    if User.query.filter_by(username=username).first():
        abort(409, description="Tên người dùng đã tồn tại.")

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    try:
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi CSDL khi đăng ký user '{username}': {str(e)}")
        abort(500, description="Lỗi máy chủ nội bộ khi tạo tài khoản.")
    
    # user_schema.dump(new_user) will include HATEOAS links
    return jsonify(user_schema.dump(new_user)), 201

@auth_bp.route('/login', methods=['POST'])
def login_user():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu đầu vào. Vui lòng cung cấp JSON body.")

    username = json_data.get('username')
    password = json_data.get('password')

    if not username or not password:
        abort(400, description="Thiếu tên người dùng hoặc mật khẩu.")

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        # Identity can be user.id (stringified)
        access_token = create_access_token(identity=str(user.id))
        
        # Return user data (with HATEOAS links) along with the token
        user_data_with_links = user_schema.dump(user)
        
        return jsonify({
            "message": "Đăng nhập thành công!",
            "access_token": access_token,
            "user": user_data_with_links  # User object now includes _links
        }), 200
    else:
        abort(401, description="Sai tên người dùng hoặc mật khẩu.")

# Example of a protected route to get current user's profile (demonstrates using UserSchema)
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(int(current_user_id))
    if not user:
        abort(404, description="Không tìm thấy người dùng.")
    # user_schema.dump(user) will include HATEOAS links defined in UserSchema
    return jsonify(user_schema.dump(user)), 200