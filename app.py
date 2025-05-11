import os
import json
from functools import wraps
from datetime import datetime, timedelta

import click
from flask import Flask, request, jsonify, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc, CheckConstraint, UniqueConstraint, func # Thêm func
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    JWTManager,
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from marshmallow import Schema, fields, ValidationError, validate

from flask_cors import CORS

# -----------------------------------------------------------------------------
# KHỞI TẠO ỨNG DỤNG VÀ CẤU HÌNH
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = f"sqlite:///{os.path.join(project_dir, 'database.db')}"
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["JWT_SECRET_KEY"] = "your-super-secret-jwt-key-ecommerce-project" # THAY ĐỔI KEY NÀY!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1) # Token hết hạn sau 1 giờ

jwt = JWTManager(app)
db = SQLAlchemy(app)

# -----------------------------------------------------------------------------
# ĐỊNH NGHĨA CÁC TRẠNG THÁI ĐƠN HÀNG
# -----------------------------------------------------------------------------
ORDER_STATUS_PENDING = 'pending' # Chờ xử lý/thanh toán
ORDER_STATUS_PROCESSING = 'processing' # Đang xử lý
ORDER_STATUS_SHIPPED = 'shipped' # Đã giao hàng
ORDER_STATUS_DELIVERED = 'delivered' # Đã nhận hàng
ORDER_STATUS_CANCELLED = 'cancelled' # Đã hủy
ORDER_STATUS_FAILED = 'failed' # Thất bại (ví dụ: thanh toán lỗi)

ALLOWED_ORDER_STATUSES = [
    ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING, ORDER_STATUS_SHIPPED,
    ORDER_STATUS_DELIVERED, ORDER_STATUS_CANCELLED, ORDER_STATUS_FAILED
]

# -----------------------------------------------------------------------------
# ĐỊNH NGHĨA MODELS
# -----------------------------------------------------------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='buyer')

    ALLOWED_ROLES = ['buyer', 'seller', 'admin']
    REGISTRATION_ALLOWED_ROLES = ['buyer', 'seller']
    
    cart = db.relationship('Cart', back_populates='user', uselist=False, cascade='all, delete-orphan')
    orders = db.relationship('Order', back_populates='user', lazy='dynamic') # Một user có nhiều order

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

class Phone(db.Model):
    __tablename__ = 'phones'
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    manufacturer = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    specifications = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    owner = db.relationship('User', backref=db.backref('phones_listed', lazy='dynamic'))
    
    __table_args__ = (CheckConstraint('stock_quantity >= 0', name='ck_phone_stock_non_negative'),)


class Cart(db.Model):
    __tablename__ = 'carts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', back_populates='cart')
    items = db.relationship('CartItem', backref='cart', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def total_price(self):
        total = 0
        for item in self.items.all():
            if item.phone: total += item.quantity * item.phone.price
        return round(total, 2)
    
    def is_empty(self):
        return self.items.first() is None


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
    phone = db.relationship('Phone')

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) # Buyer ID
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default=ORDER_STATUS_PENDING)
    shipping_address = db.Column(db.Text, nullable=True) # Địa chỉ giao hàng (có thể làm đơn giản)
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
    phone_id = db.Column(db.Integer, db.ForeignKey('phones.id'), nullable=False) # Phone tại thời điểm mua
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False) # Giá tại thời điểm mua

    phone = db.relationship('Phone') # Để lấy thông tin cơ bản của phone (tên, hình ảnh...)
    
    __table_args__ = (CheckConstraint('quantity > 0', name='ck_order_item_quantity_positive'),
                      CheckConstraint('price_at_purchase >= 0', name='ck_order_item_price_non_negative'))


# -----------------------------------------------------------------------------
# ĐỊNH NGHĨA MARSHMALLOW SCHEMAS
# -----------------------------------------------------------------------------
class UserRegisterSchema(Schema): # Giữ nguyên
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128))
    role = fields.Str(validate=validate.OneOf(User.REGISTRATION_ALLOWED_ROLES), load_default='buyer')

class UserSchema(Schema): # Giữ nguyên
    id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    role = fields.Str(dump_only=True)

class PhoneSchema(Schema): # Giữ nguyên
    id = fields.Int(dump_only=True)
    model_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    manufacturer = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    price = fields.Float(required=True, validate=validate.Range(min=0))
    stock_quantity = fields.Int(required=True, validate=validate.Range(min=0))
    specifications = fields.Str(validate=validate.Length(max=500), allow_none=True)
    added_by_user_id = fields.Int(dump_only=True, attribute="user_id")

class CartItemSchema(Schema): # Giữ nguyên
    id = fields.Int(dump_only=True)
    phone_id = fields.Int(required=True, load_only=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1."))
    added_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    phone = fields.Nested(PhoneSchema, dump_only=True)
    item_subtotal = fields.Method("get_item_subtotal", dump_only=True)
    def get_item_subtotal(self, obj): return round(obj.quantity * obj.phone.price, 2) if obj.phone else 0

class CartSchema(Schema): # Giữ nguyên
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)
    total_price = fields.Float(dump_only=True)


# --- SCHEMAS CHO ORDER ---
class OrderItemSchema(Schema):
    id = fields.Int(dump_only=True)
    phone_id = fields.Int(dump_only=True) # Không load_only vì được tạo từ cart
    quantity = fields.Int(dump_only=True)
    price_at_purchase = fields.Float(dump_only=True)
    phone = fields.Nested(PhoneSchema(only=("id", "model_name", "manufacturer")), dump_only=True) # Chỉ lấy thông tin cơ bản của phone

class OrderSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True) # Hoặc user = fields.Nested(UserSchema(only=("id", "username")))
    user = fields.Nested(UserSchema(only=("id", "username")), dump_only=True) # Hiển thị thông tin người mua
    total_amount = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    shipping_address = fields.Str(required=False, allow_none=True) # Cho phép nhập khi tạo order, hoặc là dump_only nếu lấy từ profile
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)

class OrderCreateSchema(Schema): # Schema cho input khi tạo order
    shipping_address = fields.Str(required=True, validate=validate.Length(min=5, error="Địa chỉ giao hàng phải có ít nhất 5 ký tự."))

class OrderStatusUpdateSchema(Schema): # Schema cho input khi cập nhật status
    status = fields.Str(required=True, validate=validate.OneOf(ALLOWED_ORDER_STATUSES, error="Trạng thái không hợp lệ."))


# Khởi tạo instances của Schemas
user_register_schema = UserRegisterSchema()
user_schema = UserSchema()
phone_schema = PhoneSchema()
phones_schema = PhoneSchema(many=True)
cart_item_input_schema = CartItemSchema(only=('phone_id', 'quantity'))
cart_item_update_schema = CartItemSchema(only=('quantity',), partial=True)
cart_schema_output = CartSchema()
order_schema_output = OrderSchema()
orders_schema_output = OrderSchema(many=True)
order_create_schema_input = OrderCreateSchema()
order_status_update_schema_input = OrderStatusUpdateSchema()


# -----------------------------------------------------------------------------
# JWT, DECORATORS, CLI, ERROR HANDLERS (Giữ nguyên như phiên bản trước)
# -----------------------------------------------------------------------------
@jwt.additional_claims_loader
def add_claims_to_access_token(identity): # Giữ nguyên
    user = User.query.get(int(identity)); return {"role": user.role} if user else {}
def roles_required(*r): # Giữ nguyên
    def decorator(f): @wraps(f)
    def wrapper(*a, **kw): verify_jwt_in_request(); c=get_jwt(); ur=c.get("role");
                       if ur not in r: abort(403,f"Quyền bị từ chối. Yêu cầu vai trò: {', '.join(r)}."); return f(*a,**kw)
    return wrapper; return decorator
def admin_required(f): return roles_required('admin')(f)
def seller_or_admin_required(f): return roles_required('seller', 'admin')(f)
def buyer_required(f): return roles_required('buyer')(f)
@app.cli.command("init-db") # Giữ nguyên
def init_db_command(): db.create_all(); print("DB initialized.")
@app.cli.command("create-admin") # Giữ nguyên
@click.argument("u"); @click.argument("p")
def create_admin_command(u, p):
    if User.query.filter_by(username=u).first(): print(f"Err: User '{u}' exists."); return
    if len(p) < 6: print("Err: Pass too short."); return
    db.session.add(User(username=u, password_hash=generate_password_hash(p), role='admin')); db.session.commit(); print(f"Admin '{u}' created.")
def get_or_create_user_cart(uid): # Giữ nguyên
    u = User.query.get(uid)
    if not u: abort(404, "User không tồn tại.");
    if u.role != 'buyer': abort(403, "Chỉ 'buyer' mới có giỏ hàng.");
    if not u.cart: u.cart = Cart(user_id=uid, user=u); db.session.add(u.cart); db.session.commit()
    return u.cart
@app.errorhandler(HTTPException) # Giữ nguyên
def handle_http_exception(e): r=e.get_response();r.data=json.dumps({"error":{"code":e.code,"name":e.name,"message":e.description}});r.content_type = "application/json";return r
@app.errorhandler(ValidationError) # Giữ nguyên
def handle_marshmallow_validation(err): return jsonify(err.messages), 400

# -----------------------------------------------------------------------------
# ROUTES XÁC THỰC & QUẢN LÝ ĐIỆN THOẠI (Giữ nguyên như phiên bản trước)
# -----------------------------------------------------------------------------
@app.route('/register', methods=['POST']) # Giữ nguyên
def register(): json_data = request.get_json(); \
    if not json_data: abort(400, "No input."); \
    try: data = user_register_schema.load(json_data)
    except ValidationError as err: return jsonify(err.messages), 400
    if data['role'] == 'admin': abort(403, "Cannot self-assign admin."); \
    if User.query.filter_by(username=data['username']).first(): abort(409, "User exists."); \
    new_user = User(username=data['username'], password_hash=generate_password_hash(data['password']), role=data['role']); \
    db.session.add(new_user); db.session.commit(); return jsonify(user_schema.dump(new_user)), 201

@app.route('/login', methods=['POST']) # Giữ nguyên
def login(): json_data = request.get_json(); \
    if not json_data: abort(400, "No input."); \
    username=json_data.get('username'); password=json_data.get('password'); \
    if not username or not password: abort(400, "Missing credentials."); \
    user = User.query.filter_by(username=username).first(); \
    if user and check_password_hash(user.password_hash, password): \
        return jsonify(access_token=create_access_token(identity=str(user.id))), 200; \
    abort(401, "Bad username or password.")

# --- PHONE ROUTES (Giữ nguyên như code đầy đủ trước đó với filter/sort/pagination) ---
@app.route('/phones', methods=['POST']) # Giữ nguyên
@jwt_required() @seller_or_admin_required
def create_phone(): uid=get_jwt_identity();d=request.get_json(); \
    if not d: abort(400,"No input."); \
    try: data=phone_schema.load(d)
    except ValidationError as err: return jsonify(err.messages),400
    p=Phone(model_name=data['model_name'],manufacturer=data['manufacturer'],price=data['price'],
            stock_quantity=data['stock_quantity'],specifications=data.get('specifications'),user_id=int(uid)); \
    db.session.add(p);db.session.commit();return jsonify(phone_schema.dump(p)),201

@app.route('/phones', methods=['GET']) # Giữ nguyên
def get_all_phones(): q=Phone.query;m=request.args.get('manufacturer'); \
    if m:q=q.filter(Phone.manufacturer.ilike(f"%{m}%")); \
    mnc=request.args.get('model_name_contains'); \
    if mnc:q=q.filter(Phone.model_name.ilike(f"%{mnc}%")); \
    pmn_v=None; \
    try:pmn_s=request.args.get('price_min'); \
        if pmn_s:pmn_v=float(pmn_s); \
            if pmn_v<0:abort(400,"price_min<0."); q=q.filter(Phone.price>=pmn_v); \
        pmx_s=request.args.get('price_max'); \
        if pmx_s:pmx_v=float(pmx_s); \
            if pmx_v<0:abort(400,"price_max<0."); \
            if pmn_v is not None and pmx_v<pmn_v:abort(400,"price_max<price_min."); q=q.filter(Phone.price<=pmx_v)
    except ValueError:abort(400,"Invalid price."); \
    s_by=request.args.get('sort_by','id').lower();o_by=request.args.get('order','asc').lower(); \
    asf={'id':Phone.id,'model_name':Phone.model_name,'manufacturer':Phone.manufacturer,'price':Phone.price,'stock_quantity':Phone.stock_quantity}; \
    sc=asf.get(s_by); \
    if sc is None:abort(400,f"Invalid sort field: {s_by}."); \
    if o_by not in['asc','desc']:abort(400,"Invalid order."); \
    q=q.order_by(desc(sc) if o_by=='desc' else asc(sc)); \
    try:pg=request.args.get('page',1,type=int);ppg=request.args.get('per_page',10,type=int); \
        if pg<=0 or ppg<=0:abort(400,"page/per_page must be >0."); \
        if ppg>100:ppg=100
    except:abort(400,"Invalid page/per_page."); \
    p_o=q.paginate(page=pg,per_page=ppg,error_out=False);ca=request.args.copy();cf={k:v for k,v in ca.items() if k not in['page']}; \
    n_u,p_u=None,None; \
    if p_o.has_next:n_p=ca.copy();n_p['page']=p_o.next_num;n_u=url_for('get_all_phones',_external=False,**n_p); \
    if p_o.has_prev:p_p=ca.copy();p_p['page']=p_o.prev_num;p_u=url_for('get_all_phones',_external=False,**p_p); \
    return jsonify({"data":phones_schema.dump(p_o.items),"meta":{"page":p_o.page,"per_page":p_o.per_page, \
    "total_pages":p_o.pages,"total_items":p_o.total,"next_page_url":n_u,"prev_page_url":p_u,"filters_applied":cf}}),200

@app.route('/phones/<int:pid>', methods=['GET']) # Giữ nguyên (đổi phone_id thành pid cho ngắn)
def get_phone(pid): p=Phone.query.get_or_404(pid,f"Phone ID {pid} not found.");return jsonify(phone_schema.dump(p)),200

@app.route('/phones/<int:pid>', methods=['PUT']) # Giữ nguyên
@jwt_required()
def update_phone(pid): uid=int(get_jwt_identity());r=get_jwt().get("role");p=Phone.query.get_or_404(pid); \
    c_u=(r=='admin')or(r=='seller' and p.user_id==uid); \
    if not c_u:abort(403,"No permission."); \
    jd=request.get_json();if not jd:abort(400,"No input."); \
    try:vd=PhoneSchema(partial=True,unknown='EXCLUDE').load(jd)
    except ValidationError as err:return jsonify(err.messages),400
    if not vd:abort(400,"No valid fields."); \
    up_c=0; \
    for k,v in vd.items(): \
        if hasattr(p,k)and getattr(p,k)!=v:setattr(p,k,v);up_c+=1; \
    if up_c>0:db.session.commit(); \
    return jsonify(phone_schema.dump(p)),200

@app.route('/phones/<int:pid>', methods=['DELETE']) # Giữ nguyên
@jwt_required()
def delete_phone(pid): uid=int(get_jwt_identity());r=get_jwt().get("role");p=Phone.query.get_or_404(pid); \
    c_d=(r=='admin')or(r=='seller' and p.user_id==uid); \
    if not c_d:abort(403,"No permission."); \
    db.session.delete(p);db.session.commit();return jsonify(msg="Phone deleted."),200

# -----------------------------------------------------------------------------
# ROUTES QUẢN LÝ GIỎ HÀNG (CART ROUTES - Giữ nguyên như phiên bản trước)
# -----------------------------------------------------------------------------
@app.route('/cart', methods=['GET']) # Giữ nguyên
@jwt_required() @buyer_required
def view_cart_route(): uid=int(get_jwt_identity());c=get_or_create_user_cart(uid);return jsonify(cart_schema_output.dump(c)),200

@app.route('/cart/items', methods=['POST']) # Giữ nguyên
@jwt_required() @buyer_required
def add_item_to_cart_route(): uid=int(get_jwt_identity());cart=get_or_create_user_cart(uid);jd=request.get_json(); \
    if not jd:abort(400,"No input."); \
    try:data=cart_item_input_schema.load(jd)
    except ValidationError as err:return jsonify(err.messages),400; \
    p=Phone.query.get(data['phone_id']); \
    if not p:abort(404,f"Phone ID {data['phone_id']} not found."); \
    qty=data['quantity'];ci=CartItem.query.filter_by(cart_id=cart.id,phone_id=p.id).first(); \
    if ci:n_qty=ci.quantity+qty; \
        if p.stock_quantity<n_qty:abort(400,f"Not enough stock for {p.model_name}. Req: {n_qty}, Has: {p.stock_quantity}."); \
        ci.quantity=n_qty
    else: \
        if p.stock_quantity<qty:abort(400,f"Not enough stock for {p.model_name}. Req: {qty}, Has: {p.stock_quantity}."); \
        ci=CartItem(cart_id=cart.id,phone_id=p.id,quantity=qty);db.session.add(ci); \
    cart.updated_at=datetime.utcnow();db.session.commit();return jsonify(cart_schema_output.dump(cart)),200

@app.route('/cart/items/<int:ciid>', methods=['PUT']) # Giữ nguyên (cart_item_id -> ciid)
@jwt_required() @buyer_required
def update_cart_item_route(ciid): uid=int(get_jwt_identity());cart=get_or_create_user_cart(uid); \
    ci=CartItem.query.filter_by(id=ciid,cart_id=cart.id).first(); \
    if not ci:abort(404,f"CartItem ID {ciid} not in your cart."); \
    jd=request.get_json();if not jd:abort(400,"No input."); \
    try:data=cart_item_update_schema.load(jd)
    except ValidationError as err:return jsonify(err.messages),400; \
    n_qty=data['quantity'];msg=""; \
    if n_qty<=0:db.session.delete(ci);msg=f"Item ID {ciid} removed (qty<=0)."
    else:p=ci.phone; \
        if p.stock_quantity<n_qty:abort(400,f"Not enough stock for {p.model_name}. Req: {n_qty}, Has: {p.stock_quantity}."); \
        ci.quantity=n_qty;msg=f"Item ID {ciid} quantity updated."; \
    cart.updated_at=datetime.utcnow();db.session.commit();return jsonify(msg=msg,cart=cart_schema_output.dump(cart)),200

@app.route('/cart/items/<int:ciid>', methods=['DELETE']) # Giữ nguyên
@jwt_required() @buyer_required
def remove_cart_item_route(ciid): uid=int(get_jwt_identity());cart=get_or_create_user_cart(uid); \
    ci=CartItem.query.filter_by(id=ciid,cart_id=cart.id).first(); \
    if not ci:abort(404,f"CartItem ID {ciid} not in your cart."); \
    db.session.delete(ci);cart.updated_at=datetime.utcnow();db.session.commit(); \
    return jsonify(msg=f"Item ID {ciid} removed.",cart=cart_schema_output.dump(cart)),200

@app.route('/cart', methods=['DELETE']) # Giữ nguyên
@jwt_required() @buyer_required
def clear_cart_route(): uid=int(get_jwt_identity());cart=Cart.query.filter_by(user_id=uid).first(); \
    if cart and cart.items.first():CartItem.query.filter_by(cart_id=cart.id).delete();cart.updated_at=datetime.utcnow();db.session.commit(); \
        rc=Cart.query.get(cart.id);return jsonify(msg="Cart cleared.",cart=cart_schema_output.dump(rc)),200; \
    return jsonify(msg="Cart already empty or not found."),200

# -----------------------------------------------------------------------------
# ROUTES QUẢN LÝ ĐƠN HÀNG (ORDER MANAGEMENT) - MỚI
# -----------------------------------------------------------------------------
@app.route('/orders', methods=['POST'])
@jwt_required()
@buyer_required # Chỉ buyer mới được tạo đơn hàng
def create_order_from_cart():
    current_user_id = int(get_jwt_identity())
    cart = Cart.query.filter_by(user_id=current_user_id).first()

    if not cart or cart.is_empty():
        abort(400, description="Giỏ hàng trống. Không thể tạo đơn hàng.")

    json_data = request.get_json()
    # Validate shipping_address từ input
    try:
        order_input_data = order_create_schema_input.load(json_data if json_data else {})
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    shipping_address = order_input_data.get('shipping_address')

    # Kiểm tra tồn kho và tính tổng tiền (trong một transaction tiềm năng)
    # Để đơn giản, nếu có lỗi stock thì rollback thủ công (bằng cách không commit)
    # Trong hệ thống thực, nên dùng db.session.begin_nested() hoặc tương tự
    
    items_to_order = []
    calculated_total_amount = 0

    for cart_item in cart.items.all(): # Cần .all() vì lazy='dynamic'
        phone = cart_item.phone
        if not phone: # Sản phẩm đã bị xóa khỏi hệ thống trong khi còn trong giỏ
            abort(400, description=f"Sản phẩm với ID {cart_item.phone_id} không còn tồn tại. Vui lòng xóa khỏi giỏ hàng.")
        if phone.stock_quantity < cart_item.quantity:
            abort(400, description=f"Không đủ tồn kho cho sản phẩm '{phone.model_name}'. Yêu cầu: {cart_item.quantity}, chỉ còn: {phone.stock_quantity}.")
        
        items_to_order.append({
            "phone": phone,
            "quantity": cart_item.quantity,
            "price_at_purchase": phone.price # Lấy giá hiện tại của sản phẩm
        })
        calculated_total_amount += cart_item.quantity * phone.price
    
    calculated_total_amount = round(calculated_total_amount, 2)

    # Tạo Order
    new_order = Order(
        user_id=current_user_id,
        total_amount=calculated_total_amount,
        status=ORDER_STATUS_PENDING, # Trạng thái ban đầu
        shipping_address=shipping_address
    )
    db.session.add(new_order)
    # Phải flush để new_order có ID cho OrderItem
    try:
        db.session.flush() 
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Order flush error: {e}")
        abort(500, description="Lỗi khi tạo đơn hàng (flush).")


    # Tạo OrderItems và cập nhật tồn kho sản phẩm
    for item_data in items_to_order:
        phone_to_update = item_data["phone"]
        order_item = OrderItem(
            order_id=new_order.id,
            phone_id=phone_to_update.id,
            quantity=item_data["quantity"],
            price_at_purchase=item_data["price_at_purchase"]
        )
        db.session.add(order_item)
        
        # Trừ tồn kho
        phone_to_update.stock_quantity -= item_data["quantity"]
        if phone_to_update.stock_quantity < 0: # Double check, dù đã kiểm tra ở trên
            db.session.rollback() # Quan trọng: rollback nếu có lỗi
            abort(500, description="Lỗi nghiêm trọng: Tồn kho âm sau khi trừ. Đơn hàng đã được hủy.")
        db.session.add(phone_to_update) # Add lại để SQLAlchemy theo dõi thay đổi

    # Xóa giỏ hàng sau khi tạo đơn hàng thành công
    CartItem.query.filter_by(cart_id=cart.id).delete()
    cart.updated_at = datetime.utcnow() # Cập nhật giỏ hàng (giờ đã trống)
    db.session.add(cart)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Order commit error: {e}")
        # Cố gắng hoàn lại stock nếu commit lỗi (phần này có thể phức tạp)
        # Đây là lý do tại sao transaction lồng nhau quan trọng
        for item_data in items_to_order:
            phone_revert = Phone.query.get(item_data["phone"].id)
            if phone_revert:
                phone_revert.stock_quantity += item_data["quantity"]
                db.session.add(phone_revert)
        db.session.commit() # Cố gắng commit việc hoàn stock
        abort(500, description="Lỗi khi lưu đơn hàng. Thay đổi đã được hoàn tác (nếu có thể).")


    return jsonify(order_schema_output.dump(new_order)), 201


@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders_list():
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")

    query = Order.query

    if current_user_role == 'buyer':
        query = query.filter_by(user_id=current_user_id)
    elif current_user_role == 'seller':
        # Lọc các đơn hàng chứa sản phẩm của seller này
        # Đây là một query phức tạp hơn, cần join OrderItem và Phone
        # SELECT DISTINCT orders.* FROM orders
        # JOIN order_items ON orders.id = order_items.order_id
        # JOIN phones ON order_items.phone_id = phones.id
        # WHERE phones.user_id = :seller_id
        query = query.join(OrderItem, Order.id == OrderItem.order_id)\
                     .join(Phone, OrderItem.phone_id == Phone.id)\
                     .filter(Phone.user_id == current_user_id).distinct()
    # Admin có thể xem tất cả, không cần filter theo user_id

    # Lọc theo trạng thái (ví dụ: /orders?status=pending)
    status_filter = request.args.get('status')
    if status_filter:
        if status_filter not in ALLOWED_ORDER_STATUSES:
            abort(400, description=f"Trạng thái lọc không hợp lệ: {status_filter}.")
        query = query.filter(Order.status == status_filter)

    # Sắp xếp (ví dụ: /orders?sort_by=created_at&order=desc)
    sort_by = request.args.get('sort_by', 'created_at')
    order_dir = request.args.get('order', 'desc').lower()

    order_sort_columns = {
        'created_at': Order.created_at,
        'updated_at': Order.updated_at,
        'total_amount': Order.total_amount,
        'status': Order.status,
        'id': Order.id
    }
    sort_column = order_sort_columns.get(sort_by)
    if not sort_column:
        abort(400, description=f"Trường sắp xếp đơn hàng không hợp lệ: {sort_by}")
    if order_dir not in ['asc', 'desc']:
        abort(400, description="Thứ tự sắp xếp không hợp lệ.")
    
    query = query.order_by(desc(sort_column) if order_dir == 'desc' else asc(sort_column))

    # Phân trang
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page <= 0 or per_page <= 0: abort(400, description="page/per_page phải >0.");
        if per_page > 100: per_page = 100
    except: abort(400, "page/per_page phải là số nguyên.");

    paginated_orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    current_args = request.args.copy()
    filters_applied = {k: v for k, v in current_args.items() if k not in ['page']}
    next_url, prev_url = None, None
    if paginated_orders.has_next:
        next_params = current_args.copy(); next_params['page'] = paginated_orders.next_num
        next_url = url_for('get_orders_list', _external=False, **next_params)
    if paginated_orders.has_prev:
        prev_params = current_args.copy(); prev_params['page'] = paginated_orders.prev_num
        prev_url = url_for('get_orders_list', _external=False, **prev_params)

    return jsonify({
        "data": orders_schema_output.dump(paginated_orders.items),
        "meta": {"page": paginated_orders.page, "per_page": paginated_orders.per_page,
                 "total_pages": paginated_orders.pages, "total_items": paginated_orders.total,
                 "next_page_url": next_url, "prev_page_url": prev_url, "filters_applied": filters_applied }
    }), 200


@app.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order_details(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")

    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'buyer' and order.user_id != current_user_id:
        abort(403, description="Bạn không có quyền xem đơn hàng này.")
    elif current_user_role == 'seller':
        # Kiểm tra xem seller có sản phẩm nào trong đơn hàng này không
        is_seller_order = db.session.query(OrderItem.id)\
            .join(Phone, OrderItem.phone_id == Phone.id)\
            .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id)\
            .first()
        if not is_seller_order:
            abort(403, description="Bạn không có quyền xem đơn hàng này vì nó không chứa sản phẩm của bạn.")
    # Admin có thể xem mọi đơn hàng

    return jsonify(order_schema_output.dump(order)), 200


@app.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
@seller_or_admin_required # Chỉ admin hoặc seller (có sản phẩm trong đơn) mới được cập nhật status
def update_order_status(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")

    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    if current_user_role == 'seller':
        is_seller_order = db.session.query(OrderItem.id)\
            .join(Phone, OrderItem.phone_id == Phone.id)\
            .filter(OrderItem.order_id == order.id, Phone.user_id == current_user_id)\
            .first()
        if not is_seller_order:
            abort(403, description="Bạn không có quyền cập nhật trạng thái đơn hàng này.")
    # Admin có toàn quyền

    json_data = request.get_json()
    if not json_data: abort(400, description="Không có dữ liệu đầu vào.")
    try:
        data = order_status_update_schema_input.load(json_data)
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_status = data['status']

    # Thêm logic kiểm tra chuyển đổi trạng thái hợp lệ nếu cần
    # Ví dụ: không thể chuyển từ 'delivered' về 'pending'
    if order.status == ORDER_STATUS_DELIVERED and new_status != ORDER_STATUS_DELIVERED :
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã giao.")
    if order.status == ORDER_STATUS_CANCELLED and new_status != ORDER_STATUS_CANCELLED:
         abort(400, description="Không thể thay đổi trạng thái của đơn hàng đã hủy.")


    order.status = new_status
    order.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(order_schema_output.dump(order)), 200


@app.route('/orders/<int:order_id>/cancel', methods=['POST']) # Sử dụng POST thay vì PUT/DELETE cho hành động cụ thể
@jwt_required()
def cancel_order(order_id):
    current_user_id = int(get_jwt_identity())
    current_user_role = get_jwt().get("role")

    order = Order.query.get_or_404(order_id, description=f"Đơn hàng ID {order_id} không tìm thấy.")

    can_cancel = False
    if current_user_role == 'admin':
        can_cancel = True
    elif current_user_role == 'buyer' and order.user_id == current_user_id:
        # Buyer chỉ có thể hủy nếu đơn hàng đang ở trạng thái cho phép (ví dụ: pending, processing)
        if order.status in [ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING]:
            can_cancel = True
        else:
            abort(403, description=f"Bạn không thể hủy đơn hàng ở trạng thái '{order.status}'.")
    
    if not can_cancel:
        abort(403, description="Bạn không có quyền hủy đơn hàng này.")

    if order.status == ORDER_STATUS_CANCELLED:
        return jsonify(msg="Đơn hàng này đã được hủy trước đó.", order=order_schema_output.dump(order)), 400
    if order.status in [ORDER_STATUS_SHIPPED, ORDER_STATUS_DELIVERED]:
        abort(400, description=f"Không thể hủy đơn hàng đã '{order.status}'.")


    # Hoàn lại tồn kho cho các sản phẩm
    for item in order.items:
        phone = item.phone
        if phone: # Phone có thể đã bị xóa, cần kiểm tra
            phone.stock_quantity += item.quantity
            db.session.add(phone)
    
    order.status = ORDER_STATUS_CANCELLED
    order.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Order cancellation commit error: {e}")
        abort(500, description="Lỗi khi hủy đơn hàng. Thay đổi đã được hoàn tác (nếu có thể).")

    return jsonify(msg="Đơn hàng đã được hủy thành công.", order=order_schema_output.dump(order)), 200


# -----------------------------------------------------------------------------
# CHẠY ỨNG DỤNG
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')