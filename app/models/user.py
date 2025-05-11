# phone_management_api/app/models/user.py
from app.extensions import db
# from werkzeug.security import generate_password_hash, check_password_hash # Cần nếu bạn có method set/check password trong model

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')

    ALLOWED_ROLES = ['buyer', 'seller', 'admin']
    REGISTRATION_ALLOWED_ROLES = ['buyer', 'seller']

    # --- Mối quan hệ với Cart ---
    # 'Cart' là tên class của model Cart.
    # back_populates='user' phải khớp với tên thuộc tính 'user' trong model Cart trỏ về User.
    # uselist=False chỉ định đây là mối quan hệ một-một (một User chỉ có một Cart).
    # cascade='all, delete-orphan' nghĩa là khi User bị xóa, Cart liên quan cũng bị xóa.
    cart = db.relationship('Cart', back_populates='user', uselist=False, cascade='all, delete-orphan')

    # --- Mối quan hệ với Order ---
    # 'Order' là tên class của model Order.
    # back_populates='user' phải khớp với tên thuộc tính 'user' trong model Order trỏ về User.
    # lazy='dynamic' cho phép thực hiện các truy vấn tiếp theo trên user.orders.
    orders = db.relationship('Order', back_populates='user', lazy='dynamic')

    # --- Mối quan hệ với Phone (khi user là người bán/tạo sản phẩm) ---
    # 'Phone' là tên class của model Phone.
    # back_populates='owner' phải khớp với tên thuộc tính 'owner' trong model Phone trỏ về User.
    phones_listed = db.relationship('Phone', back_populates='owner', lazy='dynamic')


    def __repr__(self):
        return f'<User {self.username} ({self.role})>'