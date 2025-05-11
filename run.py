# Anakonkai01/webtest/webtest-56020c9fc852ddd6495dc0e46baf7ebb8913bd4a/run.py
import os
from app import create_app # Import hàm factory từ package app

# Lấy tên cấu hình từ biến môi trường FLASK_ENV (ví dụ: 'dev', 'prod')
# Hoặc đặt mặc định là 'dev' nếu không có
config_name = os.getenv('FLASK_ENV', 'dev') # 'default' sẽ dùng DevelopmentConfig trong config.py

app = create_app(config_name)

if __name__ == '__main__':
    # host='0.0.0.0' cho phép truy cập từ các máy khác trong cùng mạng
    # debug=True sẽ được đặt bởi DevelopmentConfig nếu config_name là 'dev'
    app.run(host='0.0.0.0', port=5000) # Chỉ định port rõ ràng nếu cần