# phone_management_api/app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow 
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
ma = Marshmallow()
cors = CORS()