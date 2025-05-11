# phone_management_api/app/schemas/order_schema.py
from marshmallow import fields, validate # Vẫn cần cho validate và fields thường
from app.extensions import ma
from app.models.order import Order, OrderItem, ALLOWED_ORDER_STATUSES
from .user_schema import UserSchema # UserSchema đã được cập nhật
from .phone_schema import PhoneSchema # PhoneSchema đã được cập nhật

class OrderItemSchema(ma.SQLAlchemySchema): # Output schema cho OrderItem
    class Meta:
        model = OrderItem
        load_instance = True

    id = ma.auto_field(dump_only=True)
    # phone_id được lấy từ phone relationship bên dưới, không cần dump trực tiếp
    quantity = ma.auto_field(dump_only=True)
    price_at_purchase = ma.auto_field(dump_only=True)
    phone = fields.Nested(PhoneSchema(only=("id", "model_name", "manufacturer")), dump_only=True)

class OrderCreateSchema(ma.Schema): # Input schema khi tạo Order
    shipping_address = fields.Str(
        required=True, 
        validate=validate.Length(min=5, max=255, error="Địa chỉ giao hàng phải từ 5 đến 255 ký tự.")
    )

class OrderStatusUpdateSchema(ma.Schema): # Input schema khi cập nhật status Order
    status = fields.Str(
        required=True, 
        validate=validate.OneOf(ALLOWED_ORDER_STATUSES, error="Trạng thái không hợp lệ.")
    )

class OrderSchema(ma.SQLAlchemyAutoSchema): # Output schema cho Order
    class Meta:
        model = Order
        load_instance = True
        # total_amount, status, shipping_address, created_at, updated_at
        # sẽ được tự động thêm từ model Order.
        # SQLAlchemyAutoSchema tự format DateTime.
        # Nếu cần format cụ thể:
        # created_at = ma.auto_field(format='%Y-%m-%dT%H:%M:%S', dump_only=True) 
        # updated_at = ma.auto_field(format='%Y-%m-%dT%H:%M:%S', dump_only=True)


    user = fields.Nested(UserSchema(only=("id", "username")), dump_only=True)
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)