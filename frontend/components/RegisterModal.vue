<template>
    <div class="modal fade" id="registerModalVue" tabindex="-1" aria-labelledby="registerModalLabel" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="registerModalLabel">Đăng ký</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <form @submit.prevent="handleRegister">
                        <div class="mb-3">
                            <label for="reg-username" class="form-label">Tên đăng nhập:</label>
                            <input type="text" class="form-control" id="reg-username" :value="registerForm.username" @input="updateRegisterForm({ field: 'username', value: $event.target.value })" required>
                        </div>
                        <div class="mb-3">
                            <label for="reg-password" class="form-label">Mật khẩu:</label>
                            <input type="password" class="form-control" id="reg-password" :value="registerForm.password" @input="updateRegisterForm({ field: 'password', value: $event.target.value })" required>
                        </div>
                         <div class="mb-3">
                            <label for="reg-role" class="form-label">Vai trò:</label>
                            <select class="form-select" id="reg-role" :value="registerForm.role" @change="updateRegisterForm({ field: 'role', value: $event.target.value })">
                                <option value="buyer">Người mua (Buyer)</option>
                                <option value="seller">Người bán (Seller)</option>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary">Đăng ký</button>
                    </form>
                    <!-- Consider adding a message display area here if needed -->
                </div>
                 <div class="modal-footer">
                    <p>Đã có tài khoản? <a href="#" @click.prevent="$emit('switch-to-login')">Đăng nhập</a></p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';

export default {
    name: 'RegisterModal',
    computed: {
        ...mapState('auth', ['registerForm'])
    },
    methods: {
        ...mapActions('auth', ['register', 'updateRegisterForm']),
        handleRegister() {
            // The action itself will handle the API call and state updates
            this.register();
        }
    }
};
</script>

<style scoped>
/* Add any specific styles for the modal here */
</style>