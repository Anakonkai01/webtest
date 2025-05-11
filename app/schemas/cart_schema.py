# phone_management_api/app/schemas/cart_schema.py
from marshmallow import fields, validate # Vẫn cần cho validate và fields thường
from app.extensions import ma
from app.models.cart import Cart, CartItem
from .phone_schema import PhoneSchema # PhoneSchema đã được cập nhật

class CartItemInputSchema(ma.Schema): # Input schema
    phone_id = fields.Int(required=True)
    quantity = fields.Int(
        required=True, 
        validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1.")
    )

class CartItemUpdateSchema(ma.Schema): # Input schema
    quantity = fields.Int(
        required=True, 
        validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1.")
    )

class CartItemSchema(ma.SQLAlchemySchema): # Output schema cho CartItem
    class Meta:
        model = CartItem
        load_instance = True

    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field(dump_only=True)
    added_at = ma.auto_field(dump_only=True) # Flask-Marshmallow tự format DateTime
    
    phone = fields.Nested(PhoneSchema, dump_only=True) # Sử dụng marshmallow.fields.Nested
    
    item_subtotal = fields.Method("get_item_subtotal", dump_only=True)

    def get_item_subtotal(self, obj): # obj là instance của CartItem model
        if obj.phone and obj.phone.price is not None and obj.quantity is not None:
            return round(obj.quantity * obj.phone.price, 2)
        return 0

class CartSchema(ma.SQLAlchemyAutoSchema): # Output schema cho Cart
    class Meta:
        model = Cart
        load_instance = True
        # total_price là một property trên model Cart, SQLAlchemyAutoSchema sẽ tự động thêm vào
        # nếu không, bạn có thể định nghĩa: total_price = ma.Float(dump_only=True)
        # created_at, updated_at cũng sẽ được tự động thêm và format.

    # Định nghĩa rõ ràng items để đảm bảo sử dụng CartItemSchema đã tùy chỉnh
    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)