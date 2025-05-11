# phone_management_api/app/models/cart.py
from datetime import datetime
from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint
# from .phone import Phone # Không cần import trực tiếp nếu dùng string trong relationship
# from .user import User   # Không cần import trực tiếp nếu dùng string trong relationship

class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Mối quan hệ với User ---
    # 'User' là tên class của model User.
    # back_populates='cart' phải khớp với tên thuộc tính 'cart' trong model User trỏ về Cart.
    user = db.relationship('User', back_populates='cart')
    
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total_price(self):
        total = 0
        for item in self.items.all(): 
            if item.phone:
                total += item.quantity * item.phone.price
        return round(total, 2)
    
    def is_empty(self):
        return self.items.first() is None

    def __repr__(self):
        return f'<Cart id={self.id} user_id={self.user_id}>'

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    phone_id = db.Column(db.Integer, db.ForeignKey('phones.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_cart_item_quantity_positive'),
        UniqueConstraint('cart_id', 'phone_id', name='uq_cart_phone')
    )
    
    phone = db.relationship("Phone") # Giữ nguyên, không cần back_populates nếu Phone không trỏ lại

    def __repr__(self):
        return f'<CartItem id={self.id} phone_id={self.phone_id} quantity={self.quantity}>' 