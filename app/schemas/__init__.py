# phone_management_api/app/schemas/__init__.py

# Import các schema đã được cập nhật
from .user_schema import UserRegisterSchema, UserSchema
from .phone_schema import PhoneSchema
from .cart_schema import CartItemSchema, CartSchema, CartItemInputSchema, CartItemUpdateSchema
from .order_schema import OrderSchema, OrderItemSchema, OrderCreateSchema, OrderStatusUpdateSchema

# Khởi tạo các instance của schema để sử dụng trong ứng dụng
# Các instance này giờ là của các schema đã được refactor với Flask-Marshmallow

# User schemas
user_register_schema = UserRegisterSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True) # Dùng cho danh sách user nếu cần

# Phone schemas
phone_schema = PhoneSchema()
phones_schema = PhoneSchema(many=True) # Dùng cho danh sách phone

# Cart schemas
cart_item_input_schema = CartItemInputSchema() # Schema để validate input khi thêm item vào giỏ
cart_item_update_schema = CartItemUpdateSchema() # Schema để validate input khi cập nhật item
cart_schema_output = CartSchema() # Schema để serialize toàn bộ giỏ hàng (output)
# CartItemSchema có thể được dùng trực tiếp nếu cần serialize một CartItem đơn lẻ,
# nhưng thường nó được nested trong CartSchema.

# Order schemas
order_schema_output = OrderSchema() # Schema để serialize một đơn hàng (output)
orders_schema_output = OrderSchema(many=True) # Schema để serialize danh sách đơn hàng (output)
order_create_schema_input = OrderCreateSchema() # Schema để validate input khi tạo đơn hàng
order_status_update_schema_input = OrderStatusUpdateSchema() # Schema để validate input khi cập nhật status đơn hàng
# OrderItemSchema cũng thường được nested trong OrderSchema.