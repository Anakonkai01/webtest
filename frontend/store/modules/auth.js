// frontend/store/modules/auth.js
import { fetchWithAuth } from '../../services/api';

const state = {
    isLoggedIn: false,
    username: '',
    userId: null,
    userRole: '',
    loginForm: { username: '', password: '' },
    registerForm: { username: '', password: '', role: 'buyer' },
};

const mutations = {
    SET_LOGIN_STATE(state, isLoggedIn) {
        state.isLoggedIn = isLoggedIn;
    },
    SET_USER_DETAILS(state, { userId, username, userRole }) {
        state.userId = userId;
        state.username = username;
        state.userRole = userRole;
    },
    CLEAR_AUTH_STATE(state) {
        state.isLoggedIn = false;
        state.username = '';
        state.userId = null;
        state.userRole = '';
        state.loginForm = { username: '', password: '' };
        state.registerForm = { username: '', password: '', role: 'buyer' };
    },
    SET_LOGIN_FORM(state, form) {
        state.loginForm = { ...state.loginForm, ...form };
    },
    SET_REGISTER_FORM(state, form) {
        state.registerForm = { ...state.registerForm, ...form };
    },
    RESET_LOGIN_FORM(state) {
        state.loginForm = { username: '', password: '' };
    },
    RESET_REGISTER_FORM(state) {
        state.registerForm = { username: '', password: '', role: 'buyer' };
    },
};

const actions = {
    checkLoginState({ commit }) {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try {
                const tokenPayload = JSON.parse(atob(token.split('.')[1]));
                const now = Date.now() / 1000;
                if (tokenPayload.exp && tokenPayload.exp < now) {
                    localStorage.removeItem('accessToken');
                    localStorage.removeItem('userId');
                    localStorage.removeItem('username');
                    localStorage.removeItem('userRole');
                    commit('CLEAR_AUTH_STATE');
                    return;
                }
                const userId = localStorage.getItem('userId');
                const username = localStorage.getItem('username');
                const userRole = localStorage.getItem('userRole');
                commit('SET_LOGIN_STATE', true);
                commit('SET_USER_DETAILS', { userId, username, userRole });
            } catch (e) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('userId');
                localStorage.removeItem('username');
                localStorage.removeItem('userRole');
                commit('CLEAR_AUTH_STATE');
            }
        } else {
            commit('CLEAR_AUTH_STATE');
        }
    },
    async login({ commit, state, dispatch }, loginData) {
        try {
            const data = await fetchWithAuth(`${API_BASE_URL}/auth/login`, {
                method: 'POST',
                body: JSON.stringify(loginData || state.loginForm),
            }, 'auth');
            if (data.access_token) {
                localStorage.setItem('accessToken', data.access_token);
                const tokenPayload = JSON.parse(atob(data.access_token.split('.')[1]));
                localStorage.setItem('userId', tokenPayload.sub);
                localStorage.setItem('userRole', tokenPayload.role);
                localStorage.setItem('username', tokenPayload.username);
                commit('SET_LOGIN_STATE', true);
                commit('SET_USER_DETAILS', { userId: tokenPayload.sub, username: tokenPayload.username, userRole: tokenPayload.role });
                commit('RESET_LOGIN_FORM');
                // Optional: Dispatch action to load initial user data like cart
                // dispatch('cart/loadUserCart', null, { root: true });
                return true; // Indicate success
            }
        } catch (error) {
            console.error("Error during login:", error);
            // Re-throw error or handle specifically in component
            throw error;
        }
    },
    async register({ commit, state }, registerData) {
         if ((registerData || state.registerForm).password.length < 6) {
             throw new Error('Mật khẩu phải có ít nhất 6 ký tự.');
         }
        try {
            await fetchWithAuth(`${API_BASE_URL}/auth/register`, {
                method: 'POST',
                body: JSON.stringify(registerData || state.registerForm),
            }, 'auth');
            commit('RESET_REGISTER_FORM');
            return true; // Indicate success
        } catch (error) {
            console.error("Error during registration:", error);
             // Re-throw error or handle specifically in component
            throw error;
        }
    },
    logout({ commit }) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        localStorage.removeItem('userRole');
        commit('CLEAR_AUTH_STATE');
        // Optional: Dispatch actions to clear user-specific data like cart/orders
        // commit('cart/CLEAR_CART', null, { root: true });
        // commit('orders/CLEAR_ORDERS', null, { root: true });
    },
    updateLoginForm({ commit }, form) {
        commit('SET_LOGIN_FORM', form);
    },
    updateRegisterForm({ commit }, form) {
        commit('SET_REGISTER_FORM', form);
    }
};

const getters = {
    isLoggedIn: state => state.isLoggedIn,
    username: state => state.username,
    userId: state => state.userId,
    userRole: state => state.userRole,
    loginForm: state => state.loginForm,
    registerForm: state => state.registerForm,
};

export default {
    namespaced: true, // Add namespacing to the module
    state,
    mutations,
    actions,
    getters,
};