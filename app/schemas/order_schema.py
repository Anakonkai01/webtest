# app/schemas/order_schema.py
from marshmallow import fields, validate, post_dump
from flask import url_for
from app.extensions import ma
from app.models.order import Order, OrderItem, ALLOWED_ORDER_STATUSES, ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING, ORDER_STATUS_CANCELLED, ORDER_STATUS_DELIVERED, ORDER_STATUS_SHIPPED
from .user_schema import UserSchema
from .phone_schema import PhoneSchema

class OrderItemSchema(ma.SQLAlchemySchema): # Giữ nguyên
    class Meta: model = OrderItem; load_instance = True
    id = ma.auto_field(dump_only=True)
    quantity = ma.auto_field(dump_only=True)
    price_at_purchase = ma.auto_field(dump_only=True)
    phone = fields.Nested(PhoneSchema(only=("id", "model_name", "manufacturer", "price", "_links")), dump_only=True)
    @post_dump
    def add_order_item_links(self, data, **kwargs):
        if data.get('phone') and data['phone'].get('_links') and data['phone']['_links'].get('self'):
            if '_links' not in data: data['_links'] = {}
            data['_links']['product_detail'] = data['phone']['_links']['self']
        return data

class OrderCreateSchema(ma.Schema): # Giữ nguyên
    shipping_address = fields.Str(required=True, validate=validate.Length(min=5, max=255))

class OrderStatusUpdateSchema(ma.Schema): # Giữ nguyên
    status = fields.Str(required=True, validate=validate.OneOf(ALLOWED_ORDER_STATUSES))

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta: model = Order; load_instance = True

    user = fields.Nested(UserSchema(only=("id", "username", "role", "_links")), dump_only=True) # UserSchema đã có _links
    items = fields.List(fields.Nested(OrderItemSchema), dump_only=True)
    total_amount = ma.auto_field()
    status = ma.auto_field()
    shipping_address = ma.auto_field()
    created_at = ma.auto_field(dump_only=True)
    updated_at = ma.auto_field(dump_only=True)

    @post_dump
    def add_order_links(self, data, **kwargs):
        order_id = data.get('id'); status = data.get('status')
        if order_id is None: return data
        links = {"self": {"href": url_for('orders_bp.get_order_details_route', order_id=order_id, _external=False), "method": "GET"}}
        if status in [ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING]:
            links["cancel"] = {"href": url_for('orders_bp.cancel_order_route', order_id=order_id, _external=False), "method": "POST"}
        if status not in [ORDER_STATUS_DELIVERED, ORDER_STATUS_CANCELLED]:
            links["update_status"] = {"href": url_for('orders_bp.update_order_status_route', order_id=order_id, _external=False), "method": "PUT"}
        
        # Thêm link đến customer (user)
        if data.get('user') and data['user'].get('_links') and data['user']['_links'].get('self'):
            links["customer"] = data['user']['_links']['self']
        elif data.get('user') and data['user'].get('id'): # Fallback nếu UserSchema không có link self phức tạp
             links["customer"] = {
                 "href": f"/users/{data['user']['id']}", # Placeholder
                 "method": "GET",
                 "description": "View the customer who placed this order."
             }

        data['_links'] = links
        return data