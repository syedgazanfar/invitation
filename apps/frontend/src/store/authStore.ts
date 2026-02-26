/**
 * Authentication Store with Zustand
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthState } from '../types';
import { authApi } from '../services/api';

interface AuthStore extends AuthState {
  // Actions
  login: (phone: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: User | null) => void;
  clearAuth: () => void;
  loadUser: () => Promise<void>;
}

interface RegisterData {
  phone: string;
  username: string;
  email?: string;
  full_name?: string;
  password: string;
  password_confirm: string;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
};

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      login: async (phone: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await authApi.login({ phone, password });
          const { access, refresh, user } = response.data!;
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true });
        try {
          const response = await authApi.register(data);
          const { access, refresh, user } = response.data!;
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        const { refreshToken } = get();
        if (refreshToken) {
          try {
            await authApi.logout({ refresh: refreshToken });
          } catch (error) {
            console.error('Logout error:', error);
          }
        }
        get().clearAuth();
      },

      setTokens: (access: string, refresh: string) => {
        set({
          accessToken: access,
          refreshToken: refresh,
          isAuthenticated: true,
        });
      },

      setAccessToken: (token: string) => {
        set({ accessToken: token });
      },

      setUser: (user: User | null) => {
        set({ user, isAuthenticated: !!user });
      },

      clearAuth: () => {
        set(initialState);
      },

      loadUser: async () => {
        try {
          const response = await authApi.getProfile();
          set({ user: response.data! });
        } catch (error) {
          get().clearAuth();
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    }
  )
);

// Invitation Store
interface InvitationStore {
  currentInvitation: any | null;
  invitations: any[];
  orders: any[];
  setCurrentInvitation: (invitation: any | null) => void;
  setInvitations: (invitations: any[]) => void;
  setOrders: (orders: any[]) => void;
  addInvitation: (invitation: any) => void;
  updateInvitation: (slug: string, data: any) => void;
  addOrder: (order: any) => void;
  updateOrder: (id: string, data: any) => void;
}

export const useInvitationStore = create<InvitationStore>()((set) => ({
  currentInvitation: null,
  invitations: [],
  orders: [],
  
  setCurrentInvitation: (invitation) => set({ currentInvitation: invitation }),
  setInvitations: (invitations) => set({ invitations }),
  setOrders: (orders) => set({ orders }),
  
  addInvitation: (invitation) => 
    set((state) => ({ invitations: [invitation, ...state.invitations] })),
  
  updateInvitation: (slug, data) =>
    set((state) => ({
      invitations: state.invitations.map((inv) =>
        inv.slug === slug ? { ...inv, ...data } : inv
      ),
      currentInvitation: state.currentInvitation?.slug === slug
        ? { ...state.currentInvitation, ...data }
        : state.currentInvitation,
    })),
  
  addOrder: (order) =>
    set((state) => ({ orders: [order, ...state.orders] })),
  
  updateOrder: (id, data) =>
    set((state) => ({
      orders: state.orders.map((o) =>
        o.id === id ? { ...o, ...data } : o
      ),
    })),
}));

// Admin Store
interface AdminStore {
  dashboardStats: any | null;
  orders: any[];
  users: any[];
  setDashboardStats: (stats: any) => void;
  setOrders: (orders: any[]) => void;
  setUsers: (users: any[]) => void;
  updateOrder: (id: string, data: any) => void;
  updateUser: (id: string, data: any) => void;
}

export const useAdminStore = create<AdminStore>()((set) => ({
  dashboardStats: null,
  orders: [],
  users: [],
  
  setDashboardStats: (stats) => set({ dashboardStats: stats }),
  setOrders: (orders) => set({ orders }),
  setUsers: (users) => set({ users }),
  
  updateOrder: (id, data) =>
    set((state) => ({
      orders: state.orders.map((o) =>
        o.id === id ? { ...o, ...data } : o
      ),
    })),
  
  updateUser: (id, data) =>
    set((state) => ({
      users: state.users.map((u) =>
        u.id === id ? { ...u, ...data } : u
      ),
    })),
}));
