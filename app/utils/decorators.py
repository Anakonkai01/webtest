from functools import wraps
from flask import request, abort, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def roles_required(*required_roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method == 'OPTIONS':
                return current_app.make_default_options_response()

            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get("role")

            if user_role not in required_roles:
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