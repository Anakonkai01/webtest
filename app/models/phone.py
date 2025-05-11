# phone_management_api/app/models/phone.py
from app.extensions import db
from sqlalchemy import CheckConstraint

class Phone(db.Model):
    __tablename__ = 'phones'

    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False, index=True)
    manufacturer = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    specifications = db.Column(db.Text, nullable=True)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    owner = db.relationship('User', back_populates='phones_listed')

    __table_args__ = (
        CheckConstraint('price >= 0', name='ck_phone_price_non_negative'),
        CheckConstraint('stock_quantity >= 0', name='ck_phone_stock_non_negative'),
    )

    def __repr__(self):
        return f'<Phone ID: {self.id} Model: {self.model_name} Manufacturer: {self.manufacturer}>'