# phone_management_api/app/models/cart.py
from datetime import datetime, timezone # Đảm bảo timezone được import từ datetime
from app.extensions import db
from sqlalchemy import CheckConstraint, UniqueConstraint

class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, 
                            default=lambda: datetime.now(timezone.utc),
                            onupdate=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total_price(self):
        total = 0
        for item in self.items.all(): # Thêm .all() để duyệt qua các item thực sự
            if item.phone and item.phone.price is not None and item.quantity is not None:
                total += item.quantity * item.phone.price
        return round(total, 2)

    def is_empty(self):
        return not self.items.first() # True nếu không có item nào

    def __repr__(self):
        return f'<Cart ID: {self.id} UserID: {self.user_id}>'

class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    phone_id = db.Column(db.Integer, db.ForeignKey('phones.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    added_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    phone = db.relationship("Phone")

    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_cart_item_quantity_positive'),
        UniqueConstraint('cart_id', 'phone_id', name='uq_cart_phone_in_cart')
    )

    def __repr__(self):
        return f'<CartItem ID: {self.id} PhoneID: {self.phone_id} Qty: {self.quantity}>'