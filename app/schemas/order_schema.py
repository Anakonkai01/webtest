# phone_management_api/app/schemas/order_schema.py
from marshmallow import Schema, fields, validate
from .user_schema import UserSchema # Để nested thông tin user (buyer)
from .phone_schema import PhoneSchema # Để nested thông tin phone trong order item
from app.models.order import ALLOWED_ORDER_STATUSES # Import hằng số trạng thái

class OrderItemSchema(Schema):
    id = fields.Int(dump_only=True)
    phone_id = fields.Int(dump_only=True)
    quantity = fields.Int(dump_only=True)
    price_at_purchase = fields.Float(dump_only=True)
    # Chỉ hiển thị thông tin cơ bản của phone, tránh trả về quá nhiều dữ liệu
    phone = fields.Nested(PhoneSchema(only=("id", "model_name", "manufacturer")), dump_only=True)

class OrderCreateSchema(Schema): # Dùng cho input khi POST /orders
    shipping_address = fields.Str(required=True, validate=validate.Length(min=5, max=255, error="Địa chỉ giao hàng phải từ 5 đến 255 ký tự."))
    # Có thể thêm các trường khác như payment_method_id nếu cần

class OrderStatusUpdateSchema(Schema): # Dùng cho input khi PUT /orders/<id>/status
    status = fields.Str(required=True, validate=validate.OneOf(ALLOWED_ORDER_STATUSES, error="Trạng thái không hợp lệ."))

class OrderSchema(Schema): # Dùng để output Order
    id = fields.Int(dump_only=True)
    # user_id = fields.Int(dump_only=True) # Thay bằng nested UserSchema
    user = fields.Nested(UserSchema(only=("id", "username")), dump_only=True) # Hiển thị thông tin cơ bản của người mua
    total_amount = fields.Float(dump_only=True)
    status = fields.Str(dump_only=True)
    shipping_address = fields.Str(dump_only=True, allow_none=True)
    created_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    updated_at = fields.DateTime(dump_only=True, format='%Y-%m-%dT%H:%M:%S')
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)