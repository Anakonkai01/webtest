# phone_management_api/app/schemas/__init__.py
from .user_schema import UserRegisterSchema, UserSchema
from .phone_schema import PhoneSchema
from .cart_schema import CartItemSchema, CartSchema, CartItemInputSchema, CartItemUpdateSchema # Đổi tên để rõ ràng hơn
from .order_schema import OrderSchema, OrderItemSchema, OrderCreateSchema, OrderStatusUpdateSchema

# Bạn có thể khởi tạo các instance của schema ở đây nếu muốn dùng chung toàn cục
# Hoặc khởi tạo trong các file route khi cần dùng.
# Ví dụ, nếu muốn dùng chung:
user_register_schema = UserRegisterSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True)

phone_schema = PhoneSchema()
phones_schema = PhoneSchema(many=True)

cart_item_input_schema = CartItemInputSchema()
cart_item_update_schema = CartItemUpdateSchema()
cart_schema_output = CartSchema() # Schema để output giỏ hàng
# CartItemSchema có thể được dùng trực tiếp cho output item nếu không cần custom nhiều

order_schema_output = OrderSchema()
orders_schema_output = OrderSchema(many=True)
order_create_schema_input = OrderCreateSchema()
order_status_update_schema_input = OrderStatusUpdateSchema()