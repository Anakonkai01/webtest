# Anakonkai01/webtest/webtest-56020c9fc852ddd6495dc0e46baf7ebb8913bd4a/app/__init__.py
import os
import json
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

from config import config_by_name
from .extensions import db, jwt, ma, cors # Đảm bảo cors được import

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Khởi tạo Extensions
    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)

    # Cấu hình CORS chi tiết và rõ ràng
    cors.init_app(app, 
                  resources={r"/*": {"origins": "*"}}, # Cho phép tất cả origins trong môi trường dev. 
                                                      # Trong production, bạn nên giới hạn lại (ví dụ: "http://yourfrontenddomain.com")
                  methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"], # Bao gồm OPTIONS
                  allow_headers=["Authorization", "Content-Type"], # Các header được phép gửi từ client
                  expose_headers=["Content-Type", "Authorization"], # Các header client được phép đọc từ response
                  supports_credentials=True) # Nếu bạn sử dụng cookies/session (không cần thiết cho JWT qua Bearer token)

    # Import Models (chỉ cần User ở đây cho JWT, các model khác SQLAlchemy tự nhận diện)
    from .models.user import User

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = User.query.get(int(identity)) # identity là user.id (string)
        if user:
            # Thêm 'sub' (subject) claim là user_id, đã có sẵn trong identity
            # Thêm 'role' và 'username' để frontend dễ dàng sử dụng
            return {"role": user.role, "username": user.username} 
        return {}

    # Error Handlers (giữ nguyên hoặc cải tiến như đã thảo luận)
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        response = e.get_response()
        response.data = json.dumps({
            "error": {"code": e.code, "name": e.name, "message": e.description,}
        })
        response.content_type = "application/json"
        return response

    @app.errorhandler(ValidationError)
    def handle_marshmallow_validation(err):
        return jsonify(errors=err.messages), 400

    @app.errorhandler(404)
    def handle_404_specifically(e):
        message = getattr(e, 'description', "The requested resource was not found.")
        return jsonify(error={"code": 404, "message": message}), 404
    
    @app.errorhandler(401)
    def handle_401_specifically(e):
        message = getattr(e, 'description', "Authentication is required and has failed or has not yet been provided.")
        return jsonify(error={"code": 401, "message": message}), 401

    @app.errorhandler(403)
    def handle_403_specifically(e):
        message = getattr(e, 'description', "You do not have permission to perform this action or access this resource.")
        return jsonify(error={"code": 403, "message": message}), 403
    
    @app.errorhandler(409)
    def handle_409_specifically(e):
        message = getattr(e, 'description', "A conflict occurred with the current state of the target resource.")
        return jsonify(error={"code": 409, "message": message}), 409

    # Đăng ký Blueprints với strict_slashes=False để tránh redirect không cần thiết
    from .routes.auth_routes import auth_bp
    from .routes.phone_routes import phones_bp
    from .routes.cart_routes import cart_bp
    from .routes.order_routes import orders_bp

    app.register_blueprint(auth_bp, url_prefix='/auth', strict_slashes=False)
    app.register_blueprint(phones_bp, url_prefix='/phones', strict_slashes=False)
    app.register_blueprint(cart_bp, url_prefix='/cart', strict_slashes=False)
    app.register_blueprint(orders_bp, url_prefix='/orders', strict_slashes=False)

    # Đăng ký Commands
    from .commands import init_db_command, create_admin_command, seed_db_command
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_db_command)

    return app