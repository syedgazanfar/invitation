/**
 * TypeScript Type Definitions
 */

// User Types
export interface User {
  id: string;
  phone: string;
  username: string;
  email?: string;
  full_name?: string;
  is_phone_verified: boolean;
  is_approved?: boolean;
  payment_verified?: boolean;
  is_blocked?: boolean;
  current_plan?: {
    code: string;
    name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Plan Types
export interface Plan {
  id: string;
  code: 'BASIC' | 'PREMIUM' | 'LUXURY';
  name: string;
  description: string;
  regular_links: number;
  test_links: number;
  price_inr: number;
  display_price: string;
  features: string[];
  is_active: boolean;
}

export interface InvitationCategory {
  id: string;
  code: string;
  name: string;
  description?: string;
  icon?: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnail: string;
  plan_code: string;
  category_name: string;
  animation_type: string;
  supports_gallery: boolean;
  supports_music: boolean;
  supports_video: boolean;
  is_premium: boolean;
  use_count: number;
  theme_colors?: Record<string, string>;
  animation_config?: Record<string, any>;
}

// Order Types
export type OrderStatus = 
  | 'DRAFT' 
  | 'PENDING_PAYMENT' 
  | 'PENDING_APPROVAL' 
  | 'APPROVED' 
  | 'REJECTED' 
  | 'EXPIRED' 
  | 'CANCELLED';

export interface Order {
  id: string;
  order_number: string;
  plan: Plan;
  plan_name?: string;
  event_type: string;
  event_type_name: string;
  status: OrderStatus;
  payment_amount: number;
  payment_method: string;
  payment_status: string;
  payment_notes?: string;
  approved_by?: string;
  approved_at?: string;
  admin_notes?: string;
  granted_regular_links: number;
  granted_test_links: number;
  has_invitation?: boolean;
  invitation_slug?: string;
  invitation_data?: InvitationSummary;
  created_at: string;
  updated_at: string;
}

// Invitation Types
export interface InvitationSummary {
  id: string;
  slug: string;
  event_title: string;
  is_active: boolean;
  is_expired: boolean;
  link_expires_at?: string;
  share_url: string;
  remaining_regular_links: number;
  remaining_test_links: number;
  regular_links_used: number;
  test_links_used: number;
  total_views: number;
  unique_guests: number;
}

export interface Invitation {
  id: string;
  slug: string;
  template: Template;
  event_title: string;
  event_date: string;
  event_venue: string;
  event_address?: string;
  event_map_link?: string;
  host_name: string;
  host_phone?: string;
  custom_message?: string;
  banner_image: string;
  gallery_images: string[];
  background_music?: string;
  is_active: boolean;
  is_expired: boolean;
  link_expires_at?: string;
  share_url: string;
  remaining_regular_links: number;
  remaining_test_links: number;
  regular_links_used: number;
  test_links_used: number;
  total_views: number;
  unique_guests: number;
  guests: Guest[];
  created_at: string;
  updated_at: string;
}

// Guest Types
export interface Guest {
  id: string;
  name: string;
  phone?: string;
  message?: string;
  attending?: boolean;
  device_type: string;
  browser: string;
  os: string;
  viewed_at: string;
}

export interface GuestRegistrationData {
  name: string;
  phone?: string;
  message?: string;
  attending?: boolean;
  fingerprint: string;
  screen_resolution?: string;
  timezone_offset?: string;
  languages?: string;
  canvas_hash?: string;
  session_id?: string;
  is_test?: boolean;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  errors?: Record<string, string[]>;
}

// Admin Types
export interface DashboardStats {
  users: {
    total: number;
    new_today: number;
    new_this_month: number;
    pending_approval: number;
  };
  orders: {
    total: number;
    pending_approval: number;
    pending_payment: number;
    approved: number;
    rejected: number;
  };
  revenue: {
    total: number;
    this_month: number;
  };
  invitations: {
    total: number;
    active: number;
    expired: number;
  };
  guests: {
    total: number;
    today: number;
  };
  links?: {
    total_granted: number;
    total_used: number;
    total_remaining: number;
  };
  notifications?: {
    unread: number;
    total: number;
  };
}

export interface DailyStat {
  date: string;
  users: number;
  orders: number;
  guests: number;
}

export interface PopularTemplate {
  id: string;
  name: string;
  use_count: number;
}

// Pending User Type (Admin)
export interface PendingUser {
  id: string;
  username: string;
  full_name?: string;
  phone: string;
  email?: string;
  created_at: string;
  signup_ip?: string;
  current_plan?: {
    code: string;
    name: string;
    price_inr: number;
    regular_links: number;
    test_links: number;
  };
  latest_order?: {
    id: string;
    order_number: string;
    status: string;
    payment_amount: number;
    payment_method: string;
  };
}

// Approval Log Type (Admin)
export interface ApprovalLog {
  id: string;
  action: 'APPROVED' | 'REJECTED';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone: string;
  };
  performed_by?: {
    id: string;
    username: string;
  };
  notes?: string;
  payment_amount?: number;
  payment_method?: string;
  created_at: string;
}

// Animation Types
export interface AnimationConfig {
  type: 'elegant' | 'fun' | 'traditional' | 'modern' | 'minimal' | 'bollywood' | 'floral' | 'royal';
  entrance: {
    hero: string;
    title: string;
    details: string;
  };
  effects: {
    particles?: boolean;
    confetti?: boolean;
    music?: boolean;
  };
  transitions: {
    betweenSections: string;
    galleryScroll: string;
  };
}

// WebSocket Types (Admin)
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface ApprovalUpdateMessage extends WebSocketMessage {
  type: 'approval_update';
  action: 'approved' | 'rejected';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone?: string;
    email?: string;
    is_approved: boolean;
    current_plan?: {
      code: string;
      name: string;
    };
  };
  performed_by?: {
    id: string;
    username: string;
  };
  timestamp: string;
  notes?: string;
}

export interface PendingCountMessage extends WebSocketMessage {
  type: 'pending_count_update';
  count: number;
  change: number;
}

export interface NewUserMessage extends WebSocketMessage {
  type: 'new_user';
  user: {
    id: string;
    username: string;
    full_name?: string;
    phone: string;
    email?: string;
    created_at: string;
  };
  timestamp: string;
}

export interface OrderUpdateMessage extends WebSocketMessage {
  type: 'order_update';
  order_id: string;
  status: string;
  previous_status?: string;
  timestamp: string;
}

export type WebSocketData = 
  | ApprovalUpdateMessage 
  | PendingCountMessage 
  | NewUserMessage 
  | OrderUpdateMessage
  | WebSocketMessage;
