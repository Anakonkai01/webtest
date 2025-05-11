<template>
    <div class="modal fade" id="loginModalVue" tabindex="-1" aria-labelledby="loginModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="loginModalLabel">Đăng nhập</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="handleLogin">
                        <div class="mb-3">
                            <label for="login-username" class="form-label">Tên đăng nhập:</label>
                            <input type="text" class="form-control" id="login-username" :value="loginForm.username" @input="updateLoginForm({ field: 'username', value: $event.target.value })" required>
                        </div>
                        <div class="mb-3">
                            <label for="login-password" class="form-label">Mật khẩu:</label>
                            <input type="password" class="form-control" id="login-password" :value="loginForm.password" @input="updateLoginForm({ field: 'password', value: $event.target.value })" required>
                        </div>
                        <button type="submit" class="btn btn-primary">Đăng nhập</button>
                    </form>
                </div>
                <div class="modal-footer justify-content-center">
                    <p>Chưa có tài khoản? <a href="#" @click.prevent="$emit('switch-to-register')">Đăng ký ngay</a></p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
    name: 'LoginModal',
    computed: {
        ...mapState('auth', ['loginForm', 'isLoading']),
        isLoginLoading() {
            return this.isLoading.auth; // Assuming isLoading.auth handles login loading
        }
    },
    methods: {
        ...mapActions('auth', ['login', 'updateLoginForm']),
        async handleLogin() {
            await this.login(this.loginForm);
            // No need to manually hide modal here, it should be handled after successful login action if needed
        }
    }
};
</script>

<style scoped>
/* Add component-specific styles here if needed */
</style>