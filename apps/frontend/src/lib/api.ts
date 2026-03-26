import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });

          const access = response.data.data?.access || response.data.access;

          localStorage.setItem('accessToken', access);

          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data: { username: string; phone: string; password: string; full_name?: string }) =>
    api.post('/auth/register/', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login/', { identifier: data.email, password: data.password }),

  adminLogin: (data: { email: string; password: string }) =>
    api.post('/auth/admin/login/', { identifier: data.email, password: data.password }),

  logout: (refresh: string) =>
    api.post('/auth/logout/', { refresh }),

  refresh: (refresh: string) =>
    api.post('/auth/token/refresh/', { refresh }),
};

// User/Profile API
export const userAPI = {
  getProfile: () =>
    api.get('/auth/profile/'),

  updateProfile: (data: object) =>
    api.patch('/auth/profile/', data),

  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password/', data),
};

// Plans API
export const plansAPI = {
  getAll: () =>
    api.get('/plans/'),
};

// Templates API
export const templatesAPI = {
  getAll: () =>
    api.get('/plans/templates/all'),

  getByPlan: (planCode?: string) =>
    planCode
      ? api.get(`/plans/templates/by-plan/${planCode}/`)
      : api.get('/plans/templates/all'),
};

// Invitations (authenticated) API
export const eventsAPI = {
  // Create an order (first step before creating an invitation)
  createOrder: (data: { plan_code: string }) =>
    api.post('/invitations/orders/create/', data),

  // Create an invitation linked to an order
  create: (data: any) =>
    api.post('/invitations/create/', data),

  // Update an invitation
  update: (slug: string, data: any) =>
    api.patch(`/invitations/${slug}/update/`, data),

  // List all invitations for the authenticated user
  getAll: () =>
    api.get('/invitations/'),

  // Get a single invitation by slug
  getOne: (slug: string) =>
    api.get(`/invitations/${slug}/`),

  // Get stats (open count, device breakdown, etc.)
  getAnalytics: (slug: string) =>
    api.get(`/invitations/${slug}/stats/`),

  // List guests
  getGuests: (slug: string, page: number = 1) =>
    api.get(`/invitations/${slug}/guests/`, { params: { page } }),

  // Export guests as CSV
  exportGuestsCSV: (slug: string) =>
    api.get(`/invitations/${slug}/guests/export/`, { responseType: 'blob' }),

  // Create Razorpay payment order
  createRazorpayOrder: (orderId: string) =>
    api.post(`/invitations/orders/${orderId}/payment/razorpay/create/`),

  // Verify Razorpay payment
  verifyPayment: (data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => api.post('/invitations/payment/razorpay/verify/', data),
};

// Public invitation API (no auth)
export const invitationsAPI = {
  getMeta: (slug: string) =>
    api.get(`/invite/${slug}/`),

  checkFingerprint: (slug: string, data: { fingerprint: string }) =>
    api.post(`/invite/${slug}/check/`, data),

  registerGuest: (slug: string, data: { guest_name: string; is_test?: boolean; fingerprint?: string }) =>
    api.post(`/invite/${slug}/register/`, data),

  submitRSVP: (slug: string, data: { guest_id: string; status: string }) =>
    api.post(`/invite/${slug}/rsvp/`, data),
};

// Admin dashboard API
export const adminAPI = {
  getStats: () =>
    api.get('/admin-dashboard/stats/'),

  getUsers: (params?: object) =>
    api.get('/admin-dashboard/users/', { params }),

  getOrders: (params?: object) =>
    api.get('/admin-dashboard/orders/', { params }),

  approveOrder: (orderId: string) =>
    api.post(`/admin-dashboard/orders/${orderId}/approve/`),

  rejectOrder: (orderId: string, data?: { reason: string }) =>
    api.post(`/admin-dashboard/orders/${orderId}/reject/`, data),

  toggleUserBlock: (userId: string) =>
    api.post(`/admin-dashboard/users/${userId}/toggle-block/`),
};
