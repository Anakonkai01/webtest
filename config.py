# phone_management_api/config.py
import os
from datetime import timedelta

# Xác định thư mục gốc của dự án
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Cấu hình cơ sở."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-default-super-secret-key-please-change' # THAY ĐỔI KEY NÀY!
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    # Thêm các cấu hình chung khác nếu cần

class DevelopmentConfig(Config):
    """Cấu hình cho môi trường phát triển."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database_dev.db') # Đổi tên CSDL cho dev
    # Có thể dùng JWT_SECRET_KEY khác cho dev
    JWT_SECRET_KEY = 'dev-jwt-secret-key'


class TestingConfig(Config):
    """Cấu hình cho môi trường testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database_test.db') # CSDL riêng cho test
    JWT_SECRET_KEY = 'test-jwt-secret-key'
    WTF_CSRF_ENABLED = False # Tắt CSRF cho test form nếu dùng WTForms

class ProductionConfig(Config):
    """Cấu hình cho môi trường production."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'database_prod.db') # CSDL cho production
    # Đảm bảo JWT_SECRET_KEY được đặt qua biến môi trường trong production
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') # Phải được đặt trong môi trường

# Dictionary để dễ dàng truy cập các lớp cấu hình
config_by_name = dict(
    dev=DevelopmentConfig,
    test=TestingConfig,
    prod=ProductionConfig,
    default=DevelopmentConfig # Cấu hình mặc định nếu FLASK_ENV không được đặt
)