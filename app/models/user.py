# phone_management_api/app/models/user.py
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')

    ALLOWED_ROLES = ['buyer', 'seller', 'admin']
    REGISTRATION_ALLOWED_ROLES = ['buyer', 'seller']


    cart = db.relationship('Cart', back_populates='user', uselist=False, cascade='all, delete-orphan')


    orders = db.relationship('Order', back_populates='user', lazy='dynamic')

   
    phones_listed = db.relationship('Phone', back_populates='owner', lazy='dynamic')


    def __repr__(self):
        return f'<User {self.username} ({self.role})>'