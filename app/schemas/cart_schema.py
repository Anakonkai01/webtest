# phone_management_api/app/schemas/cart_schema.py
from marshmallow import Schema, fields, validate
from .phone_schema import PhoneSchema # Import PhoneSchema để nested

class CartItemInputSchema(Schema): # Dùng cho input khi POST /cart/items
    phone_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1."))

class CartItemUpdateSchema(Schema): # Dùng cho input khi PUT /cart/items/<id>
    quantity = fields.Int(required=True, validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1."))


class CartItemSchema(Schema): # Dùng cho output từng cart item
    id = fields.Int(dump_only=True)
    # phone_id sẽ không được dump, thay vào đó là nested phone object
    quantity = fields.Int(dump_only=True) # quantity được dump từ object
    added_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    phone = fields.Nested(PhoneSchema, dump_only=True)
    item_subtotal = fields.Method("get_item_subtotal", dump_only=True)

    def get_item_subtotal(self, obj): # obj ở đây là CartItem model instance
        if obj.phone:
            return round(obj.quantity * obj.phone.price, 2)
        return 0

class CartSchema(Schema): # Dùng cho output toàn bộ giỏ hàng
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)
    total_price = fields.Float(dump_only=True) # Sẽ lấy từ property của Cart model