from marshmallow import fields, validate
from app.extensions import ma
from app.models.phone import Phone

class PhoneSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Phone
        load_instance = False

    id = ma.auto_field(dump_only=True)
    model_name = ma.auto_field(
 required=True,
 validate=validate.Length(min=1, max=100, error="Tên model không được để trống và tối đa 100 ký tự.")
    )
    manufacturer = ma.auto_field(
 required=True,
 validate=validate.Length(min=1, max=100, error="Hãng sản xuất không được để trống và tối đa 100 ký tự.")
    )
    price = ma.auto_field(
 required=True,
 validate=validate.Range(min=0, error="Giá tiền không được âm.")
    )
    stock_quantity = ma.auto_field(
 required=True,
 validate=validate.Range(min=0, error="Số lượng tồn kho không được âm.")
    )
    specifications = ma.auto_field(
 validate=validate.Length(max=500, error="Thông số kỹ thuật tối đa 500 ký tự."),
 allow_none=True
    )
    added_by_user_id = ma.Int(attribute="user_id", dump_only=True)