# phone_management_api/app/__init__.py
import os
import json
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from marshmallow import ValidationError

from config import config_by_name
from .extensions import db, jwt, ma, cors

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={r"/*": {"origins": "*"}})

    from .models.user import User
    # Các model khác sẽ được SQLAlchemy nhận diện qua import trong schemas/routes hoặc relationships

    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        user = User.query.get(int(identity))
        return {"role": user.role} if user else {}

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
        return jsonify(error={"code": 404, "message": getattr(e, 'description', "The requested resource was not found.")}), 404
    
    @app.errorhandler(401)
    def handle_401_specifically(e):
        return jsonify(error={"code": 401, "message": getattr(e, 'description', "Authentication is required and has failed or has not yet been provided.")}), 401

    @app.errorhandler(403)
    def handle_403_specifically(e):
        return jsonify(error={"code": 403, "message": getattr(e, 'description', "You do not have permission to perform this action or access this resource.")}), 403
    
    @app.errorhandler(409)
    def handle_409_specifically(e):
        return jsonify(error={"code": 409, "message": getattr(e, 'description', "A conflict occurred with the current state of the target resource.")}), 409

    from .routes.auth_routes import auth_bp
    from .routes.phone_routes import phones_bp
    from .routes.cart_routes import cart_bp
    from .routes.order_routes import orders_bp # File này gây ra lỗi import

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(phones_bp, url_prefix='/phones')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(orders_bp, url_prefix='/orders')

    from .commands import init_db_command, create_admin_command, seed_db_command
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(seed_db_command)

    return app