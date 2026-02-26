/**
 * API Service with Axios
 * 
 * This module provides HTTP client functionality for the application,
 * including authentication, request/response interceptors, and API methods.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { useAuthStore } from '../store/authStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && originalRequest) {
      const refreshToken = useAuthStore.getState().refreshToken;
      
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          useAuthStore.getState().setAccessToken(access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshError) {
          useAuthStore.getState().logout();
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Generic API methods
export const apiService = {
  get: <T>(url: string, params?: object) => 
    api.get<ApiResponse<T>>(url, { params }).then(res => res.data),
  
  post: <T>(url: string, data?: object) => 
    api.post<ApiResponse<T>>(url, data).then(res => res.data),
  
  put: <T>(url: string, data?: object) => 
    api.put<ApiResponse<T>>(url, data).then(res => res.data),
  
  patch: <T>(url: string, data?: object) => 
    api.patch<ApiResponse<T>>(url, data).then(res => res.data),
  
  delete: <T>(url: string) => 
    api.delete<ApiResponse<T>>(url).then(res => res.data),
};

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  errors?: Record<string, string[]>;
}

// Auth API
export const authApi = {
  register: (data: { phone: string; username: string; email?: string; full_name?: string; password: string; password_confirm: string }) =>
    apiService.post<{ access: string; refresh: string; user: any }>('/auth/register/', data),
  
  login: (data: { phone: string; password: string }) =>
    apiService.post<{ access: string; refresh: string; user: any }>('/auth/login/', data),
  
  logout: (data: { refresh: string }) =>
    apiService.post('/auth/logout/', data),
  
  refresh: (refresh: string) =>
    axios.post(`${API_BASE_URL}/auth/refresh/`, { refresh }),
  
  getProfile: () =>
    apiService.get<any>('/auth/profile/'),
  
  updateProfile: (data: Partial<any>) =>
    apiService.put<any>('/auth/profile/', data),
  
  changePassword: (data: { old_password: string; new_password: string; new_password_confirm: string }) =>
    apiService.post('/auth/change-password/', data),
  
  sendOTP: (phone: string) =>
    apiService.post('/auth/send-otp/', { phone }),
  
  verifyOTP: (data: { phone: string; otp: string }) =>
    apiService.post('/auth/verify-otp/', data),
};

// Plans API
export const plansApi = {
  getPlans: () =>
    apiService.get<any[]>('/plans/'),
  
  getPlan: (code: string) =>
    apiService.get<any>(`/plans/${code}/`),
  
  getCategories: () =>
    apiService.get<any[]>('/plans/categories/list'),
  
  getTemplates: (params?: { plan?: string; category?: string }) =>
    apiService.get<any[]>('/plans/templates/all', params),
  
  getTemplate: (id: string) =>
    apiService.get<any>(`/plans/templates/${id}/`),
  
  getFeaturedTemplates: () =>
    apiService.get<any[]>('/plans/templates/featured'),
  
  getTemplatesByPlan: (planCode: string, category?: string) =>
    apiService.get<{ plan: any; templates: any[] }>(`/plans/templates/by-plan/${planCode}/`, category ? { category } : undefined),
};

// Razorpay Types
declare global {
  interface Window {
    Razorpay: any;
  }
}

// Orders & Invitations API
export const invitationsApi = {
  getOrders: () =>
    apiService.get<any[]>('/invitations/orders/'),
  
  getOrder: (id: string) =>
    apiService.get<any>(`/invitations/orders/${id}/`),
  
  createOrder: (data: { plan_code: string; event_type: string; event_type_name: string }) =>
    apiService.post<any>('/invitations/orders/create/', data),
  
  getInvitations: () =>
    apiService.get<any[]>('/invitations/'),
  
  getInvitation: (slug: string) =>
    apiService.get<any>(`/invitations/${slug}/`),
  
  createInvitation: (data: any) =>
    apiService.post<any>('/invitations/create/', data),
  
  updateInvitation: (slug: string, data: any) =>
    apiService.put<any>(`/invitations/${slug}/update/`, data),
  
  getInvitationStats: (slug: string) =>
    apiService.get<any>(`/invitations/${slug}/stats/`),
  
  getGuests: (slug: string) =>
    apiService.get<any[]>(`/invitations/${slug}/guests/`),
  
  exportGuests: (slug: string) =>
    api.get(`/invitations/${slug}/guests/export/`, { responseType: 'blob' }),
  
  // Razorpay Payment
  createRazorpayOrder: (orderId: string) =>
    apiService.post<any>(`/invitations/orders/${orderId}/payment/razorpay/create/`),
  
  verifyRazorpayPayment: (data: {
    order_id: string;
    razorpay_payment_id: string;
    razorpay_order_id: string;
    razorpay_signature: string;
  }) => apiService.post('/invitations/payment/razorpay/verify/', data),
};

// Public Invitation API (no auth required)
export const publicApi = {
  getInvitation: (slug: string) =>
    axios.get<ApiResponse<any>>(`${API_BASE_URL.replace('/v1', '')}/invite/${slug}/`),
  
  checkGuest: (slug: string, fingerprint: string) =>
    axios.post<ApiResponse<any>>(`${API_BASE_URL.replace('/v1', '')}/invite/${slug}/check/`, { fingerprint }),
  
  registerGuest: (slug: string, data: any) =>
    axios.post<ApiResponse<any>>(`${API_BASE_URL.replace('/v1', '')}/invite/${slug}/register/`, data),
  
  updateRSVP: (slug: string, data: { fingerprint: string; attending: boolean }) =>
    axios.post<ApiResponse<any>>(`${API_BASE_URL.replace('/v1', '')}/invite/${slug}/rsvp/`, data),
};

// Admin API
export const adminApi = {
  // Dashboard Statistics
  getDashboardStats: () =>
    apiService.get<DashboardStats>('/admin-dashboard/dashboard/'),
  
  // Pending Approvals
  getPendingUsers: () =>
    apiService.get<any[]>('/admin-dashboard/approvals/pending/'),
  
  getRecentApprovals: () =>
    apiService.get<any[]>('/admin-dashboard/approvals/recent/'),
  
  // User Management
  getUsers: (params?: { status?: string; plan?: string; search?: string }) =>
    apiService.get<any[]>('/admin-dashboard/users/', params),
  
  getUserDetail: (id: string) =>
    apiService.get<any>(`/admin-dashboard/users/${id}/`),
  
  approveUser: (id: string, data: { notes?: string; payment_method?: string; payment_amount?: number }) =>
    apiService.post<any>(`/admin-dashboard/users/${id}/approve/`, data),
  
  rejectUser: (id: string, data: { reason: string; block_user?: boolean }) =>
    apiService.post<any>(`/admin-dashboard/users/${id}/reject/`, data),
  
  updateUserNotes: (id: string, notes: string) =>
    apiService.post(`/admin-dashboard/users/${id}/notes/`, { notes }),
  
  grantLinks: (id: string, data: { regular_links?: number; test_links?: number; reason?: string }) =>
    apiService.post<any>(`/admin-dashboard/users/${id}/grant-links/`, data),
  
  // Order Management (Legacy compatibility)
  getOrders: (params?: { status?: string; payment_status?: string; search?: string }) =>
    apiService.get<any[]>('/admin-dashboard/orders/', params),
  
  getOrder: (id: string) =>
    apiService.get<any>(`/admin-dashboard/orders/${id}/`),
  
  approveOrder: (id: string, notes?: string) =>
    apiService.post(`/admin-dashboard/orders/${id}/approve/`, { notes }),
  
  rejectOrder: (id: string, reason?: string) =>
    apiService.post(`/admin-dashboard/orders/${id}/reject/`, { reason }),
  
  updatePaymentStatus: (id: string, data: { payment_status?: string; payment_method?: string; notes?: string }) =>
    apiService.post(`/admin-dashboard/orders/${id}/payment/`, data),
  
  // Notifications
  getNotifications: (unreadOnly?: boolean) =>
    apiService.get<any[]>('/admin-dashboard/notifications/', unreadOnly ? { unread: 'true' } : undefined),
  
  markNotificationRead: (id: string) =>
    apiService.post(`/admin-dashboard/notifications/${id}/read/`, {}),
  
  // Statistics
  getStatistics: (days?: number) =>
    apiService.get<{ daily_stats: any[]; popular_templates: any[]; plan_distribution: any[] }>('/admin-dashboard/statistics/', { days }),
};

// Types
export interface DashboardStats {
  users: {
    total: number;
    new_today: number;
    pending_approval: number;
  };
  orders: {
    total: number;
    pending_payment: number;
    pending_approval: number;
    approved: number;
    rejected: number;
  };
  invitations: {
    total: number;
    active: number;
    expired: number;
  };
  links: {
    total_granted: number;
    total_used: number;
    total_remaining: number;
  };
  notifications: {
    unread: number;
    total: number;
  };
}

export default api;
