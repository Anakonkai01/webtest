from marshmallow import fields, validate
from app.extensions import ma
from app.models.cart import Cart, CartItem
from .phone_schema import PhoneSchema

class CartItemInputSchema(ma.Schema):
    phone_id = fields.Int(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1."))

class CartItemUpdateSchema(ma.Schema):
    quantity = fields.Int(required=True, validate=validate.Range(min=1, error="Số lượng phải ít nhất là 1."))

class CartItemSchema(ma.SQLAlchemySchema):
    class Meta:
        model = CartItem
        load_instance = True

    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field(dump_only=True)
    added_at = ma.auto_field(dump_only=True)

    phone = fields.Nested(PhoneSchema, dump_only=True)
    
    item_subtotal = fields.Method("get_item_subtotal", dump_only=True)

    def get_item_subtotal(self, obj): # obj là instance của CartItem model
        if obj.phone and obj.phone.price is not None and obj.quantity is not None:
            return round(obj.quantity * obj.phone.price, 2)
        return 0

class CartSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Cart
        load_instance = True

    items = fields.List(fields.Nested(CartItemSchema), dump_only=True)