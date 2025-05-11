# RESTful API Quản lý Điện thoại bằng Flask

Đây là một RESTful API được xây dựng bằng Flask và SQLite để quản lý thông tin điện thoại, giỏ hàng và đơn hàng. API hỗ trợ các thao tác CRUD (Create, Read, Update, Delete) và sử dụng JWT (JSON Web Tokens) để xác thực và phân quyền.

## Thông tin quản lý

-   **User**: `username`, `password`, `role` (buyer, seller, admin)
-   **Điện thoại (Phone)**: `model_name`, `manufacturer`, `price`, `stock_quantity`, `specifications`, `added_by_user_id`
-   **Giỏ hàng (Cart)**: Liên kết với user, chứa các `CartItem` (phone, quantity).
-   **Đơn hàng (Order)**: Liên kết với user, chứa các `OrderItem` (phone, quantity, price_at_purchase), `total_amount`, `status`, `shipping_address`.

## Yêu cầu

-   Python 3.7+
-   pip

## Cài đặt

1.  Clone repository (hoặc tạo thư mục dự án và các file như hướng dẫn).
2.  Đi đến thư mục dự án:
    ```bash
    cd your_project_directory # Ví dụ: cd webtest
    ```
3.  Tạo môi trường ảo (khuyến khích):
    ```bash
    python -m venv venv
    ```
4.  Kích hoạt môi trường ảo:
    -   Windows: `venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`
5.  Cài đặt các thư viện cần thiết từ `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```

## Thiết lập ban đầu (Chỉ chạy lần đầu)

1.  **Thiết lập biến môi trường (Tuỳ chọn cho development, Quan trọng cho production):**
    * `FLASK_ENV`: Đặt là `dev` cho development, `prod` cho production. Mặc định là `dev` nếu không đặt.
    * `SECRET_KEY`: Một chuỗi bí mật dài và ngẫu nhiên cho Flask và các extension.
    * `JWT_SECRET_KEY`: Một chuỗi bí mật khác cho JWT (trong production nên đặt qua biến môi trường).
    * `DATABASE_URL` (cho production), `DEV_DATABASE_URL`, `TEST_DATABASE_URL`: URL kết nối CSDL.
    Ví dụ cho development (có thể không cần nếu dùng giá trị mặc định trong `config.py`):
    ```bash
    # Linux/macOS
    export FLASK_ENV=dev
    export SECRET_KEY='your-flask-secret-key'
    export JWT_SECRET_KEY='your-jwt-secret-key-for-dev' 
    # Windows (cmd)
    set FLASK_ENV=dev
    set SECRET_KEY="your-flask-secret-key"
    set JWT_SECRET_KEY="your-jwt-secret-key-for-dev"
    ```

2.  **Khởi tạo cơ sở dữ liệu:**
    Mở terminal trong thư mục gốc của dự án (nơi có `run.py`) và chạy:
    ```bash
    flask init-db
    ```
    Lệnh này sẽ tạo các bảng trong CSDL dựa theo models.

3.  **Tạo người dùng admin (Tuỳ chọn):**
    ```bash
    flask create-admin youradminusername youradminpassword
    ```

4.  **Tạo dữ liệu mẫu (Tuỳ chọn):**
    ```bash
    flask seed-db
    ```
    Để tạo dữ liệu mẫu mà không xóa dữ liệu hiện có, dùng:
    ```bash
    flask seed-db --no-clear
    ```

## Chạy ứng dụng

Sau khi cài đặt và thiết lập, bạn có thể chạy server Flask:
```bash
python run.py