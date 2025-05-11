// frontend/services/api.js
const API_BASE_URL = 'http://127.0.0.1:5000'; // Đảm bảo đây là URL backend Flask của bạn

const getToken = () => {
    return localStorage.getItem('accessToken');
};

const removeToken = () => {
    localStorage.removeItem('accessToken');
    // Xóa các thông tin người dùng khác nếu bạn lưu chúng trong localStorage
    // localStorage.removeItem('username');
    // localStorage.removeItem('userRole');
    // localStorage.removeItem('userId');
};

const fetchWithAuth = async (url, options = {}) => {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers, // Cho phép ghi đè hoặc thêm header nếu cần
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // console.log(`Requesting: ${options.method || 'GET'} ${url}`);
    // if (options.body) console.log("Request body:", JSON.parse(options.body)); // Chỉ log nếu là JSON string

    try {
        const response = await fetch(url, { ...options, headers });
        // console.log(`Response status for ${url}: ${response.status}`);

        if (response.status === 204) { // No Content
            // console.log("Response 204 No Content");
            return { success: true, message: "Thao tác thành công (No Content)." }; // Trả về một object chuẩn
        }

        const responseData = await response.json();
        // console.log("Response data:", responseData);

        if (!response.ok) {
            const errorMessage = responseData.error?.message || responseData.msg || responseData.message || `Lỗi HTTP ${response.status}`;
            const error = new Error(errorMessage);
            error.response = responseData;
            error.status = response.status;
            console.error(`API call to ${url} FAILED with status ${response.status}:`, errorMessage, responseData);
            throw error;
        }
        return responseData;
    } catch (error) {
        // Nếu lỗi không phải từ response.json() (ví dụ: network error)
        if (!error.status) { // error.status sẽ có nếu lỗi từ throw new Error ở trên
            console.error(`API call to ${url} FAILED (Network/Other Error):`, error.message);
        }
        throw error; // Re-throw lỗi để hàm gọi có thể bắt và xử lý UI
    }
};

export { fetchWithAuth, getToken, removeToken, API_BASE_URL };