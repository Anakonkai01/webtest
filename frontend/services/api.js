// frontend/services/api.js
const API_BASE_URL = 'http://127.0.0.1:5000'; 

const getToken = () => {
    return localStorage.getItem('accessToken');
};

const removeToken = () => {
    localStorage.removeItem('accessToken');
};

const fetchWithAuth = async (url, options = {}) => {
    const token = getToken();
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers, 
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(url, { ...options, headers });

        if (response.status === 204) { 
            return { success: true, message: "Thao tác thành công (No Content)." }; // Trả về một object chuẩn
        }

        const responseData = await response.json();

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
        if (!error.status) { 
            console.error(`API call to ${url} FAILED (Network/Other Error):`, error.message);
        }
        throw error;
    }
};

export { fetchWithAuth, getToken, removeToken, API_BASE_URL };