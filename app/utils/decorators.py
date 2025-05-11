# phone_management_api/app/utils/decorators.py
from functools import wraps
from flask import jsonify, abort # Thêm abort
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def roles_required(*required_roles):
    """
    Decorator để yêu cầu người dùng phải có một trong các vai trò được chỉ định.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request() # Đảm bảo JWT hợp lệ có trong request
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role not in required_roles:
                # Sử dụng abort để kích hoạt error handler chung cho 403
                abort(403, description=f"Quyền truy cập bị từ chối. Yêu cầu vai trò: {', '.join(required_roles)}.")
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def admin_required(fn):
    return roles_required('admin')(fn)

def seller_or_admin_required(fn):
    return roles_required('seller', 'admin')(fn)

def buyer_required(fn):
    return roles_required('buyer')(fn)