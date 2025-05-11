const API_BASE_URL = 'http://127.0.0.1:5000';

const app = Vue.createApp({
    data() {
        return {
            // Auth
            isLoggedIn: false,
            username: '',
            userRole: '',
            loginForm: { username: '', password: '' },
            registerForm: { username: '', password: '', role: 'buyer' },
            authMessage: '',
            authMessageType: '',

            // Products
            products: [],
            pagination: { page: 1, per_page: 5, total_pages: 1, total_items: 0, next_page_url: null, prev_page_url: null },
            loadingProducts: false,
            filters: { manufacturer: '', model_name_contains: '', price_min: '', price_max: '' },
            sort: { sortBy: 'id', order: 'asc' },
            
            // Create Product
            newProduct: { model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' },
            createProductMessage: '',
            createProductMessageType: '',

            // Cart
            cart: { items: [], total_price: 0 },
            loadingCart: false,

            // Checkout & Orders
            showCheckoutForm: false,
            shippingAddress: '',
            orderMessage: '',
            orderMessageType: '',
            orders: [], // Danh sách đơn hàng của người dùng
        };
    },
    computed: {
        canCreateProducts() {
            return this.isLoggedIn && (this.userRole === 'seller' || this.userRole === 'admin');
        },
        isBuyer() {
            return this.isLoggedIn && this.userRole === 'buyer';
        }
    },
    methods: {
        // --- UTILITY ---
        getToken() { return localStorage.getItem('accessToken'); },
        storeToken(token) { localStorage.setItem('accessToken', token); },
        removeToken() { localStorage.removeItem('accessToken'); localStorage.removeItem('userRole'); localStorage.removeItem('username'); },
        storeUserDetails(role, username) { localStorage.setItem('userRole', role); localStorage.setItem('username', username);},
        
        async fetchWithAuth(url, options = {}) {
            const token = this.getToken();
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (token) { headers['Authorization'] = `Bearer ${token}`; }
            try {
                const response = await fetch(url, { ...options, headers });
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ error: { message: `Lỗi HTTP ${response.status}` } }));
                    console.error("API Error Response:", errorData);
                    throw new Error(errorData.error?.message || errorData.msg || JSON.stringify(errorData.errors) || `Lỗi HTTP ${response.status}`);
                }
                // Nếu response không có nội dung (ví dụ 204 No Content)
                if (response.status === 204) return null;
                return await response.json();
            } catch (error) {
                console.error('Fetch error:', error.message);
                throw error; // Ném lỗi ra để hàm gọi có thể bắt
            }
        },
        formatCurrency(value) {
            if (typeof value !== 'number') return value;
            return value.toLocaleString('vi-VN', { style: 'currency', currency: 'VND' });
        },
        getStatusColor(status) {
            switch (status) {
                case 'pending': return 'orange';
                case 'processing': return 'blue';
                case 'shipped': return 'teal';
                case 'delivered': return 'green';
                case 'cancelled': return 'red';
                case 'failed': return 'darkred';
                default: return 'black';
            }
        },
        canCancelOrder(status) {
            return ['pending', 'processing'].includes(status);
        },

        // --- AUTH ---
        async handleLogin() {
            this.authMessage = ''; this.authMessageType = '';
            try {
                const data = await this.fetchWithAuth(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    body: JSON.stringify(this.loginForm),
                });
                if (data.access_token) {
                    this.storeToken(data.access_token);
                    const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
                    this.storeUserDetails(tokenPayload.role, this.loginForm.username);
                    this.updateLoginState();
                    this.authMessage = 'Đăng nhập thành công!'; this.authMessageType = 'success';
                    // Chuyển hướng hoặc làm gì đó sau khi đăng nhập thành công
                    // window.location.href = 'index.html'; // Nếu đang ở trang login.html
                    if (window.location.pathname.includes('login.html')) {
                        window.location.href = 'index.html';
                    } else { // Nếu form login nằm trên index.html
                        this.loadInitialDataForUser();
                    }
                }
            } catch (error) {
                this.authMessage = error.message || 'Đăng nhập thất bại.'; this.authMessageType = 'error';
            }
        },
        async handleRegister() {
            this.authMessage = ''; this.authMessageType = '';
            try {
                const data = await this.fetchWithAuth(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    body: JSON.stringify(this.registerForm),
                });
                 // API trả về 201 và thông tin user
                this.authMessage = 'Đăng ký thành công! Vui lòng đăng nhập.'; this.authMessageType = 'success';
                if (typeof this.$refs.registerFormRef?.reset === 'function') {
                     this.$refs.registerFormRef.reset(); // Reset form nếu có ref
                } else { // Reset thủ công
                    this.registerForm.username = ''; this.registerForm.password = ''; this.registerForm.role = 'buyer';
                }
                // Chuyển hướng hoặc thông báo
                if (window.location.pathname.includes('register.html')) {
                    // window.location.href = 'login.html';
                }

            } catch (error) {
                this.authMessage = error.message || 'Đăng ký thất bại.'; this.authMessageType = 'error';
            }
        },
        logoutUser() {
            this.removeToken();
            this.updateLoginState();
            this.products = []; // Xóa sản phẩm khi logout
            this.cart = { items: [], total_price: 0 }; // Xóa giỏ hàng
            this.orders = []; // Xóa đơn hàng
            this.showCheckoutForm = false;
            if (window.location.pathname.includes('index.html') || window.location.pathname === '/') {
                this.loadProducts(); // Tải lại sản phẩm public
            } else {
                 window.location.href = 'index.html';
            }
        },
        updateLoginState() {
            const token = this.getToken();
            if (token) {
                this.isLoggedIn = true;
                this.username = localStorage.getItem('username') || '';
                this.userRole = localStorage.getItem('userRole') || '';
            } else {
                this.isLoggedIn = false;
                this.username = '';
                this.userRole = '';
            }
        },
        loadInitialDataForUser() {
            if (this.isLoggedIn) {
                if (this.isBuyer) {
                    this.loadUserCart();
                }
                this.loadUserOrders(); // Tất cả user đã đăng nhập có thể xem đơn hàng của mình
            }
        },

        // --- PRODUCTS ---
        async loadProducts() {
            this.loadingProducts = true;
            let queryParams = `page=${this.pagination.page}&per_page=${this.pagination.per_page}`;
            queryParams += `&sort_by=${this.sort.sortBy}&order=${this.sort.order}`;
            for (const key in this.filters) {
                if (this.filters[key] !== '' && this.filters[key] !== null) {
                    queryParams += `&${key}=${encodeURIComponent(this.filters[key])}`;
                }
            }
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/phones?${queryParams}`);
                this.products = result.data;
                this.pagination = result.meta;
            } catch (error) {
                console.error('Lỗi tải sản phẩm:', error);
                this.products = []; // Reset products nếu lỗi
                alert(error.message || "Không thể tải danh sách sản phẩm.");
            } finally {
                this.loadingProducts = false;
            }
        },
        applyFiltersAndSort() {
            this.pagination.page = 1; // Reset về trang 1 khi filter/sort
            this.loadProducts();
        },
        changePage(newPage) {
            if (newPage >= 1 && newPage <= this.pagination.total_pages) {
                this.pagination.page = newPage;
                this.loadProducts();
            }
        },
        async handleCreateProduct() {
            this.createProductMessage = ''; this.createProductMessageType = '';
            if (!this.canCreateProducts) return;
            try {
                const createdProduct = await this.fetchWithAuth(`${API_BASE_URL}/phones`, {
                    method: 'POST',
                    body: JSON.stringify(this.newProduct),
                });
                this.createProductMessage = 'Thêm sản phẩm thành công!';
                this.createProductMessageType = 'success';
                this.newProduct = { model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' }; // Reset form
                this.loadProducts(); // Tải lại danh sách
            } catch (error) {
                this.createProductMessage = error.message || 'Lỗi khi thêm sản phẩm.';
                this.createProductMessageType = 'error';
            }
        },

        // --- CART ---
        async loadUserCart() {
            if (!this.isBuyer) return;
            this.loadingCart = true;
            try {
                const cartData = await this.fetchWithAuth(`${API_BASE_URL}/cart`);
                this.cart = cartData;
            } catch (error) {
                console.error('Lỗi tải giỏ hàng:', error);
                // Không alert ở đây vì có thể user chưa có cart, API sẽ trả về lỗi (cần API trả về cart trống thay vì lỗi)
                // Hoặc get_or_create_user_cart sẽ luôn đảm bảo có cart
                this.cart = { items: [], total_price: 0 }; // Reset nếu lỗi
                 if (error.message && !error.message.toLowerCase().includes("giỏ hàng trống")) {
                    // alert(error.message || "Không thể tải giỏ hàng.");
                 }
            } finally {
                this.loadingCart = false;
            }
        },
        async addItemToCart(phoneId, quantity = 1) {
            if (!this.isBuyer) return;
            try {
                const updatedCart = await this.fetchWithAuth(`${API_BASE_URL}/cart/items`, {
                    method: 'POST',
                    body: JSON.stringify({ phone_id: phoneId, quantity }),
                });
                this.cart = updatedCart;
                alert('Đã thêm sản phẩm vào giỏ!');
            } catch (error) {
                alert(error.message || 'Lỗi khi thêm vào giỏ hàng.');
            }
        },
        async updateCartItem(cartItemId, newQuantityStr) {
            const newQuantity = parseInt(newQuantityStr);
            if (isNaN(newQuantity) || newQuantity < 0) {
                alert('Số lượng không hợp lệ.');
                this.loadUserCart(); // Tải lại để reset giá trị input
                return;
            }
            if (newQuantity === 0) { // Xử lý xóa item nếu số lượng là 0
                await this.removeCartItem(cartItemId);
                return;
            }
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, {
                    method: 'PUT',
                    body: JSON.stringify({ quantity: newQuantity }),
                });
                this.cart = result.cart; // API trả về { message, cart }
            } catch (error) {
                alert(error.message || 'Lỗi cập nhật giỏ hàng.');
                this.loadUserCart(); // Tải lại nếu lỗi
            }
        },
        async removeCartItem(cartItemId) {
            if (!confirm('Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?')) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, {
                    method: 'DELETE',
                });
                this.cart = result.cart;
                alert(result.msg || 'Đã xóa sản phẩm.');
            } catch (error) {
                alert(error.message || 'Lỗi xóa sản phẩm khỏi giỏ.');
            }
        },
        async clearUserCart() {
            if (!confirm('Bạn có chắc muốn xóa toàn bộ giỏ hàng?')) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart`, {
                    method: 'DELETE',
                });
                this.cart = result.cart; // API trả về cart trống
                alert(result.msg || 'Đã xóa giỏ hàng.');
            } catch (error) {
                alert(error.message || 'Lỗi xóa giỏ hàng.');
            }
        },

        // --- ORDERS ---
        proceedToCheckout() {
            if (!this.isBuyer || !this.cart.items || this.cart.items.length === 0) {
                alert("Giỏ hàng trống hoặc bạn không phải người mua.");
                return;
            }
            this.showCheckoutForm = true;
            this.orderMessage = ''; // Reset order message
        },
        async handlePlaceOrder() {
            this.orderMessage = ''; this.orderMessageType = '';
            if (!this.shippingAddress.trim()) {
                this.orderMessage = "Vui lòng nhập địa chỉ giao hàng.";
                this.orderMessageType = 'error';
                return;
            }
            try {
                const newOrder = await this.fetchWithAuth(`${API_BASE_URL}/orders`, {
                    method: 'POST',
                    body: JSON.stringify({ shipping_address: this.shippingAddress }),
                });
                this.orderMessage = `Đặt hàng thành công! Mã đơn hàng: #${newOrder.id}`;
                this.orderMessageType = 'success';
                this.cart = { items: [], total_price: 0 }; // Xóa giỏ hàng ở client
                this.shippingAddress = '';
                this.showCheckoutForm = false;
                this.loadUserOrders(); // Tải lại danh sách đơn hàng
                this.loadProducts(); // Tải lại sản phẩm để cập nhật tồn kho
            } catch (error) {
                this.orderMessage = error.message || 'Lỗi khi đặt hàng.';
                this.orderMessageType = 'error';
            }
        },
        async loadUserOrders() {
            if (!this.isLoggedIn) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders`); // API orders có phân trang
                this.orders = result.data; // Giả sử API trả về { data: [...], meta: ...}
            } catch (error) {
                console.error("Lỗi tải đơn hàng:", error);
                // alert(error.message || "Không thể tải danh sách đơn hàng.");
            }
        },
        async cancelUserOrder(orderId) {
            if (!confirm(`Bạn có chắc muốn hủy đơn hàng #${orderId}?`)) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/cancel`, {
                    method: 'POST', // API của chúng ta dùng POST cho cancel
                });
                alert(result.message || result.msg || "Đã gửi yêu cầu hủy đơn hàng.");
                this.loadUserOrders(); // Tải lại danh sách đơn hàng để cập nhật trạng thái
                this.loadProducts(); // Tải lại sản phẩm để cập nhật tồn kho
            } catch (error) {
                 alert(error.message || "Lỗi khi hủy đơn hàng.");
            }
        }

    },
    mounted() {
        this.updateLoginState(); // Kiểm tra trạng thái đăng nhập khi app được mount
        this.loadProducts();     // Tải sản phẩm ban đầu
        if (this.isLoggedIn) {
            this.loadInitialDataForUser();
        }

        // Xử lý cho trang login và register nếu chúng là các trang riêng biệt
        // và Vue app này cũng được dùng trên các trang đó.
        const loginFormEl = document.getElementById('login-form');
        if (loginFormEl) {
            loginFormEl.addEventListener('submit', (event) => {
                event.preventDefault();
                this.loginForm.username = event.target.username.value;
                this.loginForm.password = event.target.password.value;
                this.handleLogin();
            });
        }

        const registerFormEl = document.getElementById('register-form');
        if (registerFormEl) {
            registerFormEl.addEventListener('submit', (event) => {
                event.preventDefault();
                this.registerForm.username = document.getElementById('reg-username').value;
                this.registerForm.password = document.getElementById('reg-password').value;
                this.registerForm.role = document.getElementById('reg-role').value;
                this.handleRegister();
            });
        }
    }
});

app.mount('#app');

// Đặt các hàm global nếu cần gọi từ HTML (ví dụ: onclick)
// Tuy nhiên, với Vue, chúng ta thường dùng @click="methodName"
// Các hàm như addProductToCart, updateCartItemQuantity, removeCartItem, clearCart
// đã là method của Vue instance nên có thể gọi trực tiếp từ template với @click.
// Nếu bạn vẫn giữ các hàm onclick trong HTML cũ, bạn cần expose chúng:
// window.addProductToCart = app.addProductToCart; // Không khuyến khích