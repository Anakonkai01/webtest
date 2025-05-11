# phone_management_api/app/schemas/phone_schema.py
from marshmallow import Schema, fields, validate
# Nếu bạn dùng Flask-Marshmallow và muốn tích hợp SQLAlchemy:
# from app.extensions import ma
# from app.models.phone import Phone
# class PhoneSchema(ma.SQLAlchemyAutoSchema):
#     class Meta:
#         model = Phone
#         load_instance = True # Optional: Tải instance model khi deserialize
#         # include_fk = True # Optional: Bao gồm cả khóa ngoại
#     # Bạn có thể override hoặc thêm các trường ở đây nếu cần
#     added_by_user_id = fields.Int(dump_only=True, attribute="user_id")

# Hiện tại chúng ta đang dùng Marshmallow thuần:
class PhoneSchema(Schema):
    id = fields.Int(dump_only=True)
    model_name = fields.Str(required=True, validate=validate.Length(min=1, max=100, error="Tên model không được để trống và tối đa 100 ký tự."))
    manufacturer = fields.Str(required=True, validate=validate.Length(min=1, max=100, error="Hãng sản xuất không được để trống và tối đa 100 ký tự."))
    price = fields.Float(required=True, validate=validate.Range(min=0, error="Giá tiền không được âm."))
    stock_quantity = fields.Int(required=True, validate=validate.Range(min=0, error="Số lượng tồn kho không được âm."))
    specifications = fields.Str(validate=validate.Length(max=500, error="Thông số kỹ thuật tối đa 500 ký tự."), allow_none=True)
    added_by_user_id = fields.Int(dump_only=True, attribute="user_id") # Hiển thị user_id của người tạo