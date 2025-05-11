# RESTful API Quản lý Điện thoại bằng Flask

Đây là một RESTful API đơn giản được xây dựng bằng Flask và SQLite để quản lý thông tin điện thoại. API hỗ trợ các thao tác CRUD (Create, Read, Update, Delete) và sử dụng JWT (JSON Web Tokens) để xác thực.

## Thông tin quản lý

Mỗi điện thoại có các thông tin sau:
- `model_name`: Tên model (chuỗi, bắt buộc)
- `manufacturer`: Hãng sản xuất (chuỗi, bắt buộc)
- `price`: Giá tiền (số thực, bắt buộc, không âm)
- `stock_quantity`: Số lượng tồn kho (số nguyên, bắt buộc, không âm)
- `specifications`: Thông số kỹ thuật chung (chuỗi, tùy chọn)

## Yêu cầu

- Python 3.7+
- pip

## Cài đặt

1.  Clone repository (hoặc tạo thư mục dự án và các file như hướng dẫn).
2.  Đi đến thư mục dự án:
    ```bash
    cd phone_management_api
    ```
3.  Tạo môi trường ảo (khuyến khích):
    ```bash
    python -m venv venv
    ```
4.  Kích hoạt môi trường ảo:
    -   Windows: `venv\Scripts\activate`
    -   macOS/Linux: `source venv/bin/activate`
5.  Cài đặt các thư viện cần thiết:
    ```bash
    pip install -r requirements.txt
    ```

## Chạy ứng dụng

1.  Khởi tạo cơ sở dữ liệu (chỉ cần chạy lần đầu hoặc khi muốn tạo lại CSDL):
    ```bash
    flask init-db
    ```
    Hoặc CSDL sẽ tự tạo khi chạy ứng dụng lần đầu.

2.  Chạy server Flask:
    ```bash
    python app.py
    ```
    API sẽ chạy tại `http://127.0.0.1:5000`.

## Các Endpoints

### Xác thực

-   **`POST /register`**: Đăng ký người dùng mới.
    -   Body (JSON): `{ "username": "your_username", "password": "your_password" }`
-   **`POST /login`**: Đăng nhập và nhận JWT.
    -   Body (JSON): `{ "username": "your_username", "password": "your_password" }`
    -   Response (JSON): `{ "access_token": "your_jwt_token" }`

### Quản lý Điện thoại (Yêu cầu JWT trong Header `Authorization: Bearer <token>`)

-   **`POST /phones`**: Tạo một điện thoại mới.
    -   Body (JSON): `{ "model_name": "...", "manufacturer": "...", "price": ..., "stock_quantity": ..., "specifications": "..." }`
-   **`GET /phones`**: Lấy danh sách tất cả điện thoại.
-   **`GET /phones/<phone_id>`**: Lấy thông tin chi tiết một điện thoại.
-   **`PUT /phones/<phone_id>`**: Cập nhật thông tin một điện thoại.
    -   Body (JSON): (Các trường muốn cập nhật)
-   **`DELETE /phones/<phone_id>`**: Xóa một điện thoại.

## Kiểm thử với Postman

1.  Sử dụng endpoint `/register` để tạo tài khoản.
2.  Sử dụng endpoint `/login` để lấy `access_token`.
3.  Trong các request đến `/phones`, thêm Header:
    -   `Authorization`: `Bearer <YOUR_ACCESS_TOKEN>`
    -   `Content-Type`: `application/json` (cho POST, PUT)