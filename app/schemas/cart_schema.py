# app/schemas/cart_schema.py
from marshmallow import fields, validate, post_dump
from flask import url_for
from app.extensions import ma
from app.models.cart import Cart, CartItem
from .phone_schema import PhoneSchema
from .user_schema import UserSchema # Import UserSchema nếu bạn quyết định nest nó

class CartItemInputSchema(ma.Schema):
    phone_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))

class CartItemUpdateSchema(ma.Schema):
    quantity = fields.Int(required=True, validate=validate.Range(min=0))

class CartItemSchema(ma.SQLAlchemyAutoSchema): # Đổi thành SQLAlchemyAutoSchema nếu muốn tự động nhiều hơn
    class Meta:
        model = CartItem
        load_instance = True
        include_relationships = True # Thường cần thiết cho Nested schemas với SQLAlchemyAutoSchema
        include_fk = True # Có thể cần để phone_id được dump ra nếu không nested phone đầy đủ

    # id, quantity, added_at sẽ được auto-generate
    # Nếu bạn muốn custom, khai báo như bên dưới:
    # id = ma.auto_field(dump_only=True)
    # quantity = ma.auto_field(dump_only=True)
    # added_at = ma.auto_field(dump_only=True)

    phone = fields.Nested(PhoneSchema, dump_only=True) # PhoneSchema đã có HATEOAS
    item_subtotal = fields.Method("get_item_subtotal", dump_only=True)

    def get_item_subtotal(self, obj):
        if obj.phone and obj.phone.price is not None and obj.quantity is not None:
            return round(obj.quantity * obj.phone.price, 2)
        return 0

    @post_dump
    def add_cart_item_links(self, data, **kwargs):
        cart_item_id = data.get('id')
        if cart_item_id is None: return data
        data['_links'] = {
            "update_quantity": {"href": url_for('cart_bp.update_cart_item_route', cart_item_id=cart_item_id, _external=False), "method": "PUT"},
            "remove_item": {"href": url_for('cart_bp.remove_cart_item_route', cart_item_id=cart_item_id, _external=False), "method": "DELETE"}
        }
        if data.get('phone') and data['phone'].get('_links') and data['phone']['_links'].get('self'):
             data['_links']['product_detail'] = data['phone']['_links']['self']
        return data

class CartSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cart
        load_instance = True
        include_relationships = True # Quan trọng để xử lý 'items' và 'user' relationship

    # id, user_id, created_at, updated_at sẽ được auto-generate nếu là cột
    # Nếu user_id là ForeignKey và bạn muốn thông tin user đầy đủ:
    # user = fields.Nested(UserSchema(only=("id", "username", "role", "_links")), dump_only=True)
    # Nếu chỉ muốn user_id:
    user_id = ma.auto_field(dump_only=True)


    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)

    # Xử lý total_price property:
    # Cách 1: Dùng fields.Method nếu @property phức tạp hoặc cần custom logic khi dump
    # total_price = fields.Method("get_calculated_total_price", dump_only=True)
    # def get_calculated_total_price(self, obj):
    #     return obj.total_price # Gọi @property từ model

    # Cách 2: SQLAlchemyAutoSchema thường có thể tự động nhận diện @property.
    # Nếu nó vẫn gây lỗi, hãy thử khai báo tường minh là dump_only field.
    total_price = ma.auto_field(dump_only=True)


    @post_dump
    def add_cart_links(self, data, **kwargs):
        links = {"self": {"href": url_for('cart_bp.view_cart_route', _external=False), "method": "GET"}}
        # Kiểm tra 'items' trong 'data' (là dict đã được dump)
        if data.get('items') and len(data['items']) > 0:
            links["checkout"] = {"href": url_for('orders_bp.create_order_route', _external=False), "method": "POST", "description": "Create order. Payload: {'shipping_address': 'address'}"}
            links["clear_cart"] = {"href": url_for('cart_bp.clear_cart_route', _external=False), "method": "DELETE"}
        else:
            links["browse_products"] = {"href": url_for('phones_bp.handle_get_or_options_phones', _external=False), "method": "GET", "description": "Cart is empty. Browse products to add."}
        data['_links'] = links
        return data