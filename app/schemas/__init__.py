from .user_schema import UserRegisterSchema, UserSchema
from .phone_schema import PhoneSchema
from .cart_schema import CartItemSchema, CartSchema, CartItemInputSchema, CartItemUpdateSchema
from .order_schema import OrderSchema, OrderItemSchema, OrderCreateSchema, OrderStatusUpdateSchema

user_register_schema = UserRegisterSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True)

phone_schema = PhoneSchema()
phones_schema = PhoneSchema(many=True)

cart_item_input_schema = CartItemInputSchema()
cart_item_update_schema = CartItemUpdateSchema()
cart_schema_output = CartSchema()

# Order schemas
order_schema_output = OrderSchema()
orders_schema_output = OrderSchema(many=True)
order_create_schema_input = OrderCreateSchema()
order_status_update_schema_input = OrderStatusUpdateSchema()

# Order schemas
order_schema_output = OrderSchema() # Schema để serialize một đơn hàng (output)
orders_schema_output = OrderSchema(many=True) # Schema để serialize danh sách đơn hàng (output)
order_create_schema_input = OrderCreateSchema() # Schema để validate input khi tạo đơn hàng
order_status_update_schema_input = OrderStatusUpdateSchema() # Schema để validate input khi cập nhật status đơn hàng
# OrderItemSchema cũng thường được nested trong OrderSchema.