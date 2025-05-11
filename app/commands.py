# phone_management_api/app/commands.py
import click
from flask.cli import with_appcontext # Để command có thể truy cập app context
from app.extensions import db
from app.models.user import User
from app.models.phone import Phone
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, ORDER_STATUS_PENDING, ORDER_STATUS_PROCESSING, ORDER_STATUS_SHIPPED # Import các hằng số status
from werkzeug.security import generate_password_hash
from datetime import datetime
from app.utils.helpers import get_or_create_user_cart # Import helper nếu seed-db cần

@click.command('init-db')
@with_appcontext # Đảm bảo command chạy trong application context
def init_db_command():
    """Xóa các bảng hiện có (nếu có) và tạo lại cấu trúc CSDL."""
    # db.drop_all() # Tùy chọn: Xóa tất cả bảng trước khi tạo lại
    db.create_all()
    click.echo('Đã khởi tạo cơ sở dữ liệu (các bảng đã được tạo).')

@click.command('create-admin')
@click.argument('username')
@click.argument('password')
@with_appcontext
def create_admin_command(username, password):
    """Tạo một người dùng với vai trò admin."""
    if User.query.filter_by(username=username).first():
        click.echo(f"Lỗi: Tên người dùng '{username}' đã tồn tại.")
        return
    if len(password) < 6:
        click.echo("Lỗi: Mật khẩu phải có ít nhất 6 ký tự.")
        return
    
    admin_user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role='admin'
    )
    db.session.add(admin_user)
    try:
        db.session.commit()
        click.echo(f"Đã tạo người dùng admin '{username}' thành công.")
    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi tạo admin: {e}")


@click.command("seed-db")
@click.option('--no-clear', is_flag=True, help="Không xóa dữ liệu hiện có trước khi tạo dữ liệu mẫu.")
@with_appcontext
def seed_db_command(no_clear):
    """Xóa dữ liệu hiện có (trừ khi có --no-clear) và tạo dữ liệu mẫu."""
    
    db.create_all() 
    click.echo('Đảm bảo các bảng CSDL đã được tạo.')

    if not no_clear:
        click.echo("Đang xóa dữ liệu cũ...")
        OrderItem.query.delete()
        Order.query.delete()
        CartItem.query.delete()
        Cart.query.delete()
        Phone.query.delete()
        User.query.delete()
        try:
            db.session.commit()
            click.echo("Đã xóa dữ liệu cũ.")
        except Exception as e:
            db.session.rollback()
            click.echo(f"Lỗi khi xóa dữ liệu cũ: {e}")
            return
    else:
        click.echo("Bỏ qua việc xóa dữ liệu cũ theo yêu cầu.")

    click.echo("Đang tạo dữ liệu mẫu...")

    try:
        # --- TẠO USERS ---
        common_password = "123456"
        hashed_common_password = generate_password_hash(common_password)
        users_to_create = [
            {'username': 'admin1', 'password_hash': hashed_common_password, 'role': 'admin'},
            {'username': 'admin2', 'password_hash': hashed_common_password, 'role': 'admin'},
            {'username': 'seller_apple', 'password_hash': hashed_common_password, 'role': 'seller'},
            {'username': 'seller_samsung', 'password_hash': hashed_common_password, 'role': 'seller'},
            {'username': 'seller_xiaomi', 'password_hash': hashed_common_password, 'role': 'seller'},
            {'username': 'buyer_john', 'password_hash': hashed_common_password, 'role': 'buyer'},
            {'username': 'buyer_jane', 'password_hash': hashed_common_password, 'role': 'buyer'},
            {'username': 'buyer_mike', 'password_hash': hashed_common_password, 'role': 'buyer'},
            {'username': 'buyer_lisa', 'password_hash': hashed_common_password, 'role': 'buyer'},
            {'username': 'buyer_david', 'password_hash': hashed_common_password, 'role': 'buyer'},
        ]
        
        created_users_map = {}
        for user_data in users_to_create:
            user = User.query.filter_by(username=user_data['username']).first()
            if not user: 
                user = User(**user_data)
                db.session.add(user)
            created_users_map[user_data['username']] = user
        db.session.flush() 
        click.echo(f"Đã xử lý {len(users_to_create)} users.")

        # --- TẠO PHONES (ĐÃ SỬA) ---
        seller_apple = created_users_map.get('seller_apple')
        seller_samsung = created_users_map.get('seller_samsung')
        seller_xiaomi = created_users_map.get('seller_xiaomi')

        # Danh sách dữ liệu phone, mỗi dict chứa các thuộc tính của Phone VÀ user_id của owner
        phones_data_with_owner_id = []
        if seller_apple:
            phones_data_with_owner_id.extend([
                {'model_name': 'iPhone 15 Pro', 'manufacturer': 'Apple', 'price': 28000000, 'stock_quantity': 50, 'specifications': 'Chip A17 Bionic, Camera 48MP', 'user_id': seller_apple.id},
                {'model_name': 'iPhone 15', 'manufacturer': 'Apple', 'price': 22000000, 'stock_quantity': 70, 'specifications': 'Chip A16 Bionic, Camera 12MP', 'user_id': seller_apple.id},
                {'model_name': 'MacBook Air M3', 'manufacturer': 'Apple', 'price': 32000000, 'stock_quantity': 30, 'specifications': 'Chip M3, 8GB RAM, 256GB SSD', 'user_id': seller_apple.id},
            ])
        if seller_samsung:
            phones_data_with_owner_id.extend([
                {'model_name': 'Galaxy S25 Ultra', 'manufacturer': 'Samsung', 'price': 30000000, 'stock_quantity': 40, 'specifications': 'Snapdragon 8 Gen 4, Camera 200MP', 'user_id': seller_samsung.id},
                {'model_name': 'Galaxy Z Fold 6', 'manufacturer': 'Samsung', 'price': 45000000, 'stock_quantity': 20, 'specifications': 'Màn hình gập, S-Pen support', 'user_id': seller_samsung.id},
                {'model_name': 'Galaxy Tab S10', 'manufacturer': 'Samsung', 'price': 20000000, 'stock_quantity': 35, 'specifications': 'Màn hình AMOLED 12.4 inch', 'user_id': seller_samsung.id},
            ])
        if seller_xiaomi:
            phones_data_with_owner_id.extend([
                {'model_name': 'Xiaomi 15 Pro', 'manufacturer': 'Xiaomi', 'price': 25000000, 'stock_quantity': 60, 'specifications': 'Snapdragon 8 Gen 4, Leica Camera', 'user_id': seller_xiaomi.id},
                {'model_name': 'Redmi Note 14 Pro', 'manufacturer': 'Xiaomi', 'price': 8000000, 'stock_quantity': 100, 'specifications': 'Dimensity 8300, Camera 108MP', 'user_id': seller_xiaomi.id},
                {'model_name': 'Poco F7 Pro', 'manufacturer': 'Xiaomi', 'price': 12000000, 'stock_quantity': 55, 'specifications': 'Snapdragon 8s Gen 3, Gaming phone', 'user_id': seller_xiaomi.id},
                {'model_name': 'Xiaomi Pad 7', 'manufacturer': 'Xiaomi', 'price': 9000000, 'stock_quantity': 45, 'specifications': 'Màn hình 11 inch, Snapdragon 8 Gen 2', 'user_id': seller_xiaomi.id},
            ])

        created_phones_list = []
        for phone_data_item in phones_data_with_owner_id:
            # Tạo Phone object trực tiếp với các key mà model Phone chấp nhận
            # user_id là một cột trong model Phone
            phone = Phone(**phone_data_item) 
            db.session.add(phone)
            created_phones_list.append(phone)
        
        db.session.flush() # Flush để phone có ID trước khi tạo CartItem/OrderItem
        click.echo(f"Đã xử lý {len(created_phones_list)} phones.")


        # --- TẠO CARTS VÀ CARTITEMS ---
        buyer_john = created_users_map.get('buyer_john')
        if buyer_john and len(created_phones_list) >= 2:
            cart_john = get_or_create_user_cart(buyer_john.id)
            if created_phones_list[0].stock_quantity >= 1:
                item1_john = CartItem.query.filter_by(cart_id=cart_john.id, phone_id=created_phones_list[0].id).first()
                if not item1_john: db.session.add(CartItem(cart_id=cart_john.id, phone_id=created_phones_list[0].id, quantity=1))
            if created_phones_list[1].stock_quantity >= 2:
                item2_john = CartItem.query.filter_by(cart_id=cart_john.id, phone_id=created_phones_list[1].id).first()
                if not item2_john: db.session.add(CartItem(cart_id=cart_john.id, phone_id=created_phones_list[1].id, quantity=2))
            cart_john.updated_at = datetime.utcnow()
            click.echo(f"Đã xử lý giỏ hàng cho {buyer_john.username}")
        
        buyer_jane = created_users_map.get('buyer_jane')
        if buyer_jane and len(created_phones_list) >= 3:
            cart_jane = get_or_create_user_cart(buyer_jane.id)
            if created_phones_list[2].stock_quantity >= 1:
                item3_jane = CartItem.query.filter_by(cart_id=cart_jane.id, phone_id=created_phones_list[2].id).first()
                if not item3_jane: db.session.add(CartItem(cart_id=cart_jane.id, phone_id=created_phones_list[2].id, quantity=1))
            cart_jane.updated_at = datetime.utcnow()
            click.echo(f"Đã xử lý giỏ hàng cho {buyer_jane.username}")

        db.session.flush()

        # --- TẠO ORDERS VÀ ORDERITEMS ---
        buyer_mike = created_users_map.get('buyer_mike')
        sample_shipping_address = "123 Đường ABC, Phường XYZ, Quận LMN, TP. HCM"
        orders_created_count = 0
        if buyer_mike and len(created_phones_list) >= 4: # Cần ít nhất 2 phone khác nhau cho ví dụ
            phone1_order = created_phones_list[3] 
            phone2_order = created_phones_list[0] 
            
            if phone1_order.stock_quantity >= 1 and phone2_order.stock_quantity >= 1:
                order_mike_total = (phone1_order.price * 1) + (phone2_order.price * 1)
                # Kiểm tra order đã tồn tại chưa nếu --no-clear
                existing_order_mike = Order.query.filter_by(user_id=buyer_mike.id, total_amount=order_mike_total).first()
                if not existing_order_mike:
                    order_mike = Order(user_id=buyer_mike.id, total_amount=order_mike_total, 
                                    status=ORDER_STATUS_PROCESSING, shipping_address=sample_shipping_address)
                    db.session.add(order_mike)
                    db.session.flush() 

                    db.session.add(OrderItem(order_id=order_mike.id, phone_id=phone1_order.id, quantity=1, price_at_purchase=phone1_order.price))
                    phone1_order.stock_quantity -= 1
                    
                    db.session.add(OrderItem(order_id=order_mike.id, phone_id=phone2_order.id, quantity=1, price_at_purchase=phone2_order.price))
                    phone2_order.stock_quantity -= 1
                    
                    orders_created_count += 1
                    click.echo(f"Đã tạo đơn hàng mẫu cho {buyer_mike.username}")
        
        buyer_lisa = created_users_map.get('buyer_lisa')
        if buyer_lisa and len(created_phones_list) >= 6:
            phone_for_lisa_order = created_phones_list[5]
            if phone_for_lisa_order.stock_quantity >= 2:
                order_lisa_total = phone_for_lisa_order.price * 2
                existing_order_lisa = Order.query.filter_by(user_id=buyer_lisa.id, total_amount=order_lisa_total).first()
                if not existing_order_lisa:
                    order_lisa = Order(user_id=buyer_lisa.id, total_amount=order_lisa_total, 
                                    status=ORDER_STATUS_SHIPPED, shipping_address="456 Đường DEF, Quận UVW, TP. Hà Nội")
                    db.session.add(order_lisa)
                    db.session.flush()

                    db.session.add(OrderItem(order_id=order_lisa.id, phone_id=phone_for_lisa_order.id, quantity=2, price_at_purchase=phone_for_lisa_order.price))
                    phone_for_lisa_order.stock_quantity -= 2
                    orders_created_count += 1
                    click.echo(f"Đã tạo đơn hàng mẫu cho {buyer_lisa.username}")
        
        if orders_created_count > 0:
             click.echo(f"Đã xử lý {orders_created_count} đơn hàng mẫu và cập nhật tồn kho.")
        
        db.session.commit()
        click.echo("Đã tạo dữ liệu mẫu thành công!")

    except Exception as e:
        db.session.rollback()
        click.echo(f"Lỗi khi tạo dữ liệu mẫu: {e}")
        click.echo("Tất cả thay đổi đã được hoàn tác (nếu có).")

# Các command khác (init_db_command, create_admin_command) không thay đổi.