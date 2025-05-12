# phone_management_api/app/schemas/__init__.py

from .user_schema import UserRegisterSchema, UserSchema
from .phone_schema import PhoneSchema
from .cart_schema import CartItemSchema, CartSchema, CartItemInputSchema, CartItemUpdateSchema
from .order_schema import OrderSchema, OrderItemSchema, OrderCreateSchema, OrderStatusUpdateSchema



# User schemas
user_register_schema = UserRegisterSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True)

# Phone schemas
phone_schema = PhoneSchema()
phones_schema = PhoneSchema(many=True) 

# Cart schemas
cart_item_input_schema = CartItemInputSchema()
cart_item_update_schema = CartItemUpdateSchema()
cart_schema_output = CartSchema()


order_schema_output = OrderSchema() 
orders_schema_output = OrderSchema(many=True) 
order_create_schema_input = OrderCreateSchema()
order_status_update_schema_input = OrderStatusUpdateSchema() 
