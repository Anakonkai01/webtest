# phone_management_api/run.py
import os
from app import create_app # Import hàm factory từ package app

# Lấy tên cấu hình từ biến môi trường FLASK_ENV (ví dụ: 'dev', 'prod')
# Hoặc đặt mặc định là 'dev' nếu không có
config_name = os.getenv('FLASK_ENV', 'dev') # 'default' sẽ dùng DevelopmentConfig

app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0') # debug=True đã được set trong DevelopmentConfig