# Course Project: Building a RESTful API and Web Application for Phone Store Management

**Course:** Web Programming and Applications - 503073
**Semester:** 2 - Academic Year: 2024-2025
**Focus Topic:** RESTful Web Service
**Group:** [99]
**Members:**
* [Nguyen Tran Hoang Nhan] - [523H0164]
* [Tran Van Qui] - [523H0174]
* [Dao Xuan Son] - [523H0176]

## 1. Project Introduction

This project involves building an online phone store management system, comprising a RESTful API as the backend and a client-side web application (frontend) for user interaction. The system allows for managing product information (phones), user management with different roles (buyer, seller, admin), shopping cart management, and order processing.

The core focus of the project is the design and implementation of a RESTful API adhering to REST principles, utilizing standard HTTP methods, stateless communication with JWT authentication, and JSON for resource representation.

**Key features of the system:**

* **Backend (Flask RESTful API):**
    * User Management: Registration, login, role-based authorization (buyer, seller, admin).
    * Product Management: View product list (with filtering, sorting, pagination), view product details, add, edit, delete products (authorized for seller, admin).
    * Cart Management: Add products to cart, view cart, update quantity, remove products from cart, clear entire cart (for buyers).
    * Order Management: Create orders from cart, view order list (role-based and user-filtered), view order details, update order status (for seller, admin), cancel orders.
    * API Security using JSON Web Tokens (JWT).
    * Input data validation using Marshmallow.
* **Frontend (Vue.js - simple version):**
    * User interface for interacting with API functionalities.
    * Display product list, product details.
    * Login, registration features.
    * Shopping cart management.
    * Placing orders and viewing order history.
    * Product management interface for seller/admin.
    * Order management interface for seller/admin.

## 2. Technologies Used

* **Backend:**
    * Language: Python
    * Framework: Flask
    * Database: SQLite (default for development/testing, configurable for PostgreSQL/MySQL in `config.py`)
    * Key Libraries:
        * Flask-SQLAlchemy (ORM)
        * Flask-Migrate (Database migration management - *you can add this if used*)
        * Flask-JWT-Extended (JWT Authentication)
        * Flask-Marshmallow (Data Serialization and Validation)
        * Flask-CORS (Handling Cross-Origin Resource Sharing)
        * Werkzeug (WSGI utility library, used for password hashing)
* **Frontend:**
    * Library: Vue.js (using global build via CDN)
    * HTML, CSS, JavaScript
    * Bootstrap 5 (Styling and components)
    * Font Awesome (Icons)
    * `Workspace API` (assumed to be `axios` or `Workspace` wrapper in `api.js`) for AJAX calls to the backend.
* **Other Tools:**
    * Git (Source code version control)
    * Postman (API testing - optional, mention if used)
    * Python Virtual Environment (`venv`)

## 3. Project Directory Structure
```plaintext
webtest/
├── app/                        # Main Flask backend source code
│   ├── models/                 # SQLAlchemy model definitions (User, Phone, Cart, Order)
│   ├── routes/                 # API endpoint definitions (auth, phones, cart, orders)
│   ├── schemas/                # Marshmallow schema definitions
│   ├── utils/                  # Utility functions and decorators
│   ├── __init__.py             # Flask app factory initialization
│   ├── commands.py             # CLI commands (init-db, seed-db, create-admin)
│   └── extensions.py           # Flask extension initializations
├── frontend/                   # Frontend source code
│   ├── services/               # API service logic
│   │   └── api.js              # Logic for backend API calls
│   ├── index.html              # Main HTML page
│   ├── script.js               # Main JavaScript and Vue.js code
│   └── style.css               # Custom CSS
├── venv/                       # Python virtual environment directory
├── .flaskenv                   # Environment variable configuration (optional)
├── .gitignore                  # Git ignore configuration
├── config.py                   # Flask configuration classes (Development, Testing, Production)
├── requirements.txt            # List of required Python libraries
├── run.py                      # File to run the Flask application
└── README.md                   # This file
```

## 4. Setup and Running Instructions

### 4.1. Prerequisites

* Python 3.7+
* `pip` (Python package installer)
* Git (To clone the repository, if applicable)
* A modern web browser (Chrome, Firefox, Edge, Safari)

### 4.2. Backend Setup (Flask API)

1.  **Clone the repository (If your code is on Git):**
    ```bash
    git clone [YOUR_REPOSITORY_URL]
    cd webtest
    ```
    Alternatively, if you have the code locally, ensure you are in the `webtest` root directory.

2.  **Create and activate a Python virtual environment:**
    (Recommended for isolated dependency management)
    ```bash
    python -m venv venv
    ```
    * On Windows:
        ```bash
        .\venv\Scripts\activate
        ```
    * On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

3.  **Install required Python libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Set up environment variables:**
    You can create a `.flaskenv` file in the `webtest` root directory with the following content (for development environment):
    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    # SECRET_KEY='your-very-secret-flask-key-here' # Should be set to a truly secret key
    # JWT_SECRET_KEY='your-very-secret-jwt-key-here' # Similarly, a truly secret key
    ```
    Alternatively, set them directly in your terminal (see `config.py` for other variables that might be needed). `SECRET_KEY` and `JWT_SECRET_KEY` are crucial for security, especially in a production environment.

5.  **Initialize the database:**
    This command will create the tables in the database (defaults to `database_dev.db` for the development environment).
    ```bash
    flask init-db
    ```

6.  **(Optional) Create an initial admin account:**
    Replace `youradminusername` and `youradminpassword` with your desired credentials.
    ```bash
    flask create-admin youradminusername youradminpassword
    ```
    *Sample admin account (if you use `seed-db`):*
    * Username: `admin1`
    * Password: `123456`

7.  **(Optional) Seed sample data:**
    This command will clear existing data (if any) and add some sample users, products, carts, and orders.
    ```bash
    flask seed-db
    ```
    To add sample data without clearing existing data:
    ```bash
    flask seed-db --no-clear
    ```
    *Some sample accounts created by `seed-db` (common password is `123456`):*
    * Sellers: `seller_apple`, `seller_samsung`, `seller_xiaomi`
    * Buyers: `buyer_john`, `buyer_jane`, `buyer_mike`, `buyer_lisa`, `buyer_david`

8.  **Run the Flask Backend API:**
    ```bash
    python run.py
    ```
    By default, the API will run at `http://127.0.0.1:5000`.

### 4.3. Frontend Setup (Vue.js)

The frontend is designed to run as static files, without a complex build process.

1.  **Ensure the Backend API is running.**
2.  **Open the `frontend/index.html` file in your web browser.**
    * The simplest way is to double-click the `index.html` file.
    * Alternatively, for a better experience and to avoid potential path or CORS issues (although the backend is CORS-configured), you can use a simple static file server. If you use VS Code, the "Live Server" extension is very convenient: right-click `index.html` and select "Open with Live Server". It will typically open the page at an address like `http://127.0.0.1:5500` (the port may vary).

    The frontend will automatically connect to the backend API running at `http://127.0.0.1:5000` (configured in `frontend/services/api.js`).

## 5. Features and API Testing Guide

* **Homepage:** Displays product list (with pagination, filtering, sorting).
    * API: `GET /phones/`
* **Product Details:** Click on a product name to view details.
    * API: `GET /phones/<id>`
* **Register / Login:** Use the buttons in the navbar.
    * API: `POST /auth/register`, `POST /auth/login`
* **Shopping Cart (For Buyer):**
    * Add product to cart: "Add to Cart" button. API: `POST /cart/items`
    * View cart: "Cart" menu. API: `GET /cart/`
    * Update quantity: Change the number in the input field. API: `PUT /cart/items/<id>`
    * Remove product from cart: "Remove" button. API: `DELETE /cart/items/<id>`
    * Clear entire cart: "Clear All" button. API: `DELETE /cart/`
* **Place Order (For Buyer):** From the cart, click "Place Order", fill in the address.
    * API: `POST /orders/`
* **Orders:**
    * View list (role-based): "Orders" menu. API: `GET /orders/` (with filtering, sorting, pagination)
    * View details: "View Details" button. API: `GET /orders/<id>`
    * Cancel order (Buyer/Admin): "Cancel Order" button. API: `POST /orders/<id>/cancel`
    * Update status (Seller/Admin): Select box and "Update Status" button. API: `PUT /orders/<id>/status`
* **Product Management (For Seller/Admin):**
    * View list: "Manage Products" menu. API: `GET /phones/`
    * Add product: "Add Product" button, fill form. API: `POST /phones/`
    * Edit product: "Edit" button, fill form. API: `PUT /phones/<id>`
    * Delete product: "Delete" button. API: `DELETE /phones/<id>`

You can use your browser's Developer Tools (Network Tab) to monitor the API requests being sent and the responses received when interacting with the frontend features.

## 6. Known Issues or Potential Improvements

* Currently, filtering and sorting for the "Product Management" page are not fully implemented on the frontend (the backend API supports it).
* HATEOAS has not been thoroughly implemented in either the backend (only conceptual) or the frontend.
* Unit tests for `phone_routes.py` are missing.
* The user interface could be further improved in terms of aesthetics and user experience.
* Advanced features such as product search, product reviews, etc., could be added.

## 7. Conclusion

This project serves as a demonstration of applying RESTful principles to build a robust backend API and an interactive frontend for managing a basic phone store.