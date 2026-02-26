import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9301/api';

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
          const response = await axios.post(`${API_URL}/auth/refresh`, {
            refreshToken,
          });

          const { accessToken, refreshToken: newRefreshToken } = response.data.data;

          localStorage.setItem('accessToken', accessToken);
          localStorage.setItem('refreshToken', newRefreshToken);

          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
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
  signup: (data: { email: string; password: string; preferredCountry?: string }) =>
    api.post('/auth/signup', data),

  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),

  logout: () =>
    api.post('/auth/logout'),

  refresh: (refreshToken: string) =>
    api.post('/auth/refresh', { refreshToken }),
};

// User API
export const userAPI = {
  getProfile: () =>
    api.get('/users/profile'),

  updateProfile: (data: { preferredCountry?: string; preferredCurrency?: string }) =>
    api.put('/users/profile', data),
};

// Plans API
export const plansAPI = {
  getAll: () =>
    api.get('/plans'),

  getPricing: (countryCode: string = 'US') =>
    api.get(`/plans/pricing?country=${countryCode}`),

  getCountries: () =>
    api.get('/plans/countries'),
};

// Templates API
export const templatesAPI = {
  getByPlan: (planCode?: string) =>
    api.get(`/templates${planCode ? `?plan=${planCode}` : ''}`),
};

// Events API
export const eventsAPI = {
  create: (data: any) =>
    api.post('/events', data),

  update: (id: string, data: any) =>
    api.put(`/events/${id}`, data),

  processPayment: (id: string, data: { countryCode: string; simulateFailure?: boolean }) =>
    api.post(`/events/${id}/payment`, data),

  activate: (id: string) =>
    api.post(`/events/${id}/activate`),

  getAll: () =>
    api.get('/events'),

  getOne: (id: string) =>
    api.get(`/events/${id}`),

  getGuests: (id: string, page: number = 1, limit: number = 50) =>
    api.get(`/events/${id}/guests?page=${page}&limit=${limit}`),

  getGuestStats: (id: string) =>
    api.get(`/events/${id}/guests/stats`),

  exportGuestsCSV: (id: string) =>
    api.get(`/events/${id}/guests/export`, {
      responseType: 'blob',
    }),
};

// Invitations API (public)
export const invitationsAPI = {
  getMeta: (slug: string) =>
    api.get(`/invite/${slug}`),

  registerGuest: (slug: string, data: { guestName: string; isTest?: boolean }) =>
    api.post(`/invite/${slug}/register-guest`, data),

  getSlots: (slug: string) =>
    api.get(`/invite/${slug}/slots`),
};
