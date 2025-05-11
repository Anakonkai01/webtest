const API_BASE_URL = 'http://127.0.0.1:5000';
const ALLOWED_ORDER_STATUSES_GLOBAL = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'failed']; // Lấy từ backend nếu có endpoint

const app = Vue.createApp({
    data() {
        return {
            // System
            currentView: 'login', // productsPublic, cart, orders, productManagement, userManagement, login, register
            isLoading: { // Đối tượng chứa trạng thái loading cho các phần khác nhau
                auth: false,
                products: false,
                productsPublic: false,
                productForm: false,
                deleteProduct: null, // lưu id sản phẩm đang xóa
                cart: false,
                cartAction: null, // lưu id item hoặc hành động (add, clear)
                orders: false,
                orderAction: null, // lưu id order hoặc hành động
                // userManagement: false,
            },
            toasts: [], // {id, message, type: 'success'/'error'/'info'}
            apiLog: [],
            showApiLog: false,
            currentActionType: '', // 'update_status', 'cancel_order', etc.

            // Auth
            isLoggedIn: false,
            username: '',
            userId: null,
            userRole: '',
            loginForm: { username: '', password: '' },
            registerForm: { username: '', password: '', role: 'buyer' },
            
            // Products (For Admin/Seller Management)
            products: [],
            pagination: { page: 1, per_page: 5, total_pages: 1, total_items: 0 },
            productForm: { model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' },
            editingProduct: {},

            // Products Public
            productsPublic: [],
            paginationPublic: { page: 1, per_page: 5, total_pages: 1, total_items: 0 },
            filters: { manufacturer: '', model_name_contains: '', price_min: '', price_max: '' },
            sort: { sortBy: 'id', order: 'asc' },
            filterTimeout: null,

            // Cart (Buyer)
            cart: { items: [], total_price: 0 },

            // Checkout & Orders
            showCheckoutForm: false,
            shippingAddress: '',
            orders: [],
            paginationOrders: { page: 1, per_page: 5, total_pages: 1, total_items: 0 },
            orderFilters: { status: ''},
            allowedOrderStatuses: ALLOWED_ORDER_STATUSES_GLOBAL,
        };
    },
    computed: {
        isBuyer() { return this.isLoggedIn && this.userRole === 'buyer'; },
        isSeller() { return this.isLoggedIn && this.userRole === 'seller'; },
        isAdmin() { return this.isLoggedIn && this.userRole === 'admin'; },
        canManageProducts() { return this.isSeller || this.isAdmin; },
        canManageOrders() { return this.isSeller || this.isAdmin; },
        cartItemCount() { return this.cart.items ? this.cart.items.length : 0; }
    },
    methods: {
        // --- UI & UTILITIES ---
        showToast(message, type = 'info', duration = 3000) {
            const id = Date.now();
            this.toasts.push({ id, message, type });
            setTimeout(() => {
                this.toasts = this.toasts.filter(toast => toast.id !== id);
            }, duration);
        },
        formatDate(dateString, includeTime = false) {
            if (!dateString) return 'N/A';
            const options = { year: 'numeric', month: 'short', day: 'numeric' };
            if (includeTime) {
                options.hour = '2-digit';
                options.minute = '2-digit';
                options.second = '2-digit';
            }
            return new Date(dateString).toLocaleDateString('vi-VN', options);
        },
        formatCurrency(value) { /* Giữ nguyên */ },
        getStatusColor(status) { /* Giữ nguyên */ },
        logApiCall(method, url, requestData, responseData, status, isError = false) {
            this.apiLog.unshift({ // Thêm vào đầu để log mới nhất ở trên
                timestamp: new Date().toISOString(),
                method, url, requestData, responseData, status, isError
            });
            if (this.apiLog.length > 50) { // Giới hạn số lượng log
                this.apiLog.pop();
            }
        },
        clearApiLog() { this.apiLog = []; },
        setView(viewName) {
            this.currentView = viewName;
            // Tải dữ liệu tương ứng nếu cần khi chuyển view
            if (viewName === 'productsPublic' && this.productsPublic.length === 0) this.loadProductsPublic();
            if (viewName === 'productManagement' && this.canManageProducts && this.products.length === 0) this.loadManagedProducts();
            if (viewName === 'cart' && this.isBuyer && !this.cart.items.length) this.loadUserCart();
            if (viewName === 'orders' && this.isLoggedIn && this.orders.length === 0) this.loadUserOrders();
        },
         allowedOrderStatusesForUpdate(currentStatus) {
            // Seller có thể không được phép chuyển về pending, hoặc hủy.
            // Admin có thể có nhiều quyền hơn.
            if (this.isAdmin) return ALLOWED_ORDER_STATUSES_GLOBAL;
            if (this.isSeller) {
                 // Seller chỉ được chuyển sang processing, shipped
                 if (currentStatus === 'pending') return ['processing', 'shipped'];
                 if (currentStatus === 'processing') return ['shipped'];
                 // Không cho seller tự ý hủy hay chuyển về trạng thái cũ hơn sau khi đã ship.
            }
            return [currentStatus]; // Mặc định không cho đổi
        },


        // --- API Calls ---
        getToken() { return localStorage.getItem('accessToken'); },
        storeToken(token) { localStorage.setItem('accessToken', token); },
        removeToken() { /* Giữ nguyên */ },
        storeUserDetails(userId, role, username) { // userId được truyền vào đây
            localStorage.setItem('userId', userId); // LƯU USER ID
            localStorage.setItem('userRole', role); 
            localStorage.setItem('username', username);
        },
        async fetchWithAuth(url, options = {}, actionKey = null, itemId = null) {
            if (actionKey) {
                if (itemId) this.isLoading[actionKey] = itemId;
                else this.isLoading[actionKey] = true;
            }
            const startTime = Date.now();
            const token = this.getToken();
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (token) { headers['Authorization'] = `Bearer ${token}`; }
            
            let response, responseData = null, status, isError = false;
            try {
                response = await fetch(url, { ...options, headers });
                status = response.status;
                if (response.status === 204) { // Handle 204 No Content
                    responseData = null;
                } else {
                    responseData = await response.json();
                }

                if (!response.ok) {
                    isError = true;
                    const error = new Error(responseData.error?.message || responseData.msg || responseData.message || `Lỗi HTTP ${response.status}`);
                    error.response = responseData; // Gắn thêm data lỗi vào error object
                    throw error;
                }
                this.logApiCall(options.method || 'GET', url, options.body ? JSON.parse(options.body) : null, responseData, status, isError);
                return responseData;
            } catch (error) {
                isError = true;
                console.error(`API call to ${url} failed:`, error.message, error.response || error);
                this.showToast(error.message || 'Có lỗi xảy ra từ API', 'error');
                this.logApiCall(options.method || 'GET', url, options.body ? JSON.parse(options.body) : null, error.response || { error: error.message }, status || 'N/A', isError);
                throw error;
            } finally {
                if (actionKey) this.isLoading[actionKey] = false;
            }
        },

        // --- AUTH ---
        async handleLogin() {
            this.currentActionType = 'login';
            try {
                const data = await this.fetchWithAuth(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    body: JSON.stringify(this.loginForm),
                }, 'auth');
                if (data.access_token) {
                    this.storeToken(data.access_token);
                    const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
                    // Giả sử JWT identity (sub claim) là user ID
                    // và bạn đã thêm 'username' và 'role' vào additional_claims_loader ở backend
                    this.storeUserDetails(tokenPayload.sub, tokenPayload.role, tokenPayload.username); 

                    this.updateLoginState(); // Gọi hàm này để cập nhật state isLoggedIn, userId, username, userRole
                    this.showToast('Đăng nhập thành công!', 'success');
                    this.loginForm = { username: '', password: '' };
                    this.loadInitialDataForUser();
                    this.setView('productsPublic'); 
                }
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async handleRegister() {
             this.currentActionType = 'register';
            if (this.registerForm.password.length < 6) {
                this.showToast('Mật khẩu phải có ít nhất 6 ký tự.', 'error');
                return;
            }
            try {
                await this.fetchWithAuth(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    body: JSON.stringify(this.registerForm),
                }, 'auth');
                this.showToast('Đăng ký thành công! Vui lòng đăng nhập.', 'success');
                this.registerForm = { username: '', password: '', role: 'buyer' };
                this.currentView = 'login';
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        logoutUser() {
            this.removeToken();
            this.updateLoginState();
            this.products = []; this.productsPublic = [];
            this.cart = { items: [], total_price: 0 };
            this.orders = [];
            this.showCheckoutForm = false;
            this.currentView = 'login';
            this.showToast('Đã đăng xuất.', 'info');
            // this.loadProductsPublic(); // Không cần thiết vì sẽ chuyển về login
        },
        updateLoginState() {
            const token = this.getToken();
            if (token) {
                this.isLoggedIn = true;
                this.userId = localStorage.getItem('userId'); // ĐỌC USER ID
                this.username = localStorage.getItem('username') || '';
                this.userRole = localStorage.getItem('userRole') || '';
            } else {
                this.isLoggedIn = false; this.userId = null; this.username = ''; this.userRole = '';
            }
        },
        loadInitialDataForUser() {
            if (this.isLoggedIn) {
                this.loadProductsPublic();
                if (this.canManageProducts) this.loadManagedProducts();
                if (this.isBuyer) this.loadUserCart();
                this.loadUserOrders();
            } else {
                // this.loadProductsPublic(); // Đã được gọi khi logout hoặc setView ban đầu
            }
        },

        // --- PRODUCTS (Management) ---
        async loadManagedProducts() {
            if (!this.canManageProducts) return;
            let queryParams = `page=${this.pagination.page}&per_page=${this.pagination.per_page}&sort_by=id&order=desc`;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/phones?${queryParams}`, {}, 'products');
                this.products = result.data;
                this.pagination = result.meta;
            } catch (error) { this.products = []; /* fetchWithAuth đã showToast lỗi */ }
        },
        async handleCreateProduct() {
            this.currentActionType = 'create_product';
            // Client-side validation
            if (!this.productForm.model_name || !this.productForm.manufacturer || this.productForm.price == null || this.productForm.stock_quantity == null) {
                this.showToast('Vui lòng điền đầy đủ các trường bắt buộc cho sản phẩm.', 'error');
                return;
            }
            if (this.productForm.price < 0 || this.productForm.stock_quantity < 0) {
                 this.showToast('Giá và tồn kho không được âm.', 'error');
                return;
            }
            try {
                await this.fetchWithAuth(`${API_BASE_URL}/phones`, {
                    method: 'POST',
                    body: JSON.stringify(this.productForm),
                }, 'productForm');
                this.showToast('Thêm sản phẩm thành công!', 'success');
                this.productForm = { model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' };
                this.loadManagedProducts();
                this.loadProductsPublic(); // Refresh public list
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        startEditProduct(product) {
            this.editingProduct = { ...product };
            this.productForm = { ...product }; // Điền form
             // Cuộn đến form
            this.$nextTick(() => {
                const formContainer = this.$el.querySelector('.product-form-container');
                if (formContainer) formContainer.scrollIntoView({ behavior: 'smooth' });
            });
        },
        cancelEditProduct() {
            this.editingProduct = {};
            this.productForm = { model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' };
        },
        async handleUpdateProduct() {
            this.currentActionType = 'update_product';
            if (!this.editingProduct.id) return;
            if (!this.productForm.model_name || !this.productForm.manufacturer || this.productForm.price == null || this.productForm.stock_quantity == null) {
                this.showToast('Vui lòng điền đầy đủ các trường bắt buộc cho sản phẩm.', 'error');
                return;
            }
             if (this.productForm.price < 0 || this.productForm.stock_quantity < 0) {
                 this.showToast('Giá và tồn kho không được âm.', 'error');
                return;
            }
            const updateData = { ...this.productForm };
            delete updateData.id; delete updateData.user_id; delete updateData.added_by_user_id; // Không gửi các trường này
            try {
                await this.fetchWithAuth(`${API_BASE_URL}/phones/${this.editingProduct.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(updateData),
                }, 'productForm');
                this.showToast('Cập nhật sản phẩm thành công!', 'success');
                this.cancelEditProduct();
                this.loadManagedProducts();
                this.loadProductsPublic();
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async handleDeleteProduct(phoneId) {
            this.currentActionType = 'delete_product';
            if (!confirm(`Bạn có chắc muốn xóa sản phẩm ID: ${phoneId}? Thao tác này không thể hoàn tác.`)) return;
            try {
                await this.fetchWithAuth(`${API_BASE_URL}/phones/${phoneId}`, { method: 'DELETE' }, 'deleteProduct', phoneId);
                this.showToast('Xóa sản phẩm thành công!', 'success');
                this.loadManagedProducts();
                this.loadProductsPublic();
                if (this.editingProduct.id === phoneId) this.cancelEditProduct();
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        canEditOrDeleteProduct(phone) { // Cần userId đã được lưu
            if (!this.isLoggedIn) return false;
            if (this.isAdmin) return true;
            return this.isSeller && phone.user_id === parseInt(this.userId);
        },
        changePage(newPage) { this.pagination.page = newPage; this.loadManagedProducts(); },

        // --- PRODUCTS (Public Listing) ---
        async loadProductsPublic() {
            let queryParams = `page=${this.paginationPublic.page}&per_page=${this.paginationPublic.per_page}`;
            queryParams += `&sort_by=${this.sort.sortBy}&order=${this.sort.order}`;
            for (const key in this.filters) {
                if (this.filters[key] !== '' && this.filters[key] !== null) {
                    queryParams += `&${key}=${encodeURIComponent(this.filters[key])}`;
                }
            }
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/phones?${queryParams}`, {}, 'productsPublic');
                this.productsPublic = result.data;
                this.paginationPublic = result.meta;
            } catch (error) { this.productsPublic = []; /* fetchWithAuth đã showToast lỗi */ }
        },
        applyFiltersAndSort() { this.paginationPublic.page = 1; this.loadProductsPublic(); },
        applyFiltersAndSortDebounced() { clearTimeout(this.filterTimeout); this.filterTimeout = setTimeout(this.applyFiltersAndSort, 500); },
        changePagePublic(newPage) { this.paginationPublic.page = newPage; this.loadProductsPublic(); },

        // --- CART ---
        async loadUserCart() {
            if (!this.isBuyer) return;
            try {
                const cartData = await this.fetchWithAuth(`${API_BASE_URL}/cart`, {}, 'cart');
                this.cart = cartData || { items: [], total_price: 0 }; // Handle null response if cart is new/empty
            } catch (error) { this.cart = { items: [], total_price: 0 }; /* fetchWithAuth đã showToast lỗi (nếu không phải 404) */ }
        },
        async addItemToCart(phoneId, quantity = 1) {
            this.currentActionType = 'add_to_cart';
            if (!this.isBuyer) { this.showToast("Vui lòng đăng nhập với tài khoản người mua.", 'error'); return; }
            try {
                const updatedCart = await this.fetchWithAuth(`${API_BASE_URL}/cart/items`, {
                    method: 'POST',
                    body: JSON.stringify({ phone_id: phoneId, quantity }),
                }, 'cartAction', phoneId);
                this.cart = updatedCart;
                this.showToast('Đã thêm vào giỏ!', 'success');
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async updateCartItem(cartItemId, newQuantityStr) {
            this.currentActionType = 'update_cart_item';
            const newQuantity = parseInt(newQuantityStr);
            const itemInCart = this.cart.items.find(item => item.id === cartItemId);

            if (isNaN(newQuantity) || newQuantity < 0) {
                this.showToast('Số lượng không hợp lệ.', 'error');
                if(itemInCart) itemInCart.quantity = itemInCart.quantity; // Reset input value visually by re-assigning
                this.$forceUpdate(); // Or find a better way to reset input value
                return;
            }
            if (newQuantity === 0) { await this.removeCartItem(cartItemId); return; }
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, {
                    method: 'PUT',
                    body: JSON.stringify({ quantity: newQuantity }),
                }, 'cartAction', cartItemId);
                this.cart = result.cart;
                this.showToast('Cập nhật giỏ hàng thành công.', 'success');
            } catch (error) { this.loadUserCart(); /* fetchWithAuth đã showToast lỗi, tải lại giỏ hàng để reset */ }
        },
        async removeCartItem(cartItemId) {
            this.currentActionType = 'remove_cart_item';
            if (!confirm('Xóa sản phẩm này khỏi giỏ?')) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, { method: 'DELETE' }, 'cartAction', cartItemId);
                this.cart = result.cart;
                this.showToast(result.msg || 'Đã xóa sản phẩm.', 'success');
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async clearUserCart() {
            this.currentActionType = 'clear_cart';
            if (!confirm('Xóa toàn bộ giỏ hàng?')) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart`, { method: 'DELETE' }, 'cartAction', 'clear_cart');
                this.cart = result.cart;
                this.showToast(result.msg || 'Đã xóa giỏ hàng.', 'success');
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },

        // --- ORDERS ---
        proceedToCheckout() { this.showCheckoutForm = true; },
        async handlePlaceOrder() {
            this.currentActionType = 'place_order';
            if (!this.shippingAddress.trim()) { this.showToast("Vui lòng nhập địa chỉ giao hàng.", 'error'); return; }
            try {
                const newOrder = await this.fetchWithAuth(`${API_BASE_URL}/orders`, {
                    method: 'POST',
                    body: JSON.stringify({ shipping_address: this.shippingAddress }),
                }, 'orderAction');
                this.showToast(`Đặt hàng thành công! Mã ĐH: #${newOrder.id}`, 'success');
                this.cart = { items: [], total_price: 0 }; this.shippingAddress = ''; this.showCheckoutForm = false;
                this.loadUserOrders(); this.loadProductsPublic();
                if(this.canManageProducts) this.loadManagedProducts();
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async loadUserOrders() {
            if (!this.isLoggedIn) return;
            let queryParams = `page=${this.paginationOrders.page}&per_page=${this.paginationOrders.per_page}&sort_by=created_at&order=desc`;
            if(this.orderFilters.status) queryParams += `&status=${this.orderFilters.status}`;

            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders?${queryParams}`, {}, 'orders');
                this.orders = result.data.map(order => ({...order, new_status_to_update: order.status}));
                this.paginationOrders = result.meta;
            } catch (error) { this.orders = []; /* fetchWithAuth đã showToast lỗi */ }
        },
        applyOrderFiltersAndSort(){ this.paginationOrders.page = 1; this.loadUserOrders(); },
        changeOrderPage(newPage){ this.paginationOrders.page = newPage; this.loadUserOrders(); },
        canCancelOrder(status) { return ['pending', 'processing'].includes(status) && this.isBuyer; },
        async cancelUserOrder(orderId) {
            this.currentActionType = 'cancel_order';
            if (!confirm(`Hủy đơn hàng #${orderId}?`)) return;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/cancel`, { method: 'POST' }, 'orderAction', orderId);
                this.showToast(result.message || result.msg || "Đã hủy đơn hàng.", 'success');
                this.loadUserOrders(); this.loadProductsPublic();
                if(this.canManageProducts) this.loadManagedProducts();
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        },
        async updateOrderStatus(orderId, newStatus) {
            this.currentActionType = 'update_status';
            const order = this.orders.find(o => o.id === orderId);
            if (!order || !newStatus) { this.showToast('Lỗi: Không tìm thấy đơn hàng hoặc trạng thái mới.', 'error'); return; }
            if (!this.canManageOrders) { this.showToast("Bạn không có quyền.", 'error'); return; }
            
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                }, 'orderAction', orderId);
                this.showToast(result.message || 'Cập nhật trạng thái thành công!', 'success');
                this.loadUserOrders(); // Tải lại toàn bộ danh sách đơn hàng để đảm bảo đồng bộ
            } catch (error) { /* fetchWithAuth đã showToast lỗi */ }
        }
    },
    mounted() {
        this.updateLoginState();
        if (this.isLoggedIn) {
            this.loadInitialDataForUser();
            this.setView('productsPublic'); // Hoặc view mặc định khác
        } else {
            this.currentView = 'login'; // Mặc định là form login nếu chưa đăng nhập
        }
    },
    watch: {
        isLoggedIn(newVal, oldVal) {
            if (newVal === false && oldVal === true) { // Vừa logout
                this.currentView = 'login';
            }
        },
        currentView(newView) {
             // Tự động tải dữ liệu khi tab được chọn (nếu chưa có dữ liệu)
            if (this.isLoggedIn) {
                if (newView === 'productsPublic' && this.productsPublic.length === 0) this.loadProductsPublic();
                if (newView === 'productManagement' && this.canManageProducts && this.products.length === 0) this.loadManagedProducts();
                if (newView === 'cart' && this.isBuyer && (!this.cart.items || this.cart.items.length === 0)) this.loadUserCart();
                if (newView === 'orders' && this.orders.length === 0) this.loadUserOrders();
            }
        }
    }
});
app.mount('#app');