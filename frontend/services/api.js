// frontend/services/api.js
const API_BASE_URL = 'http://127.0.0.1:5000';

const getToken = () => {
    return localStorage.getItem('accessToken');
};

const removeToken = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    localStorage.removeItem('userRole');
};

const fetchWithAuth = async (url, options = {}, actionKey = null, itemId = null) => {
    // Note: Loading state management related to actionKey and itemId will need to be handled
    // by the components or a central store (like Vuex) that calls this function.
    // This function is purely for handling the fetch logic with auth headers and basic errors.

    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) { headers['Authorization'] = `Bearer ${token}`; }

    console.log(`Requesting: ${options.method || 'GET'} ${url}`);
    if (options.body) console.log("Request body:", options.body);

    try {
        const response = await fetch(url, { ...options, headers });
        console.log(`Response status for ${url}: ${response.status}`);

        if (response.status === 204) {
            console.log("Response 204 No Content");
            return null;
        }

        const responseData = await response.json();
        console.log("Response data:", responseData);

        if (!response.ok) {
            const error = new Error(responseData.error?.message || responseData.msg || responseData.message || `HTTP Error ${response.status}`);
            error.response = responseData;
            error.status = response.status;
            throw error;
        }
        return responseData;
    } catch (error) {
        console.error(`API call to ${url} FAILED:`, error);
        // Note: Displaying toasts will need to be handled by the caller (component or store)
        // Based on the error thrown by this function.
        throw error;
    }
};

export { fetchWithAuth, getToken, removeToken, API_BASE_URL };