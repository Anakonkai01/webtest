# phone_management_api/app/routes/auth_routes.py
from flask import Blueprint, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.user import User
from app.schemas import user_register_schema, user_schema

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/register', methods=['POST'])
def register_user():
    json_data = request.get_json()
    if not json_data:
        abort(400, description="Không có dữ liệu đầu vào. Vui lòng cung cấp JSON body.")

    data = user_register_schema.load(json_data) 

    username = data['username']
    password = data['password']
    role = data['role']

    if role not in User.REGISTRATION_ALLOWED_ROLES:
        abort(400, description=f"Vai trò '{role}' không được phép tự đăng ký.")
    
    if role == 'admin':
        abort(403, description="Không thể tự đăng ký với vai trò 'admin' qua API công khai.")

    if User.query.filter_by(username=username).first():
        abort(409, description="Tên người dùng đã tồn tại.")

    new_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    
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
        access_token = create_access_token(identity=str(user.id))
        return jsonify(access_token=access_token), 200
    else:
        abort(401, description="Sai tên người dùng hoặc mật khẩu.")