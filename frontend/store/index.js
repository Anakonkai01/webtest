// frontend/store/index.js
import { createStore } from 'vuex';
import auth from './modules/auth';

const store = createStore({
    state() {
        return {
            // Add other state properties for products, cart, orders, etc. later
        };
    },
    mutations: {
        // Add other mutations for products, cart, orders, etc. later
    },
    getters: {
        // Add other getters for products, cart, orders, etc. later
    },
    modules: {
        auth,
    },
});

export default store;