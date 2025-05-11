// frontend/script.js
const API_BASE_URL = 'http://127.0.0.1:5000';
const ALLOWED_ORDER_STATUSES_GLOBAL = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'failed'];

const app = Vue.createApp({
    data() {
        return {
            // System
            currentView: 'productsPublicWithSidebar',
            isLoading: { 
                auth: false, 
                productsPublic: false, 
                productForm: false, 
                deleteProduct: null, 
                cart: false, 
                cartAction: null, 
                currentCartActionTarget: null,
                orders: false, 
                orderAction: null,
                currentOrderActionTarget: null
            },
            toasts: [],
            
            // Auth
            isLoggedIn: false,
            username: '',
            userId: null,
            userRole: '',
            loginForm: { username: '', password: '' },
            registerForm: { username: '', password: '', role: 'buyer' },
            
            // Products
            productsPublic: [],
            paginationPublic: { page: 1, per_page: 9, total_pages: 1, total_items: 0, prev_page_url: null, next_page_url: null },
            filters: { manufacturer: '', model_name_contains: '', price_min: null, price_max: null },
            sort: { sortBy: 'id', order: 'asc' },
            
            productsManaged: [],
            paginationManaged: { page: 1, per_page: 10, total_pages: 1, total_items: 0, prev_page_url: null, next_page_url: null },
            productForm: { id: null, model_name: '', manufacturer: '', price: '', stock_quantity: null, specifications: '' }, 
            
            // Cart
            cart: { items: [], total_price: 0, user_id: null },
            shippingAddress: '',

            // Orders
            orders: [],
            paginationOrders: { page: 1, per_page: 5, total_pages: 1, total_items: 0, prev_page_url: null, next_page_url: null },
            orderFilters: { status: ''},
            allowedOrderStatuses: ALLOWED_ORDER_STATUSES_GLOBAL,

            // Bootstrap Modal Instances
            loginModalInstance: null,
            registerModalInstance: null,
            productFormModalInstance: null,
            checkoutModalInstance: null,
            bootstrapToastInstances: {},
        };
    },
    computed: {
        isBuyer() { return this.isLoggedIn && this.userRole === 'buyer'; },
        isSeller() { return this.isLoggedIn && this.userRole === 'seller'; },
        isAdmin() { return this.isLoggedIn && this.userRole === 'admin'; },
        canManageProducts() { return this.isSeller || this.isAdmin; },
        canManageOrders() { return this.isSeller || this.isAdmin; },
        cartItemCount() {
            return this.cart && this.cart.items ? this.cart.items.reduce((sum, item) => sum + item.quantity, 0) : 0;
        }
    },
    methods: {
        // --- MODAL CONTROL ---
        openLoginModal() { if (this.loginModalInstance) this.loginModalInstance.show(); },
        openRegisterModal() { if (this.registerModalInstance) this.registerModalInstance.show(); },
        openProductFormModal(product = null) {
            if (product) {
                this.productForm = { 
                    id: product.id,
                    model_name: product.model_name,
                    manufacturer: product.manufacturer,
                    price: product.price != null ? product.price.toString() : '',
                    stock_quantity: product.stock_quantity != null ? Number(product.stock_quantity) : null,
                    specifications: product.specifications || ''
                };
            } else {
                this.productForm = { id: null, model_name: '', manufacturer: '', price: '', stock_quantity: null, specifications: '' };
            }
            if (this.productFormModalInstance) this.productFormModalInstance.show();
        },
        openCheckoutModal() { 
            if (this.cart.items && this.cart.items.some(i => i.quantity > i.phone.stock_quantity)) {
                this.showToast('Một số sản phẩm trong giỏ vượt quá số lượng tồn kho. Vui lòng điều chỉnh.', 'Lỗi giỏ hàng', 'warning');
                this.setView('cart');
                return;
            }
            if (this.checkoutModalInstance) this.checkoutModalInstance.show(); 
        },
        hideModal(modalInstance) { if (modalInstance) modalInstance.hide(); },
        switchToRegisterModal() { this.hideModal(this.loginModalInstance); this.openRegisterModal(); },
        switchToLoginModal() { this.hideModal(this.registerModalInstance); this.openLoginModal(); },

        // --- UI & UTILITIES ---
        showToast(message, title = 'Thông báo', type = 'info', duration = 4000) {
            const id = 'toast-' + Date.now();
            this.toasts.push({ id, message, title, type });
            this.$nextTick(() => {
                const toastElement = this.$refs.toastElements?.find(el => el.dataset.toastId === id);
                if (toastElement) {
                    const bsToast = new bootstrap.Toast(toastElement, { delay: duration, autohide: true });
                    bsToast.show();
                    this.bootstrapToastInstances[id] = bsToast; 
                    toastElement.addEventListener('hidden.bs.toast', () => {
                        this.removeToast(id, false); 
                    }, { once: true });
                }
            });
        },
        removeToast(toastId, destroyInstance = true) {
            this.toasts = this.toasts.filter(toast => toast.id !== toastId);
            if (destroyInstance && this.bootstrapToastInstances[toastId]) {
                delete this.bootstrapToastInstances[toastId];
            }
        },
        formatCurrency(value) { return value != null ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(value) : ''; },
        formatDate(dateString, includeTime = false) {
            if (!dateString) return 'N/A';
            const options = { year: 'numeric', month: 'short', day: 'numeric' };
            if (includeTime) { options.hour = '2-digit'; options.minute = '2-digit'; }
            return new Date(dateString).toLocaleDateString('vi-VN', options);
        },
        getStatusColor(status) {
             const colors = { pending: '#ffc107', processing: '#17a2b8', shipped: '#0d6efd', delivered: '#198754', cancelled: '#dc3545', failed: '#6c757d' };
             return colors[status] || '#212529';
        },
        truncateText(text, length = 100) {
            if (text && text.length > length) return text.substring(0, length) + '...';
            return text;
        },
        getProductImage(phone) {
            // Tạm thời không load ảnh để tránh lỗi net::ERR_NAME_NOT_RESOLVED
            return ""; // Trả về string rỗng hoặc một path ảnh placeholder cục bộ nếu có
            // return `images/default-product.png`; // Nếu bạn có ảnh này
        },
        getStockStatusClass(stock_quantity) {
            if (stock_quantity === 0) return 'stock-out-of-stock';
            if (stock_quantity > 0 && stock_quantity < 10) return 'stock-low-stock';
            return 'stock-in-stock';
        },
        getStockStatusText(stock_quantity) {
            if (stock_quantity === 0) return 'Hết hàng';
            if (stock_quantity > 0 && stock_quantity < 10) return `Sắp hết: ${stock_quantity}`;
            return `Còn: ${stock_quantity}`;
        },
        simplePageRange(currentPage, totalPages, wingSize = 2) {
            const range = [];
            let start = Math.max(1, currentPage - wingSize);
            let end = Math.min(totalPages, currentPage + wingSize);
            if (totalPages <= (wingSize * 2 + 1)) { 
                start = 1;
                end = totalPages;
            } else {
                 if (currentPage - wingSize <= 1) {
                    end = Math.min(totalPages, 1 + (wingSize * 2));
                }
                if (currentPage + wingSize >= totalPages) {
                    start = Math.max(1, totalPages - (wingSize * 2));
                }
            }
            for (let i = start; i <= end; i++) { range.push(i); }
            return range;
        },

        // --- API Calls ---
        getToken() { return localStorage.getItem('accessToken'); },
        storeToken(token) { localStorage.setItem('accessToken', token); },
        removeToken() {
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userId');
            localStorage.removeItem('username');
            localStorage.removeItem('userRole');
        },
        storeUserDetails(userId, role, username) {
            localStorage.setItem('userId', userId);
            localStorage.setItem('userRole', role);
            localStorage.setItem('username', username);
        },
        async fetchWithAuth(url, options = {}, actionKey = null, itemId = null) {
            if (actionKey) {
                if (itemId !== null && itemId !== undefined) this.isLoading[actionKey] = itemId;
                else this.isLoading[actionKey] = true;
            }
            const token = this.getToken();
            const headers = { 'Content-Type': 'application/json', ...options.headers };
            if (token) { headers['Authorization'] = `Bearer ${token}`; }
            
            console.log(`Workspaceing: ${options.method || 'GET'} ${url}`); // Log request
            if (options.body) console.log("Request body:", options.body);

            try {
                const response = await fetch(url, { ...options, headers });
                console.log(`Response status for ${url}: ${response.status}`); // Log status

                if (response.status === 204) {
                    console.log("Response 204 No Content");
                    return null;
                }

                const responseData = await response.json();
                console.log("Response data:", responseData); // Log response data

                if (!response.ok) {
                    const error = new Error(responseData.error?.message || responseData.msg || responseData.message || `Lỗi HTTP ${response.status}`);
                    error.response = responseData; 
                    error.status = response.status;
                    throw error;
                }
                return responseData;
            } catch (error) {
                console.error(`API call to ${url} FAILED:`, error); // Log lỗi chi tiết hơn
                // if (error.message.includes('Failed to fetch')) {
                //     this.showToast('Không thể kết nối đến máy chủ API. Vui lòng kiểm tra lại.', 'Lỗi Mạng', 'danger');
                // } else 
                if (error.status !== 401) { // 401 thường do token hết hạn, đã xử lý ở updateLoginState
                    this.showToast(error.message || 'Có lỗi từ API hoặc không thể kết nối.', 'Lỗi API', 'danger');
                }
                throw error; // Ném lại lỗi để các hàm gọi có thể bắt
            } finally {
                if (actionKey) this.isLoading[actionKey] = false;
            }
        },

        // --- VIEW MANAGEMENT ---
        setView(viewName) {
            this.currentView = viewName;
            if (viewName === 'productsPublicWithSidebar' && (this.productsPublic.length === 0 || Object.keys(this.filters).some(k => this.filters[k]))) {
                this.loadProductsPublic();
            }
            if (viewName === 'productManagement' && this.canManageProducts && this.productsManaged.length === 0) {
                this.loadManagedProducts();
            }
            if (viewName === 'cart' && this.isBuyer) { 
                this.loadUserCart();
            }
            if (viewName === 'orders' && this.isLoggedIn && this.orders.length === 0) {
                this.loadUserOrders();
            }
            if (this.loginModalInstance && viewName !== 'loginModal') this.loginModalInstance.hide();
            if (this.registerModalInstance && viewName !== 'registerModal') this.registerModalInstance.hide();
            if (this.productFormModalInstance && viewName !== 'productFormModal') this.productFormModalInstance.hide();
            if (this.checkoutModalInstance && viewName !== 'checkoutModal') this.checkoutModalInstance.hide();
        },

        // --- AUTH ---
        async handleLogin() {
            this.isLoading.auth = true;
            try {
                // URL cho login là /auth/login (KHÔNG có / cuối)
                const data = await this.fetchWithAuth(`${API_BASE_URL}/auth/login`, {
                    method: 'POST',
                    body: JSON.stringify(this.loginForm),
                });
                if (data.access_token) {
                    this.storeToken(data.access_token);
                    const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
                    this.storeUserDetails(tokenPayload.sub, tokenPayload.role, tokenPayload.username);
                    this.updateLoginState();
                    this.showToast(`Chào mừng ${this.username} trở lại!`, 'Đăng nhập thành công', 'success');
                    this.loginForm = { username: '', password: '' };
                    this.hideModal(this.loginModalInstance);
                    this.loadInitialDataForUser();
                    this.setView('productsPublicWithSidebar');
                }
            } catch (error) { 
                 console.error("Lỗi đăng nhập trong handleLogin:", error);
            }
            finally { this.isLoading.auth = false; }
        },
        async handleRegister() {
            this.isLoading.auth = true;
            if (this.registerForm.password.length < 6) {
                this.showToast('Mật khẩu phải có ít nhất 6 ký tự.', 'Lỗi đăng ký', 'warning');
                this.isLoading.auth = false;
                return;
            }
            try {
                // URL cho register là /auth/register (KHÔNG có / cuối)
                await this.fetchWithAuth(`${API_BASE_URL}/auth/register`, {
                    method: 'POST',
                    body: JSON.stringify(this.registerForm),
                });
                this.showToast('Đăng ký thành công! Vui lòng đăng nhập.', 'Thành công', 'success');
                this.registerForm = { username: '', password: '', role: 'buyer' };
                this.hideModal(this.registerModalInstance);
                this.openLoginModal();
            } catch (error) { 
                console.error("Lỗi đăng ký trong handleRegister:", error);
            }
            finally { this.isLoading.auth = false; }
        },
        logoutUser() {
            this.removeToken();
            this.updateLoginState();
            this.showToast('Bạn đã đăng xuất.', 'Thông báo', 'info');
            this.cart = { items: [], total_price: 0, user_id: null }; 
            this.orders = []; 
            this.productsManaged = []; 
            this.setView('productsPublicWithSidebar');
        },
        updateLoginState() {
            const token = this.getToken();
            if (token) {
                try {
                    const tokenPayload = JSON.parse(atob(token.split('.')[1]));
                    const now = Date.now() / 1000;
                    if (tokenPayload.exp && tokenPayload.exp < now) {
                        this.removeToken();
                        this.isLoggedIn = false; this.userId = null; this.username = ''; this.userRole = '';
                        // this.showToast('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.', 'Thông báo', 'warning'); // Bỏ toast ở đây
                        return;
                    }
                    this.isLoggedIn = true;
                    this.userId = localStorage.getItem('userId');
                    this.username = localStorage.getItem('username') || '';
                    this.userRole = localStorage.getItem('userRole') || '';
                } catch (e) {
                    this.removeToken();
                    this.isLoggedIn = false; this.userId = null; this.username = ''; this.userRole = '';
                }
            } else {
                this.isLoggedIn = false; this.userId = null; this.username = ''; this.userRole = '';
            }
        },
        loadInitialDataForUser() {
            if (this.isLoggedIn) {
                if (this.currentView === 'productsPublicWithSidebar' || this.productsPublic.length === 0) {
                    this.loadProductsPublic();
                }
                if (this.isBuyer) { this.loadUserCart(false); }
            } else {
                 if (this.currentView === 'productsPublicWithSidebar' || this.productsPublic.length === 0) {
                    this.loadProductsPublic();
                }
            }
        },

        // --- PRODUCTS (Public Listing & Filtering) ---
        async loadProductsPublic() {
            this.isLoading.productsPublic = true;
            let queryParams = `page=${this.paginationPublic.page}&per_page=${this.paginationPublic.per_page}`;
            queryParams += `&sort_by=${this.sort.sortBy}&order=${this.sort.order}`;
            for (const key in this.filters) {
                if (this.filters[key] !== '' && this.filters[key] !== null && this.filters[key] !== undefined) {
                    queryParams += `&${key}=${encodeURIComponent(this.filters[key])}`;
                }
            }
            try {
                // **SỬA Ở ĐÂY: URL /phones/ (có / cuối)**
                const result = await this.fetchWithAuth(`${API_BASE_URL}/phones/?${queryParams}`);
                this.productsPublic = result.data;
                this.paginationPublic = result.meta;
            } catch (error) { 
                this.productsPublic = []; 
                this.paginationPublic = { page: 1, per_page: 9, total_pages: 1, total_items: 0, prev_page_url: null, next_page_url: null };
            } finally {
                this.isLoading.productsPublic = false;
            }
        },
        applyFiltersAndSort() { this.paginationPublic.page = 1; this.loadProductsPublic(); },
        resetFiltersAndSort() {
            this.filters = { manufacturer: '', model_name_contains: '', price_min: null, price_max: null };
            this.sort = { sortBy: 'id', order: 'asc' };
            this.applyFiltersAndSort();
        },
        changePagePublic(newPage) {
            if (newPage >= 1 && newPage <= this.paginationPublic.total_pages && newPage !== this.paginationPublic.page) {
                this.paginationPublic.page = newPage;
                this.loadProductsPublic();
            }
        },

        // --- PRODUCTS (Management - Seller/Admin) ---
        async loadManagedProducts(page = 1) {
            if (!this.canManageProducts) return;
            this.isLoading.productForm = true; 
            let queryParams = `page=${page}&per_page=${this.paginationManaged.per_page}&sort_by=id&order=desc`;
            try {
                 // **SỬA Ở ĐÂY: URL /phones/ (có / cuối)**
                const result = await this.fetchWithAuth(`${API_BASE_URL}/phones/?${queryParams}`);
                if (this.isSeller) {
                    this.productsManaged = result.data.filter(p => p.user_id == this.userId || p.added_by_user_id == this.userId);
                } else {
                     this.productsManaged = result.data;
                }
                this.paginationManaged = result.meta;
            } catch (error) { this.productsManaged = []; }
            finally { this.isLoading.productForm = false; }
        },
        changePageManaged(newPage) {
             if (newPage >= 1 && newPage <= this.paginationManaged.total_pages && newPage !== this.paginationManaged.page) {
                this.paginationManaged.page = newPage;
                this.loadManagedProducts(newPage);
            }
        },
        async handleSaveProduct() {
            this.isLoading.productForm = true;
            const productData = { ...this.productForm };
            
            productData.price = parseFloat(this.productForm.price); 
            productData.stock_quantity = parseInt(this.productForm.stock_quantity);

            if (isNaN(productData.price) || productData.price < 0 || 
                isNaN(productData.stock_quantity) || productData.stock_quantity < 0) {
                this.showToast('Giá và tồn kho phải là số không âm hợp lệ.', 'Lỗi dữ liệu', 'warning');
                this.isLoading.productForm = false;
                return;
            }
            try {
                if (productData.id) { 
                    await this.fetchWithAuth(`${API_BASE_URL}/phones/${productData.id}`, { 
                        method: 'PUT',
                        body: JSON.stringify(productData)
                    });
                    this.showToast('Cập nhật sản phẩm thành công!', 'Thành công', 'success');
                } else { 
                    const { id, ...createData } = productData;
                     // **SỬA Ở ĐÂY: URL /phones/ (có / cuối)**
                    await this.fetchWithAuth(`${API_BASE_URL}/phones/`, { 
                        method: 'POST',
                        body: JSON.stringify(createData)
                    });
                    this.showToast('Thêm sản phẩm thành công!', 'Thành công', 'success');
                }
                this.hideModal(this.productFormModalInstance);
                this.loadManagedProducts();
                this.loadProductsPublic();
            } catch (error) { 
                console.error("Lỗi khi lưu sản phẩm:", error);
            } finally {
                this.isLoading.productForm = false;
            }
        },
        async handleDeleteProduct(phoneId) {
            if (!confirm(`Bạn có chắc muốn xóa sản phẩm ID: ${phoneId}?`)) return;
            this.isLoading.deleteProduct = phoneId;
            try {
                await this.fetchWithAuth(`${API_BASE_URL}/phones/${phoneId}`, { method: 'DELETE' });
                this.showToast('Xóa sản phẩm thành công!', 'Thành công', 'success');
                this.loadManagedProducts(this.paginationManaged.page); 
                this.loadProductsPublic();
                if (this.productForm.id === phoneId) {
                    this.hideModal(this.productFormModalInstance);
                }
            } catch (error) { /* fetchWithAuth đã xử lý */ }
            finally { this.isLoading.deleteProduct = null; }
        },
        canEditOrDeleteProduct(phone) {
            if (!this.isLoggedIn) return false;
            if (this.isAdmin) return true;
            return this.isSeller && (phone.user_id == this.userId || phone.added_by_user_id == this.userId);
        },

        // --- CART (Buyer) ---
        async loadUserCart(showLoadingIndicator = true) {
            if (!this.isBuyer) { this.cart = { items: [], total_price: 0, user_id: null }; return; }
            if (showLoadingIndicator) this.isLoading.cart = true;
            try {
                 // **SỬA Ở ĐÂY: URL /cart/ (có / cuối)**
                const cartData = await this.fetchWithAuth(`${API_BASE_URL}/cart/`); 
                this.cart = cartData || { items: [], total_price: 0, user_id: this.userId };
            } catch (error) { this.cart = { items: [], total_price: 0, user_id: this.userId }; }
            finally { if (showLoadingIndicator) this.isLoading.cart = false; }
        },
        async addItemToCart(phoneId, quantity = 1) {
            if (!this.isBuyer) { this.showToast('Vui lòng đăng nhập để mua hàng.', 'Thông báo', 'info'); this.openLoginModal(); return; }
            this.isLoading.cartAction = phoneId; 
            this.isLoading.currentCartActionTarget = phoneId;
            try {
                const updatedCart = await this.fetchWithAuth(`${API_BASE_URL}/cart/items`, { 
                    method: 'POST',
                    body: JSON.stringify({ phone_id: parseInt(phoneId), quantity }),
                });
                this.cart = updatedCart;
                this.showToast('Đã thêm vào giỏ!', 'Thành công', 'success');
            } catch (error) { /* fetchWithAuth đã xử lý */ }
            finally { this.isLoading.cartAction = null; this.isLoading.currentCartActionTarget = null; }
        },
        async updateCartItemQuantity(cartItemId, newQuantityStr) {
            const newQuantity = parseInt(newQuantityStr);
            const itemInCart = this.cart.items.find(item => item.id === cartItemId);
            if (!itemInCart) return;

            if (isNaN(newQuantity) || newQuantity < 0) {
                this.showToast('Số lượng không hợp lệ.', 'Lỗi', 'warning');
                this.$forceUpdate(); 
                return;
            }
            if (newQuantity === 0) {
                this.confirmRemoveCartItem(cartItemId);
                return;
            }
            if (newQuantity > itemInCart.phone.stock_quantity) {
                this.showToast(`Chỉ còn ${itemInCart.phone.stock_quantity} sản phẩm trong kho.`, 'Thông báo', 'info');
                this.$forceUpdate();
                return; 
            }

            this.isLoading.cartAction = cartItemId;
            this.isLoading.currentCartActionTarget = cartItemId;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, {
                    method: 'PUT',
                    body: JSON.stringify({ quantity: newQuantity }),
                });
                this.cart = result.cart;
            } catch (error) { this.loadUserCart(); }
            finally { this.isLoading.cartAction = null; this.isLoading.currentCartActionTarget = null;}
        },
        confirmRemoveCartItem(cartItemId) {
            if (confirm('Bạn có chắc muốn xóa sản phẩm này khỏi giỏ hàng?')) {
                this.removeCartItem(cartItemId);
            }
        },
        async removeCartItem(cartItemId) {
            this.isLoading.cartAction = cartItemId;
            this.isLoading.currentCartActionTarget = cartItemId;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, { method: 'DELETE' });
                this.cart = result.cart;
                this.showToast(result.msg || 'Đã xóa sản phẩm khỏi giỏ.', 'Thành công', 'success');
            } catch (error) { this.loadUserCart(); }
            finally { this.isLoading.cartAction = null; this.isLoading.currentCartActionTarget = null;}
        },
        async clearUserCart() {
            if (!confirm('Bạn có chắc muốn xóa toàn bộ sản phẩm trong giỏ hàng?')) return;
            this.isLoading.cartAction = 'clear_cart';
            try {
                 // **SỬA Ở ĐÂY: URL /cart/ (có / cuối)**
                const result = await this.fetchWithAuth(`${API_BASE_URL}/cart/`, { method: 'DELETE' });
                this.cart = result.cart;
                this.showToast(result.msg || 'Đã xóa toàn bộ giỏ hàng.', 'Thành công', 'success');
            } catch (error) { this.loadUserCart(); }
            finally { this.isLoading.cartAction = null; }
        },

        // --- ORDERS ---
        async handlePlaceOrder() {
            if (!this.shippingAddress.trim() || this.shippingAddress.trim().length < 5) {
                this.showToast("Vui lòng nhập địa chỉ giao hàng hợp lệ (ít nhất 5 ký tự).", 'Lỗi đặt hàng', 'warning');
                return;
            }
            if (this.cart.items && this.cart.items.some(i => i.quantity > i.phone.stock_quantity)) {
                this.showToast('Một số sản phẩm trong giỏ vượt quá số lượng tồn kho. Vui lòng điều chỉnh.', 'Lỗi giỏ hàng', 'warning');
                this.hideModal(this.checkoutModalInstance); 
                this.setView('cart'); 
                return;
            }
            this.isLoading.orderAction = true;
            try {
                // **SỬA Ở ĐÂY: URL /orders/ (có / cuối)**
                const newOrder = await this.fetchWithAuth(`${API_BASE_URL}/orders/`, { 
                    method: 'POST',
                    body: JSON.stringify({ shipping_address: this.shippingAddress }),
                });
                this.showToast(`Đặt hàng thành công! Mã ĐH: #${newOrder.id}`, 'Thành công', 'success');
                this.shippingAddress = '';
                this.hideModal(this.checkoutModalInstance);
                await this.loadUserCart(); 
                await this.loadProductsPublic(); 
                if (this.canManageProducts) await this.loadManagedProducts();
                this.setView('orders');
            } catch (error) { /* fetchWithAuth đã xử lý */ }
            finally { this.isLoading.orderAction = false; }
        },
        async loadUserOrders(page = 1) {
            if (!this.isLoggedIn) return;
            this.isLoading.orders = true;
            let queryParams = `page=${page}&per_page=${this.paginationOrders.per_page}&sort_by=created_at&order=desc`;
            if (this.orderFilters.status) {
                queryParams += `&status=${this.orderFilters.status}`;
            }
            try {
                 // **SỬA Ở ĐÂY: URL /orders/ (có / cuối)**
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/?${queryParams}`);
                this.orders = result.data.map(order => ({...order, new_status_to_update: order.status}));
                this.paginationOrders = result.meta;
            } catch (error) { this.orders = []; }
            finally { this.isLoading.orders = false; }
        },
        applyOrderFiltersAndSort(){ this.paginationOrders.page = 1; this.loadUserOrders(); },
        changeOrderPage(newPage){
            if (newPage >= 1 && newPage <= this.paginationOrders.total_pages && newPage !== this.paginationOrders.page) {
                this.paginationOrders.page = newPage;
                this.loadUserOrders(newPage);
            }
        },
        async cancelUserOrder(orderId) {
            if (!confirm(`Bạn có chắc muốn hủy đơn hàng #${orderId}?`)) return;
            this.isLoading.orderAction = true;
            this.isLoading.currentOrderActionTarget = orderId;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/cancel`, { method: 'POST' });
                this.showToast(result.message || "Đã hủy đơn hàng.", 'Thành công', 'success');
                this.loadUserOrders(this.paginationOrders.page);
                this.loadProductsPublic();
                if (this.canManageProducts) this.loadManagedProducts();
            } catch (error) { /* fetchWithAuth đã xử lý */ }
            finally { this.isLoading.orderAction = false; this.isLoading.currentOrderActionTarget = null;}
        },
        async updateOrderStatus(orderId, newStatus) {
            const order = this.orders.find(o => o.id === orderId);
            if (!order || !newStatus || newStatus === order.status) {
                this.showToast('Vui lòng chọn một trạng thái mới khác trạng thái hiện tại.', 'Thông báo', 'info');
                return;
            }
            this.isLoading.orderAction = true;
            this.isLoading.currentOrderActionTarget = orderId;
            try {
                const result = await this.fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/status`, {
                    method: 'PUT',
                    body: JSON.stringify({ status: newStatus })
                });
                this.showToast(result.message || 'Cập nhật trạng thái thành công!', 'Thành công', 'success');
                this.loadUserOrders(this.paginationOrders.page);
                if (newStatus === 'cancelled') {
                    this.loadProductsPublic();
                    if (this.canManageProducts) this.loadManagedProducts();
                }
            } catch (error) { /* fetchWithAuth đã xử lý */ }
             finally { this.isLoading.orderAction = false; this.isLoading.currentOrderActionTarget = null; }
        },
        allowedOrderStatusesForUpdate(currentStatus) {
            if (this.isAdmin) return ALLOWED_ORDER_STATUSES_GLOBAL.filter(s => s !== currentStatus && s !== 'failed');
            if (this.isSeller) {
                 if (currentStatus === 'pending') return ['processing', 'shipped', 'cancelled'];
                 if (currentStatus === 'processing') return ['shipped', 'cancelled'];
            }
            return [currentStatus]; 
        },
    },
    mounted() {
        this.updateLoginState();
        this.loadInitialDataForUser();

        this.$nextTick(() => {
            if (document.getElementById('loginModalVue')) this.loginModalInstance = new bootstrap.Modal(document.getElementById('loginModalVue'));
            if (document.getElementById('registerModalVue')) this.registerModalInstance = new bootstrap.Modal(document.getElementById('registerModalVue'));
            if (document.getElementById('productFormModalVue')) this.productFormModalInstance = new bootstrap.Modal(document.getElementById('productFormModalVue'));
            if (document.getElementById('checkoutModalVue')) this.checkoutModalInstance = new bootstrap.Modal(document.getElementById('checkoutModalVue'));
        });
    }
});
app.mount('#app');