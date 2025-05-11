# phone_management_api/app/models/order.py
from datetime import datetime
from app.extensions import db
from sqlalchemy import CheckConstraint
# from .user import User # Không cần nếu User model không import Order
# from .phone import Phone # Không cần nếu Phone model không import OrderItem

# --- ĐỊNH NGHĨA CÁC HẰNG SỐ TRẠNG THÁI ĐƠN HÀNG ---
ORDER_STATUS_PENDING = 'pending'
ORDER_STATUS_PROCESSING = 'processing'
ORDER_STATUS_SHIPPED = 'shipped'
ORDER_STATUS_DELIVERED = 'delivered'
ORDER_STATUS_CANCELLED = 'cancelled' # <<< ĐÂY LÀ HẰNG SỐ QUAN TRỌNG
ORDER_STATUS_FAILED = 'failed'

ALLOWED_ORDER_STATUSES = [
    ORDER_STATUS_PENDING,
    ORDER_STATUS_PROCESSING,
    ORDER_STATUS_SHIPPED,
    ORDER_STATUS_DELIVERED,
    ORDER_STATUS_CANCELLED, # <<< ĐẢM BẢO NÓ CÓ TRONG DANH SÁCH NÀY
    ORDER_STATUS_FAILED
]

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Buyer ID
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default=ORDER_STATUS_PENDING)
    shipping_address = db.Column(db.Text, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    __table_args__ = (CheckConstraint(status.in_(ALLOWED_ORDER_STATUSES), name='ck_order_status_valid'),)

    def __repr__(self):
        return f'<Order id={self.id} user_id={self.user_id} status="{self.status}">'

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    phone_id = db.Column(db.Integer, db.ForeignKey('phones.id'), nullable=False) 
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False) 

    phone = db.relationship("Phone") 
    
    __table_args__ = (
        CheckConstraint('quantity > 0', name='ck_order_item_quantity_positive'),
        CheckConstraint('price_at_purchase >= 0', name='ck_order_item_price_non_negative')
    )
    
    def __repr__(self):
        return f'<OrderItem id={self.id} order_id={self.order_id} phone_id={self.phone_id}>'