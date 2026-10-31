import { API_BASE } from './config.js';

export class ApiError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

async function request(method, path, body) {
    let response;
    try {
        response = await fetch(API_BASE + path, {
            method,
            headers: body === undefined ? {} : { 'Content-Type': 'application/json' },
            body: body === undefined ? undefined : JSON.stringify(body),
        });
    } catch {
        throw new ApiError(0, 'Cannot reach the server. Is it running?');
    }

    if (response.status === 204) {
        return null;
    }

    const isJson = (response.headers.get('Content-Type') || '').includes('json');
    const data = isJson ? await response.json() : null;
    if (response.status === 401 && !path.startsWith('/auth/')) {
        // The session ended (signed out elsewhere, password changed, account disabled): show the sign-in screen
        window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    if (!response.ok) {
        // Errors are RFC 9457 problem details: { title, status, detail }
        throw new ApiError(response.status, data?.detail || data?.title || `Request failed (${response.status})`);
    }
    return data;
}

function query(params) {
    const search = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null && value !== '') search.set(key, value);
    }
    const text = search.toString();
    return text ? `?${text}` : '';
}

export const api = {
    auth: {
        login: (username, password) => request('POST', '/auth/login', { username, password }),
        logout: () => request('POST', '/auth/logout'),
        me: () => request('GET', '/auth/me'),
        changePassword: (currentPassword, newPassword) =>
            request('PUT', '/auth/password', { current_password: currentPassword, new_password: newPassword }),
    },
    users: {
        list: () => request('GET', '/users'),
        create: (user) => request('POST', '/users', user),
        update: (id, user) => request('PUT', `/users/${id}`, user),
    },
    uoms: {
        list: () => request('GET', '/uoms'),
    },
    products: {
        list: () => request('GET', '/products'),
        create: (product) => request('POST', '/products', product),
        update: (id, product) => request('PUT', `/products/${id}`, product),
        remove: (id) => request('DELETE', `/products/${id}`),
    },
    orders: {
        list: ({ limit, offset, q } = {}) => request('GET', `/orders${query({ limit, offset, q })}`),
        get: (id) => request('GET', `/orders/${id}`),
        create: (order) => request('POST', '/orders', order),
    },
    stats: {
        summary: (days) => request('GET', `/stats/summary${query({ days })}`),
    },
};
