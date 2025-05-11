from marshmallow import fields, validate
from app.extensions import ma
from app.models.order import Order, OrderItem, ALLOWED_ORDER_STATUSES
from .user_schema import UserSchema
from .phone_schema import PhoneSchema

class OrderItemSchema(ma.SQLAlchemySchema):
    class Meta:
        model = OrderItem
        load_instance = True

    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field(dump_only=True)
    price_at_purchase = ma.auto_field(dump_only=True)
    phone = fields.Nested(PhoneSchema(only=("id", "model_name", "manufacturer")), dump_only=True)

class OrderStatusUpdateSchema(ma.Schema):
    status = fields.Str(
        required=True, 
        validate=validate.OneOf(ALLOWED_ORDER_STATUSES, error="Trạng thái không hợp lệ.")
    )

class OrderSchema(ma.SQLAlchemyAutoSchema): # Output schema cho Order
    class Meta:
        model = Order
 load_instance = True



    user = fields.Nested(UserSchema(only=("id", "username")), dump_only=True)
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)