# Đồ án Môn học: Xây dựng RESTful API và Ứng dụng Web Quản lý Cửa hàng Điện thoại

**Môn học:** Lập trình và Ứng dụng Web - 503073
**Học kỳ:** 2 - Năm học: 2024-2025
**Chủ đề tập trung:** Dịch vụ Web RESTful (Restful Web Service)
**Nhóm:** [99]
**Thành viên:**
* [Nguyễn Trần Hoàng Nhân] - [523H0164]
* [Trần Văn Quí] - [MSSV2]
* [Đào Xuân Sơn] - [MSSV2]

## 1. Giới thiệu Dự án

Dự án này xây dựng một hệ thống quản lý cửa hàng điện thoại trực tuyến bao gồm một RESTful API làm backend và một ứng dụng web phía client (frontend) để người dùng tương tác. Hệ thống cho phép quản lý thông tin sản phẩm (điện thoại), quản lý người dùng với các vai trò khác nhau (người mua, người bán, quản trị viên), quản lý giỏ hàng và đơn đặt hàng.

Trọng tâm của dự án là thiết kế và triển khai một RESTful API tuân thủ các nguyên tắc REST, sử dụng các phương thức HTTP chuẩn, stateless communication với xác thực JWT, và biểu diễn tài nguyên bằng JSON.

**Các chức năng chính của hệ thống:**

* **Backend (Flask RESTful API):**
    * Quản lý người dùng: Đăng ký, đăng nhập, phân quyền (buyer, seller, admin).
    * Quản lý sản phẩm: Xem danh sách (có lọc, sắp xếp, phân trang), xem chi tiết, thêm, sửa, xóa sản phẩm (phân quyền cho seller, admin).
    * Quản lý giỏ hàng: Thêm sản phẩm vào giỏ, xem giỏ hàng, cập nhật số lượng, xóa sản phẩm khỏi giỏ, xóa toàn bộ giỏ hàng (cho buyer).
    * Quản lý đơn hàng: Tạo đơn hàng từ giỏ, xem danh sách đơn hàng (phân quyền và lọc theo user), xem chi tiết đơn hàng, cập nhật trạng thái đơn hàng (cho seller, admin), hủy đơn hàng.
    * Bảo mật API sử dụng JSON Web Tokens (JWT).
    * Validation dữ liệu đầu vào sử dụng Marshmallow.
* **Frontend (Vue.js - phiên bản đơn giản):**
    * Giao diện người dùng để tương tác với các chức năng của API.
    * Hiển thị danh sách sản phẩm, chi tiết sản phẩm.
    * Chức năng đăng nhập, đăng ký.
    * Quản lý giỏ hàng.
    * Đặt hàng và xem lịch sử đơn hàng.
    * Giao diện quản lý sản phẩm cho seller/admin.
    * Giao diện quản lý đơn hàng cho seller/admin.

## 2. Công nghệ sử dụng

* **Backend:**
    * Ngôn ngữ: Python
    * Framework: Flask
    * Cơ sở dữ liệu: SQLite (mặc định cho development/testing, có thể cấu hình cho PostgreSQL/MySQL trong `config.py`)
    * Thư viện chính:
        * Flask-SQLAlchemy (ORM)
        * Flask-Migrate (Quản lý migration CSDL - *bạn có thể thêm nếu dùng*)
        * Flask-JWT-Extended (Xác thực JWT)
        * Flask-Marshmallow (Serialization và Validation dữ liệu)
        * Flask-CORS (Xử lý Cross-Origin Resource Sharing)
        * Werkzeug (WSGI utility library, dùng cho password hashing)
* **Frontend:**
    * Thư viện: Vue.js (sử dụng global build qua CDN)
    * HTML, CSS, JavaScript
    * Bootstrap 5 (Styling và components)
    * Font Awesome (Icons)
    * `Workspace API` cho việc gọi AJAX đến backend.
* **Công cụ khác:**
    * Git (Quản lý phiên bản mã nguồn)
    * Postman (Kiểm thử API - tùy chọn, bạn có thể đề cập nếu dùng)
    * Môi trường ảo Python (`venv`)

## 3. Cấu trúc Thư mục Dự án

webtest/
├── app/                        # Thư mục chứa mã nguồn chính của Flask backend
│   ├── models/                 # Định nghĩa các model SQLAlchemy (User, Phone, Cart, Order)
│   ├── routes/                 # Định nghĩa các API endpoints (auth, phones, cart, orders)
│   ├── schemas/                # Định nghĩa các schema Marshmallow
│   ├── utils/                  # Chứa các hàm tiện ích, decorators
│   ├── init.py             # Khởi tạo Flask app factory
│   ├── commands.py             # Định nghĩa các lệnh CLI (init-db, seed-db, create-admin)
│   └── extensions.py           # Khởi tạo các extension của Flask
├── frontend/                   # Thư mục chứa mã nguồn frontend
│   ├── services/
│   │   └── api.js              # Logic gọi API backend
│   ├── index.html              # Trang HTML chính
│   ├── script.js               # Mã JavaScript và Vue.js chính
│   └── style.css               # CSS tùy chỉnh
├── tests/                      # Thư mục chứa các unit test (nếu có)
│   ├── conftest.py
│   ├── test_auth_api.py
│   ├── test_cart_api.py
│   └── test_order_api.py
│   └── (thêm test_phone_api.py nếu có)
├── venv/                       # Thư mục môi trường ảo Python (nếu tạo)
├── .flaskenv                   # (Tùy chọn) File cấu hình biến môi trường cho Flask
├── .gitignore
├── config.py                   # Chứa các lớp cấu hình cho Flask (Development, Testing, Production)
├── requirements.txt            # Danh sách các thư viện Python cần thiết
├── run.py                      # File để chạy ứng dụng Flask
└── README.md                   # File này

## 4. Hướng dẫn Cài đặt và Chạy Dự án

### 4.1. Yêu cầu chung

* Python 3.7+
* `pip` (Python package installer)
* Git (Để clone repository, nếu có)
* Một trình duyệt web hiện đại (Chrome, Firefox, Edge, Safari)

### 4.2. Cài đặt Backend (Flask API)

1.  **Clone repository (Nếu bạn đặt code lên Git):**
    ```bash
    git clone [URL_repository_cua_ban]
    cd webtest
    ```
    Hoặc nếu bạn có code sẵn, hãy đảm bảo bạn đang ở thư mục gốc `webtest`.

2.  **Tạo và kích hoạt môi trường ảo Python:**
    (Khuyến khích để quản lý dependencies một cách độc lập)
    ```bash
    python -m venv venv
    ```
    * Trên Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * Trên macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Cài đặt các thư viện Python cần thiết:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Tùy chọn) Thiết lập biến môi trường:**
    Bạn có thể tạo file `.flaskenv` trong thư mục gốc `webtest` với nội dung sau (cho môi trường phát triển):
    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    # SECRET_KEY='your-very-secret-flask-key-here' # Nên đặt một key bí mật thực sự
    # JWT_SECRET_KEY='your-very-secret-jwt-key-here' # Tương tự
    ```
    Hoặc đặt trực tiếp trong terminal (xem `config.py` để biết các biến khác có thể cần). `SECRET_KEY` và `JWT_SECRET_KEY` rất quan trọng cho bảo mật, đặc biệt là trong môi trường production.

5.  **Khởi tạo cơ sở dữ liệu:**
    Lệnh này sẽ tạo các bảng trong CSDL (mặc định là `database_dev.db` cho môi trường development).
    ```bash
    flask init-db
    ```

6.  **(Tùy chọn) Tạo tài khoản admin ban đầu:**
    Thay `youradminusername` và `youradminpassword` bằng thông tin bạn muốn.
    ```bash
    flask create-admin youradminusername youradminpassword
    ```
    *Tài khoản admin mẫu (nếu bạn dùng `seed-db`):*
    * Username: `admin1`
    * Password: `123456`

7.  **(Tùy chọn) Tạo dữ liệu mẫu (Seed data):**
    Lệnh này sẽ xóa dữ liệu cũ (nếu có) và thêm một số người dùng, sản phẩm, giỏ hàng, đơn hàng mẫu.
    ```bash
    flask seed-db
    ```
    Để thêm dữ liệu mẫu mà không xóa dữ liệu hiện có:
    ```bash
    flask seed-db --no-clear
    ```
    *Một số tài khoản mẫu được tạo bởi `seed-db` (mật khẩu chung là `123456`):*
    * Seller: `seller_apple`, `seller_samsung`, `seller_xiaomi`
    * Buyer: `buyer_john`, `buyer_jane`, `buyer_mike`, `buyer_lisa`, `buyer_david`

8.  **Chạy Backend Flask API:**
    ```bash
    python run.py
    ```
    Theo mặc định, API sẽ chạy ở `http://127.0.0.1:5000`.

### 4.3. Chạy Frontend (Vue.js)

Frontend được thiết kế để chạy như các tệp tĩnh, không cần quá trình build phức tạp.

1.  **Đảm bảo Backend API đang chạy.**
2.  **Mở tệp `frontend/index.html` bằng trình duyệt web của bạn.**
    * Cách đơn giản nhất là nhấp đúp vào tệp `index.html`.
    * Hoặc, để có trải nghiệm tốt hơn và tránh một số vấn đề về đường dẫn hoặc CORS (mặc dù backend đã cấu hình CORS), bạn có thể sử dụng một máy chủ file tĩnh đơn giản. Nếu dùng VS Code, tiện ích "Live Server" rất tiện: chuột phải vào `index.html` và chọn "Open with Live Server". Nó thường sẽ mở trang ở một địa chỉ như `http://127.0.0.1:5500` (cổng có thể khác).

    Frontend sẽ tự động kết nối đến API backend đang chạy ở `http://127.0.0.1:5000` (được cấu hình trong `frontend/services/api.js`).

## 5. Các Chức Năng và Cách Kiểm Thử API

* **Trang chủ:** Hiển thị danh sách sản phẩm (có phân trang, lọc, sắp xếp).
    * API: `GET /phones/`
* **Chi tiết sản phẩm:** Nhấp vào tên sản phẩm để xem chi tiết.
    * API: `GET /phones/<id>`
* **Đăng ký / Đăng nhập:** Sử dụng các nút ở navbar.
    * API: `POST /auth/register`, `POST /auth/login`
* **Giỏ hàng (Cho Buyer):**
    * Thêm sản phẩm: Nút "Thêm vào giỏ". API: `POST /cart/items`
    * Xem giỏ hàng: Menu "Giỏ hàng". API: `GET /cart/`
    * Cập nhật số lượng: Thay đổi số trong ô input. API: `PUT /cart/items/<id>`
    * Xóa sản phẩm khỏi giỏ: Nút "Xóa". API: `DELETE /cart/items/<id>`
    * Xóa toàn bộ giỏ: Nút "Xóa hết". API: `DELETE /cart/`
* **Đặt hàng (Cho Buyer):** Từ giỏ hàng, nhấn "Đặt hàng", điền địa chỉ.
    * API: `POST /orders/`
* **Đơn hàng:**
    * Xem danh sách (phân quyền): Menu "Đơn hàng". API: `GET /orders/` (có lọc, sắp xếp, phân trang)
    * Xem chi tiết: Nút "Xem chi tiết". API: `GET /orders/<id>`
    * Hủy đơn (Buyer/Admin): Nút "Hủy đơn". API: `POST /orders/<id>/cancel`
    * Cập nhật trạng thái (Seller/Admin): Select box và nút "Cập nhật TT". API: `PUT /orders/<id>/status`
* **Quản lý Sản phẩm (Cho Seller/Admin):**
    * Xem danh sách: Menu "Quản lý SP". API: `GET /phones/`
    * Thêm sản phẩm: Nút "Thêm SP", điền form. API: `POST /phones/`
    * Sửa sản phẩm: Nút "Sửa", điền form. API: `PUT /phones/<id>`
    * Xóa sản phẩm: Nút "Xóa". API: `DELETE /phones/<id>`

Bạn có thể sử dụng Developer Tools của trình duyệt (Tab Network) để theo dõi các request API được gửi đi và response nhận về khi tương tác với các chức năng trên frontend.

## 6. Các Vấn Đề Đã Biết hoặc Cải Tiến Tiềm Năng

* Hiện tại, việc lọc và sắp xếp cho trang "Quản lý Sản phẩm" chưa được triển khai đầy đủ ở frontend (API backend có hỗ trợ).
* Chưa triển khai HATEOAS một cách triệt để ở cả backend (mới chỉ có ý tưởng) và frontend.
* Chưa có unit test cho `phone_routes.py`.
* Giao diện người dùng có thể được cải thiện thêm về mặt thẩm mỹ và trải nghiệm.
* Có thể thêm các tính năng nâng cao như tìm kiếm sản phẩm, đánh giá sản phẩm, v.v.

## 7. Kết luận

Dự án này là một minh chứng cho việc áp dụng các nguyên tắc RESTful để xây dựng một API backend mạnh mẽ và một frontend tương tác để quản lý một cửa hàng điện thoại cơ bản.

---
