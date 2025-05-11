# phone_management_api/app/models/phone.py
from app.extensions import db
from sqlalchemy import CheckConstraint

class Phone(db.Model):
    __tablename__ = 'phones'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    specifications = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # ID của seller/admin tạo sản phẩm
    
    # --- Mối quan hệ với User (người tạo sản phẩm) ---
    # 'User' là tên class của model User.
    # back_populates='phones_listed' phải khớp với tên thuộc tính 'phones_listed' trong model User trỏ về Phone.
    owner = db.relationship('User', back_populates='phones_listed')

    __table_args__ = (CheckConstraint('stock_quantity >= 0', name='ck_phone_stock_non_negative'),)

    def __repr__(self):
        return f'<Phone {self.model_name}>'