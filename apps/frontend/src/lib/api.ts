/**
 * Django REST API client: the frontend's single source of backend endpoints.
 * Every function here is pinned by src/lib/api.test.ts.
 *
 *  - `api`       → authenticated endpoints under /api/v1 (JWT, auto-refresh)
 *  - `publicApi` → guest invitation endpoints under /api/invite (no auth)
 */
import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  GuestRegisterInput,
  InvitationCreateInput,
  InvitationUpdateInput,
  RegisterInput,
  UserStatusFilter,
} from './types';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const PUBLIC_API_URL = API_URL.replace(/\/v1$/, '');

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------
export const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const publicApi = axios.create({
  baseURL: PUBLIC_API_URL,
  headers: { 'Content-Type': 'application/json' },
});

type RetriableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('accessToken');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refreshToken') : null;

    if (error.response?.status !== 401 || !original || original._retry || !refreshToken) {
      return Promise.reject(error);
    }
    original._retry = true;

    try {
      const res = await api.post('/auth/token/refresh/', { refresh: refreshToken }, { _retry: true } as object);
      const access: string | undefined = res.data?.data?.access || res.data?.access;
      if (!access) throw new Error('No access token in refresh response');
      localStorage.setItem('accessToken', access);
      original.headers.Authorization = `Bearer ${access}`;
      return api(original);
    } catch (refreshError) {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      if (typeof window !== 'undefined' && !process.env.VITEST) window.location.href = '/login';
      return Promise.reject(refreshError);
    }
  },
);

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------
/** Best human-readable message from a Django/DRF error response. */
export function apiErrorMessage(err: unknown, fallback: string): string {
  const data = (err as { response?: { data?: unknown } })?.response?.data;
  if (!data || typeof data !== 'object') return fallback;
  const body = data as Record<string, unknown>;

  if (typeof body.message === 'string' && body.message) return body.message;
  const fromFields = firstFieldError(body.errors) ?? firstFieldError(body);
  if (fromFields) return fromFields;
  if (typeof body.detail === 'string' && body.detail) return body.detail;
  return fallback;
}

function firstFieldError(value: unknown): string | undefined {
  if (!value || typeof value !== 'object') return undefined;
  for (const [key, v] of Object.entries(value as Record<string, unknown>)) {
    if (key === 'success' || key === 'code') continue;
    if (Array.isArray(v) && typeof v[0] === 'string') return v[0];
    if (typeof v === 'string' && key !== 'message' && key !== 'detail') return v;
  }
  return undefined;
}

// ---------------------------------------------------------------------------
// Endpoints
// ---------------------------------------------------------------------------
export const authAPI = {
  register: (data: RegisterInput) => api.post('/auth/register/', data),
  login: (data: { identifier: string; password: string }) => api.post('/auth/login/', data),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
};

export const userAPI = {
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data: { full_name?: string; email?: string }) => api.patch('/auth/profile/', data),
};

export const plansAPI = {
  getAll: () => api.get('/plans/'),
};

export const templatesAPI = {
  getByPlan: (planCode?: string) =>
    planCode ? api.get(`/plans/templates/by-plan/${planCode}/`) : api.get('/plans/templates/all'),
};

export const eventsAPI = {
  createOrder: (data: { plan_code: string; event_type?: string; event_type_name?: string }) =>
    api.post('/invitations/orders/create/', data),
  create: (data: InvitationCreateInput) => api.post('/invitations/create/', data),
  update: (slug: string, data: InvitationUpdateInput) => api.patch(`/invitations/${slug}/update/`, data),
  getAll: () => api.get('/invitations/'),
  getOne: (slug: string) => api.get(`/invitations/${slug}/`),
  getStats: (slug: string) => api.get(`/invitations/${slug}/stats/`),
  getGuests: (slug: string, page: number = 1) => api.get(`/invitations/${slug}/guests/`, { params: { page } }),
  exportGuestsCSV: (slug: string) => api.get(`/invitations/${slug}/guests/export/`, { responseType: 'blob' }),
  createRazorpayOrder: (orderId: string) => api.post(`/invitations/orders/${orderId}/payment/razorpay/create/`),
  verifyPayment: (data: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) =>
    api.post('/invitations/payment/razorpay/verify/', data),
};

export const invitationsAPI = {
  get: (slug: string) => publicApi.get(`/invite/${slug}/`),
  check: (slug: string, data: { fingerprint: string }) => publicApi.post(`/invite/${slug}/check/`, data),
  register: (slug: string, data: GuestRegisterInput) => publicApi.post(`/invite/${slug}/register/`, data),
  rsvp: (slug: string, data: { fingerprint: string; attending: boolean }) =>
    publicApi.post(`/invite/${slug}/rsvp/`, data),
};

export const adminAPI = {
  getStats: () => api.get('/admin-dashboard/dashboard/'),
  getUsers: (params?: { search?: string; status?: UserStatusFilter }) =>
    api.get('/admin-dashboard/users/', { params }),
  getPendingApprovals: () => api.get('/admin-dashboard/approvals/pending/'),
  approveUser: (userId: string, data?: { notes?: string }) =>
    api.post(`/admin-dashboard/users/${userId}/approve/`, data),
  rejectUser: (userId: string, data: { reason: string; block_user?: boolean }) =>
    api.post(`/admin-dashboard/users/${userId}/reject/`, data),
};
