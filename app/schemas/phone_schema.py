# app/schemas/phone_schema.py
from marshmallow import fields, validate, post_dump
from flask import url_for
from app.extensions import ma
from app.models.phone import Phone

class PhoneSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Phone
        load_instance = False

    id = ma.auto_field(dump_only=True)
    model_name = ma.auto_field(required=True, validate=validate.Length(min=1, max=100))
    manufacturer = ma.auto_field(required=True, validate=validate.Length(min=1, max=100))
    price = ma.auto_field(required=True, validate=validate.Range(min=0))
    stock_quantity = ma.auto_field(required=True, validate=validate.Range(min=0))
    specifications = ma.auto_field(validate=validate.Length(max=500), allow_none=True)
    added_by_user_id = ma.Int(attribute="user_id", dump_only=True) # Ai đã thêm sản phẩm

    @post_dump
    def add_hypermedia_links(self, data, **kwargs):
        phone_id = data.get('id')
        if phone_id is None: return data

        links = {
            "self": {"href": url_for('phones_bp.get_phone_route', phone_id=phone_id, _external=False), "method": "GET"},
            "update": {"href": url_for('phones_bp.update_phone_route', phone_id=phone_id, _external=False), "method": "PUT"},
            "delete": {"href": url_for('phones_bp.delete_phone_route', phone_id=phone_id, _external=False), "method": "DELETE"}
        }
        if data.get('stock_quantity', 0) > 0:
            links["add_to_cart"] = {
                "href": url_for('cart_bp.add_item_to_cart_route', _external=False),
                "method": "POST",
                "description": f"Add this product to cart. Payload example: {{'phone_id': {phone_id}, 'quantity': 1}}"
            }
        # Link đến người bán (owner)
        owner_id = data.get('added_by_user_id')
        if owner_id:
            links["seller"] = {
                # Giả sử bạn sẽ có route để xem chi tiết user (hoặc profile)
                "href": f"/users/{owner_id}", # Placeholder, thay bằng url_for nếu có route
                "method": "GET",
                "description": "View the seller of this product."
            }
        data['_links'] = links
        return data