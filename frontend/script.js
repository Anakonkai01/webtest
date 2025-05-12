// frontend/script.js
import { fetchWithAuth, API_BASE_URL, getToken, removeToken } from './services/api.js';

const ALLOWED_ORDER_STATUSES_GLOBAL = ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'failed'];

const { createApp } = Vue;

const app = createApp({
    data() {
        return {
            currentView: 'productsPublic',
            isLoading: {
                login: false, register: false, productsPublic: false, productDetail: false,
                productForm: false, productManagement: false, deleteProduct: null,
                cart: false, cartAction: null,
                orders: false, orderDetail: false, orderAction: null,
            },
            toasts: [], apiResponse: null,
            isLoggedIn: false, username: '', userId: null, userRole: '',
            loginForm: { username: '', password: '' },
            registerForm: { username: '', password: '', role: 'buyer' },
            productsPublic: [],
            productFilters: { manufacturer: '', model_name_contains: '', price_min: null, price_max: null },
            productSort: { sortBy: 'id', order: 'asc' },
            paginationPublic: { page: 1, per_page: 9, total_pages: 1, total_items: 0 },
            currentProductDetail: null,
            productsManaged: [],
            productForm: { id: null, model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' },
            cart: { items: [], total_price: 0, user_id: null },
            shippingAddress: '',
            orders: [],
            orderFilters: { status: '' },
            orderSort: { sortBy: 'created_at', order: 'desc' },
            paginationOrders: { page: 1, per_page: 5, total_pages: 1, total_items: 0 },
            currentOrderDetail: null,
            bootstrapModals: {}, toastRefs: {},
        };
    },
    computed: {
        isBuyer() { return this.userRole === 'buyer'; },
        isSeller() { return this.userRole === 'seller'; },
        isAdmin() { return this.userRole === 'admin'; },
        canManageProducts() { return this.isSeller || this.isAdmin; },
        canManageOrders() { return this.isSeller || this.isAdmin; },
        cartItemCount() { return this.cart?.items?.reduce((sum, item) => sum + item.quantity, 0) || 0; },
        allowedOrderStatuses() { return ALLOWED_ORDER_STATUSES_GLOBAL; }
    },
    methods: {
        setToastRef(el, id) { if (el) this.toastRefs[id] = el; },
        showToast(message, title = 'Thông báo', type = 'info', duration = 4000) {
            const id = 'toast-' + Date.now(); this.toasts.push({ id, message, title, type });
            this.$nextTick(() => {
                const toastElement = this.toastRefs[id];
                if (toastElement) {
                    const bsToast = new bootstrap.Toast(toastElement, { delay: duration, autohide: true });
                    bsToast.show();
                    toastElement.addEventListener('hidden.bs.toast', () => { this.removeToast(id); delete this.toastRefs[id]; }, { once: true });
                }
            });
        },
        removeToast(toastId) { this.toasts = this.toasts.filter(t => t.id !== toastId); },
        formatCurrency(v) { return v != null ? new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v) : ''; },
        formatDate(d, time) { if (!d) return 'N/A'; const opts = { year: 'numeric', month: 'short', day: 'numeric' }; if (time) { opts.hour = '2-digit'; opts.minute = '2-digit'; } return new Date(d).toLocaleDateString('vi-VN', opts); },
        getStatusColor(s) { const c = { pending: '#ffc107', processing: '#17a2b8', shipped: '#0d6efd', delivered: '#198754', cancelled: '#dc3545', failed: '#6c757d' }; return c[s] || '#212529'; },
        simplePageRange(currentPage, totalPages, wingSize = 2) {
            const range = []; let start = Math.max(1, currentPage - wingSize); let end = Math.min(totalPages, currentPage + wingSize);
            if (totalPages <= (wingSize * 2 + 1)) { start = 1; end = totalPages; }
            else { if (currentPage - wingSize <= 1) end = Math.min(totalPages, 1 + (wingSize * 2)); if (currentPage + wingSize >= totalPages) start = Math.max(1, totalPages - (wingSize * 2)); }
            for (let i = start; i <= end; i++) range.push(i); return range;
        },
        getModal(id) {
            if (!this.bootstrapModals[id]) {
                const el = document.getElementById(id);
                if (el) this.bootstrapModals[id] = new bootstrap.Modal(el);
                else { console.error(`Modal '${id}' not found.`); return null; }
            }
            return this.bootstrapModals[id];
        },

        setView(viewName) {
            this.currentView = viewName;
            this.apiResponse = null;

            if (viewName !== 'productDetail') {
                this.currentProductDetail = null;
            }
            if (viewName !== 'orderDetail') {
                this.currentOrderDetail = null;
            }

            if (viewName === 'productsPublic' && (this.productsPublic.length === 0 || !this.isLoading.productsPublic) ) this.loadProductsPublic();
            else if (viewName === 'cart' && this.isBuyer) this.loadUserCart();
            else if (viewName === 'orders' && this.isLoggedIn) this.loadUserOrders();
            else if (viewName === 'productManagement' && this.canManageProducts) this.loadManagedProducts();
        },

        checkLoginState() {
            const token = getToken();
            if (token) {
                try {
                    const tokenPayload = JSON.parse(atob(token.split('.')[1]));
                    const now = Date.now() / 1000;
                    if (tokenPayload.exp && tokenPayload.exp < now) { this.clearAuthDataAndNotify("Phiên đăng nhập hết hạn."); return; }
                    this.isLoggedIn = true; this.userId = tokenPayload.sub; this.username = tokenPayload.username; this.userRole = tokenPayload.role;
                    this.loadDataForLoggedInUser();
                } catch (e) { console.error("Token processing error:", e); this.clearAuthDataAndNotify("Lỗi token."); }
            } else { this.clearAuthData(); }
        },
        async handleLogin() {
            this.isLoading.login = true; this.apiResponse = null;
            try {
                const data = await fetchWithAuth(`${API_BASE_URL}/auth/login`, { method: 'POST', body: JSON.stringify(this.loginForm) });
                if (data.access_token) {
                    localStorage.setItem('accessToken', data.access_token); this.checkLoginState();
                    this.showToast('Đăng nhập thành công!', 'Thành công', 'success'); this.getModal('loginModal').hide(); this.loginForm = { username: '', password: '' };
                } else { throw new Error(data.message || "Đăng nhập thất bại."); }
            } catch (error) { this.showToast(error.message || 'Lỗi đăng nhập.', 'Lỗi', 'danger'); }
            finally { this.isLoading.login = false; }
        },
        async handleRegister() {
            if (this.registerForm.password.length < 6) { this.showToast('Mật khẩu >= 6 ký tự.', 'Lỗi', 'warning'); return; }
            this.isLoading.register = true; this.apiResponse = null;
            try {
                await fetchWithAuth(`${API_BASE_URL}/auth/register`, { method: 'POST', body: JSON.stringify(this.registerForm) });
                this.showToast('Đăng ký thành công! Vui lòng đăng nhập.', 'Thành công', 'success');
                this.getModal('registerModal').hide(); this.registerForm = { username: '', password: '', role: 'buyer' }; this.getModal('loginModal').show();
            } catch (error) { this.showToast(error.message || 'Lỗi đăng ký.', 'Lỗi', 'danger');}
            finally { this.isLoading.register = false; }
        },
        logoutUser() { removeToken(); this.clearAuthDataAndNotify('Bạn đã đăng xuất.'); this.setView('productsPublic'); },
        clearAuthData() {
            this.isLoggedIn = false; this.username = ''; this.userId = null; this.userRole = '';
            this.cart = { items: [], total_price: 0, user_id: null }; this.orders = []; this.productsManaged = [];
            this.currentProductDetail = null; this.currentOrderDetail = null; // Cũng reset detail khi logout
        },
        clearAuthDataAndNotify(message) { this.clearAuthData(); if (message) this.showToast(message, 'Thông báo', 'info');},
        loadDataForLoggedInUser() {
            if (this.isBuyer) this.loadUserCart();
            this.loadUserOrders();
            if (this.canManageProducts) this.loadManagedProducts();
        },

        // --- Products ---
        async loadProductsPublic(page = this.paginationPublic.page) {
            this.isLoading.productsPublic = true; this.apiResponse = null;
            this.paginationPublic.page = Number(page);
            let queryParams = `page=${this.paginationPublic.page}&per_page=${this.paginationPublic.per_page}`;
            queryParams += `&sort_by=${this.productSort.sortBy}&order=${this.productSort.order}`;
            for (const key in this.productFilters) {
                if (this.productFilters[key] !== '' && this.productFilters[key] !== null && this.productFilters[key] !== undefined) {
                    queryParams += `&${key}=${encodeURIComponent(this.productFilters[key])}`;
                }
            }
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/phones/?${queryParams}`);
                this.productsPublic = result.data;
                this.paginationPublic = { ...this.paginationPublic, ...result.meta };
                this.apiResponse = result;
            } catch (error) { this.showToast(error.message || 'Lỗi tải sản phẩm.', 'Lỗi', 'danger'); this.productsPublic = [];}
            finally { this.isLoading.productsPublic = false; }
        },
        applyProductFiltersAndSort() { this.loadProductsPublic(1); },
        resetProductFiltersAndSort() {
            this.productFilters = { manufacturer: '', model_name_contains: '', price_min: null, price_max: null };
            this.productSort = { sortBy: 'id', order: 'asc' };
            this.paginationPublic.per_page = 9;
            this.applyProductFiltersAndSort();
        },
        changeProductPage(newPage) {
            if (newPage >= 1 && newPage <= this.paginationPublic.total_pages && newPage !== this.paginationPublic.page) {
                this.loadProductsPublic(newPage);
            }
        },
        async viewProductDetail(phoneId) {
            this.isLoading.productDetail = true;
            this.currentProductDetail = null; 
            this.apiResponse = null;
            console.log(`Workspaceing details for phoneId: ${phoneId}`);
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/phones/${phoneId}`);
                console.log("API result for product detail:", result); 
                if (result && typeof result === 'object' && result.id) { 
                    this.apiResponse = result;
                    this.setView('productDetail'); 
                } else {
                    console.error("Product data not found in API response or invalid format:", result);
                    this.showToast('Không tìm thấy thông tin sản phẩm từ API.', 'Lỗi dữ liệu', 'warning');
                    this.currentProductDetail = null; 

                }
            } catch (error) {
                console.error("Error fetching product detail:", error, error.response); // DEBUG
                this.showToast(error.message || 'Lỗi tải chi tiết sản phẩm.', 'Lỗi', 'danger');
                this.currentProductDetail = null; 
            } finally {
                this.isLoading.productDetail = false;
            }
        },
        openProductFormModal(product = null) {
             if (product) this.productForm = { ...product, price: Number(product.price), stock_quantity: Number(product.stock_quantity) }; // Đảm bảo price, stock là số
             else this.productForm = { id: null, model_name: '', manufacturer: '', price: null, stock_quantity: null, specifications: '' };
        },
        async handleSaveProduct() {
            this.isLoading.productForm = true; this.apiResponse = null;
            if (!this.productForm.model_name?.trim()) { this.showToast('Tên model là bắt buộc.', 'Lỗi', 'warning'); this.isLoading.productForm = false; return; }
            if (!this.productForm.manufacturer?.trim()) { this.showToast('Hãng sản xuất là bắt buộc.', 'Lỗi', 'warning'); this.isLoading.productForm = false; return; }
            const price = parseFloat(this.productForm.price);
            if (isNaN(price) || price < 0) { this.showToast('Giá không hợp lệ.', 'Lỗi', 'warning'); this.isLoading.productForm = false; return; }
            const stock = parseInt(this.productForm.stock_quantity);
            if (isNaN(stock) || stock < 0) { this.showToast('Tồn kho không hợp lệ.', 'Lỗi', 'warning'); this.isLoading.productForm = false; return; }

            const payload = {
                model_name: this.productForm.model_name.trim(),
                manufacturer: this.productForm.manufacturer.trim(),
                price: price,
                stock_quantity: stock,
                specifications: this.productForm.specifications?.trim() || null
            };
            const method = this.productForm.id ? 'PUT' : 'POST';
            let url = `${API_BASE_URL}/phones/`; if (this.productForm.id) url = `${API_BASE_URL}/phones/${this.productForm.id}`;

            try {
                const result = await fetchWithAuth(url, { method, body: JSON.stringify(payload) });
                this.showToast(`Sản phẩm ${this.productForm.id ? 'cập nhật' : 'thêm mới'} thành công!`, 'Thành công', 'success');
                this.apiResponse = result; this.getModal('productFormModal').hide();
                this.loadProductsPublic(); if (this.canManageProducts) this.loadManagedProducts();
            } catch (error) {
                let errMsg = "Lỗi lưu sản phẩm.";
                if (error.response && error.response.description) {
                    let d = error.response.description; errMsg = typeof d === 'object' ? Object.entries(d).map(([k,v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('; ') : String(d);
                } else if (error.message) errMsg = error.message;
                this.showToast(errMsg, 'Lỗi', 'danger'); this.apiResponse = error.response || { error: { message: error.message } };
            } finally { this.isLoading.productForm = false; }
        },
        async handleDeleteProduct(phoneId) {
            if (!confirm(`Xóa SP ID: ${phoneId}?`)) return;
            this.isLoading.deleteProduct = phoneId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/phones/${phoneId}`, { method: 'DELETE' });
                this.showToast(result.message || 'Xóa SP thành công!', 'Thành công', 'success'); // API của bạn có thể trả về message trong result
                this.apiResponse = result;
                this.loadProductsPublic(); if (this.canManageProducts) this.loadManagedProducts();
            } catch (error) { this.showToast(error.message || 'Lỗi xóa SP.', 'Lỗi', 'danger');}
            finally { this.isLoading.deleteProduct = null; }
        },
        async loadManagedProducts() {
            if(!this.canManageProducts) return;
            this.isLoading.productManagement = true;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/phones/?per_page=100&sort_by=id&order=desc`); // Lấy nhiều, sắp xếp theo ID mới nhất
                if (this.isSeller) {
                     this.productsManaged = result.data.filter(p => p.added_by_user_id === this.userId);
                } else if (this.isAdmin) {
                    this.productsManaged = result.data;
                } else { this.productsManaged = []; }
            } catch (error) { this.showToast(error.message || 'Lỗi tải SP quản lý.', 'Lỗi', 'danger'); this.productsManaged = [];}
            finally { this.isLoading.productManagement = false; }
        },

        // --- Cart Methods (Giữ nguyên từ lần trước) ---
        async loadUserCart() {
            if (!this.isBuyer) { this.cart = { items: [], total_price: 0, user_id: null }; return; }
            this.isLoading.cart = true; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/cart/`);
                this.cart = result || { items: [], total_price: 0, user_id: this.userId }; this.apiResponse = result;
            } catch (error) { this.showToast(error.message || 'Lỗi tải giỏ hàng.', 'Lỗi', 'danger'); this.cart = { items: [], total_price: 0, user_id: this.userId };}
            finally { this.isLoading.cart = false; }
        },
        async addItemToCart(phoneId, quantity = 1) {
            if (!this.isLoggedIn) { this.showToast('Vui lòng đăng nhập.', 'Thông báo', 'info'); this.getModal('loginModal').show(); return; }
            if (!this.isBuyer) { this.showToast('Chỉ người mua mới thao tác được.', 'Cảnh báo', 'warning'); return; }
            this.isLoading.cartAction = phoneId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/cart/items`, { method: 'POST', body: JSON.stringify({ phone_id: parseInt(phoneId), quantity: parseInt(quantity) }) });
                this.cart = result; this.apiResponse = result; this.showToast('Đã thêm vào giỏ!', 'Thành công', 'success');
            } catch (error) { this.showToast(error.message || 'Lỗi thêm vào giỏ.', 'Lỗi', 'danger');}
            finally { this.isLoading.cartAction = null; }
        },
        async updateCartItemQuantity(cartItemId, newQuantity) {
            newQuantity = parseInt(newQuantity);
            if (isNaN(newQuantity) || newQuantity < 0) { this.showToast("Số lượng không hợp lệ.", "Lỗi", "warning"); this.loadUserCart(); return; }
            if (newQuantity === 0) { this.removeCartItem(cartItemId); return; }
            const itemInCart = this.cart.items.find(item => item.id === cartItemId);
            if (itemInCart && newQuantity > itemInCart.phone.stock_quantity) {
                this.showToast(`Tồn kho '${itemInCart.phone.model_name}' không đủ (còn ${itemInCart.phone.stock_quantity}).`, 'Lỗi', 'warning');
                this.loadUserCart(); return;
            }
            this.isLoading.cartAction = cartItemId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, { method: 'PUT', body: JSON.stringify({ quantity: newQuantity }) });
                this.cart = result.cart; this.apiResponse = result;
            } catch (error) { this.showToast(error.message || 'Lỗi cập nhật số lượng.', 'Lỗi', 'danger'); this.loadUserCart(); }
            finally { this.isLoading.cartAction = null; }
        },
        async removeCartItem(cartItemId) {
            this.isLoading.cartAction = cartItemId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/cart/items/${cartItemId}`, { method: 'DELETE' });
                this.cart = result.cart; this.apiResponse = result; this.showToast(result.message || 'Đã xóa khỏi giỏ.', 'Thông báo', 'info');
            } catch (error) { this.showToast(error.message || 'Lỗi xóa khỏi giỏ.', 'Lỗi', 'danger'); this.loadUserCart();}
            finally { this.isLoading.cartAction = null; }
        },
        async clearUserCart() {
            if(!confirm("Xóa toàn bộ giỏ hàng?")) return;
            this.isLoading.cartAction = 'clear_cart'; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/cart/`, { method: 'DELETE' });
                this.cart = result.cart; this.apiResponse = result; this.showToast(result.message || 'Đã dọn sạch giỏ hàng.', 'Thông báo', 'info');
            } catch (error) { this.showToast(error.message || 'Lỗi dọn giỏ hàng.', 'Lỗi', 'danger'); this.loadUserCart();}
            finally { this.isLoading.cartAction = null; }
        },

        // --- Order Methods ---
        async handlePlaceOrder() {
            if (!this.shippingAddress.trim() || this.shippingAddress.trim().length < 5) { this.showToast("Địa chỉ giao hàng (ít nhất 5 ký tự).", 'Lỗi', 'warning'); return; }
            for (const item of this.cart.items) { if (item.quantity > item.phone.stock_quantity) { this.showToast(`'${item.phone.model_name}' không đủ tồn kho.`, 'Lỗi', 'warning'); this.setView('cart'); return; } }
            this.isLoading.orderAction = 'place_order'; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/orders/`, { method: 'POST', body: JSON.stringify({ shipping_address: this.shippingAddress }) });
                this.showToast(`Đặt hàng thành công! ĐH #${result.id}`, 'Thành công', 'success'); this.apiResponse = result;
                this.shippingAddress = ''; this.getModal('checkoutModal').hide();
                await this.loadUserCart(); await this.loadProductsPublic(); this.setView('orders');
            } catch (error) { this.showToast(error.message || 'Lỗi đặt hàng.', 'Lỗi', 'danger'); }
            finally { this.isLoading.orderAction = null; }
        },
        async loadUserOrders(page = this.paginationOrders.page) {
            if (!this.isLoggedIn) return;
            this.isLoading.orders = true; this.apiResponse = null;
            this.paginationOrders.page = Number(page);
            let queryParams = `page=${this.paginationOrders.page}&per_page=${this.paginationOrders.per_page}`;
            queryParams += `&sort_by=${this.orderSort.sortBy}&order=${this.orderSort.order}`;
            if (this.orderFilters.status) queryParams += `&status=${encodeURIComponent(this.orderFilters.status)}`;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/orders/?${queryParams}`);
                this.orders = result.data.map(o => ({ ...o, new_status_to_update: o.status }));
                this.paginationOrders = { ...this.paginationOrders, ...result.meta }; this.apiResponse = result;
            } catch (error) { this.showToast(error.message || 'Lỗi tải đơn hàng.', 'Lỗi', 'danger'); this.orders = [];}
            finally { this.isLoading.orders = false; }
        },
        applyOrderFiltersAndSort() { this.loadUserOrders(1); },
        changeOrderPage(newPage) {
            if (newPage >= 1 && newPage <= this.paginationOrders.total_pages && newPage !== this.paginationOrders.page) {
                this.loadUserOrders(newPage);
            }
        },
        async viewOrderDetail(orderId) {
            this.isLoading.orderDetail = true;
            this.currentOrderDetail = null; // Reset trước
            this.apiResponse = null;
            console.log(`Workspaceing details for orderId: ${orderId}`); // DEBUG
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/orders/${orderId}`);
                console.log("API result for order detail:", result); // DEBUG
                if (result && typeof result === 'object' && result.id) { // Kiểm tra có 'id'
                    this.currentOrderDetail = { ...result, new_status_to_update: result.status };
                    this.apiResponse = result;
                    this.setView('orderDetail');
                } else {
                    console.error("Order data not found or invalid:", result);
                    this.showToast('Không tìm thấy thông tin đơn hàng từ API.', 'Lỗi dữ liệu', 'warning');
                    this.currentOrderDetail = null;
                }
            } catch (error) {
                console.error("Error fetching order detail:", error, error.response); // DEBUG
                this.showToast(error.message || 'Lỗi tải chi tiết đơn hàng.', 'Lỗi', 'danger');
                this.currentOrderDetail = null;
            } finally {
                this.isLoading.orderDetail = false;
            }
        },
        async cancelUserOrder(orderId) {
            const orderToCancel = this.orders.find(o => o.id === orderId) || this.currentOrderDetail;
            if (this.isBuyer && orderToCancel && !['pending', 'processing'].includes(orderToCancel.status) ) {
                 this.showToast('Chỉ hủy được đơn hàng đang chờ/đang xử lý.', 'Không thể hủy', 'warning'); return;
            }
            if (!confirm(`Hủy đơn hàng #${orderId}?`)) return;
            this.isLoading.orderAction = orderId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/cancel`, { method: 'POST' });
                this.showToast(result.message || 'Đã hủy đơn hàng.', 'Thành công', 'success'); this.apiResponse = result;
                this.loadUserOrders(this.paginationOrders.page);
                if (this.currentView === 'orderDetail' && this.currentOrderDetail?.id === orderId) this.loadOrderDetail(orderId);
                this.loadProductsPublic();
            } catch (error) { this.showToast(error.message || 'Lỗi hủy đơn hàng.', 'Lỗi', 'danger');}
            finally { this.isLoading.orderAction = null; }
        },
        async updateOrderStatus(orderId, newStatus) {
            const order = this.orders.find(o => o.id === orderId) || this.currentOrderDetail;
            if (!order || newStatus === order.status) return;
            this.isLoading.orderAction = orderId; this.apiResponse = null;
            try {
                const result = await fetchWithAuth(`${API_BASE_URL}/orders/${orderId}/status`, { method: 'PUT', body: JSON.stringify({ status: newStatus }) });
                this.showToast(result.message || 'Cập nhật TT thành công!', 'Thành công', 'success'); this.apiResponse = result;
                this.loadUserOrders(this.paginationOrders.page);
                if(this.currentView === 'orderDetail' && this.currentOrderDetail?.id === orderId) this.loadOrderDetail(orderId);
                if (newStatus === 'cancelled') this.loadProductsPublic();
            } catch (error) {
                this.showToast(error.message || 'Lỗi cập nhật TT.', 'Lỗi', 'danger');
                if(order) order.new_status_to_update = order.status;
            } finally { this.isLoading.orderAction = null; }
        },
        allowedOrderStatusesForUpdate(currentStatus) {
            if (this.isAdmin) return ALLOWED_ORDER_STATUSES_GLOBAL.filter(s => s !== currentStatus && s !== 'failed');
            if (this.isSeller) {
                 if (currentStatus === 'pending') return ['processing', 'shipped', 'cancelled'].filter(s => s !== currentStatus);
                 if (currentStatus === 'processing') return ['shipped', 'cancelled'].filter(s => s !== currentStatus);
            }
            return [];
        },
    },
    mounted() {
        this.checkLoginState();
        if (!this.isLoggedIn) { 
            this.loadProductsPublic();
        }

        const modalIds = ['loginModal', 'registerModal', 'productFormModal', 'checkoutModal'];
        modalIds.forEach(id => {
            const el = document.getElementById(id);
            if (el) this.bootstrapModals[id] = new bootstrap.Modal(el);
        });
    },
    watch: {
        isLoggedIn(newVal, oldVal) {
            if (newVal === true && oldVal === false) { 
                this.loadDataForLoggedInUser();
            } else if (newVal === false && oldVal === true) { 
                if(this.currentView !== 'productsPublic') this.setView('productsPublic'); 
                else if (this.productsPublic.length === 0) this.loadProductsPublic(); 
            }
        }
    }
});

app.mount('#app');