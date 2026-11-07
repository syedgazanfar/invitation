// Types matching the Django REST API (apps/backend). Each type names the
// serializer or view it mirrors; keep them in sync when the backend changes.
// DRF serialises DecimalField as a string (e.g. price_inr: "999.00").

export type PlanCode = 'BASIC' | 'PREMIUM' | 'LUXURY';

// ---------------------------------------------------------------------------
// Envelopes
// ---------------------------------------------------------------------------
/** Custom Django views: { success, message?, data, errors? } */
export interface ApiEnvelope<T> {
  success: boolean;
  message?: string;
  data: T;
  errors?: Record<string, string[]>;
  count?: number;
}

/** Generic DRF list views (PageNumberPagination). */
export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ---------------------------------------------------------------------------
// Auth / accounts
// ---------------------------------------------------------------------------
/** authentication/services._build_user_payload (login, also stored in authStore) */
export interface User {
  id: string;
  username: string;
  phone: string;
  email: string;
  full_name: string;
  is_approved: boolean;
  is_phone_verified: boolean;
  is_staff?: boolean;
  is_superuser?: boolean;
  current_plan?: { code: PlanCode; name: string; price_inr: number } | null;
}

/** POST /auth/login/ and /auth/register/ → data */
export interface AuthPayload {
  access: string;
  refresh: string;
  user: User;
}

/** accounts.UserProfileSerializer */
export interface Profile {
  id: string;
  phone: string;
  username: string;
  email: string;
  full_name: string;
  is_phone_verified: boolean;
  created_at: string;
  updated_at: string;
  active_orders_count?: number;
  total_invitations?: number;
}

// ---------------------------------------------------------------------------
// Plans & templates
// ---------------------------------------------------------------------------
/** plans.PlanSerializer */
export interface Plan {
  id: string;
  code: PlanCode;
  name: string;
  description: string;
  regular_links: number;
  test_links: number;
  price_inr: string;
  display_price: string;
  features: string[];
  is_active: boolean;
  sort_order: number;
}

/** plans.TemplateListSerializer */
export interface Template {
  id: string;
  name: string;
  description: string;
  thumbnail: string | null;
  plan_code: PlanCode;
  category_name: string;
  animation_type: string;
  supports_gallery: boolean;
  supports_music: boolean;
  supports_video: boolean;
  is_premium: boolean;
  use_count: number;
}

// ---------------------------------------------------------------------------
// Orders
// ---------------------------------------------------------------------------
export type OrderStatus = 'PENDING_PAYMENT' | 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | 'EXPIRED';

/** invitations.OrderListSerializer (GET /invitations/orders/, paginated) */
export interface OrderSummary {
  id: string;
  order_number: string;
  plan_name: string;
  event_type: string;
  event_type_name: string;
  status: OrderStatus | string;
  payment_status: string;
  approved_at: string | null;
  created_at: string;
  has_invitation: boolean;
  invitation_slug: string | null;
  granted_regular_links: number;
  granted_test_links: number;
}

// ---------------------------------------------------------------------------
// Invitations (owner)
// ---------------------------------------------------------------------------
/** invitations.InvitationListSerializer */
export interface InvitationListItem {
  id: string;
  slug: string;
  event_title: string;
  event_date: string;
  template_name: string;
  template_thumbnail: string | null;
  order_status: string;
  is_active: boolean;
  is_expired: boolean;
  link_expires_at: string | null;
  total_views: number;
  unique_guests: number;
}

/** invitations.GuestSerializer */
export interface Guest {
  id: string;
  name: string;
  phone: string;
  message: string;
  attending: boolean | null;
  device_type: string;
  browser: string;
  os: string;
  viewed_at: string;
}

/** invitations.InvitationDetailSerializer */
export interface InvitationDetail {
  id: string;
  slug: string;
  template: Template;
  event_title: string;
  event_date: string;
  event_venue: string;
  event_address: string;
  event_map_link: string;
  host_name: string;
  host_phone: string;
  custom_message: string;
  banner_image: string | null;
  gallery_images: string[];
  background_music: string | null;
  is_active: boolean;
  is_expired: boolean;
  link_expires_at: string | null;
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

/** invitations.InvitationStatsSerializer (GET /invitations/<slug>/stats/ → data) */
export interface InvitationStats {
  total_views: number;
  unique_guests: number;
  regular_links_used: number;
  test_links_used: number;
  remaining_regular_links: number;
  remaining_test_links: number;
  is_link_valid: boolean;
  expires_in_days: number;
}

// ---------------------------------------------------------------------------
// Public invitation (guests)
// ---------------------------------------------------------------------------
/** invitations.PublicInvitationSerializer */
export interface PublicInvitation {
  event_title: string;
  event_date: string;
  event_venue: string;
  event_address: string;
  event_map_link: string;
  host_name: string;
  custom_message: string;
  banner_image: string | null;
  gallery_images: string[];
  background_music: string | null;
  template_animation: string;
  template_theme: Record<string, string> | null;
  template_config: Record<string, unknown> | null;
}

/** GET /api/invite/<slug>/ → data */
export interface PublicInviteResponse {
  invitation: PublicInvitation;
  can_register: boolean;
  remaining_links: number;
}

/** POST /api/invite/<slug>/check/ → data */
export type GuestCheckResult =
  | { already_registered: true; guest_name: string; viewed_at: string; message: string }
  | { already_registered: false; can_register: boolean; remaining_links: number };

/** POST /api/invite/<slug>/register/ → data */
export interface GuestRegisterResult {
  already_registered: boolean;
  guest_name: string;
  total_guests: number;
  remaining_links?: number;
}

// ---------------------------------------------------------------------------
// Admin dashboard
// ---------------------------------------------------------------------------
/** admin_dashboard.views.DashboardStatsView */
export interface AdminStats {
  users: { total: number; new_today: number; pending_approval: number };
  orders: { total: number; pending_payment: number; pending_approval: number; approved: number; rejected: number };
  invitations: { total: number; active: number; expired: number };
  links: { total_granted: number; total_used: number; total_remaining: number };
  notifications: { unread: number; total: number };
}

/** admin_dashboard.views.AllUsersListView.list */
export interface AdminUser {
  id: string;
  username: string;
  full_name: string;
  phone: string;
  email: string;
  is_approved: boolean;
  payment_verified: boolean;
  is_blocked: boolean;
  current_plan: { code: PlanCode; name: string } | null;
  created_at: string | null;
  approved_at: string | null;
  last_login: string | null;
  signup_ip: string | null;
  notes: string;
  latest_order: { id: string; status: string; amount: number } | null;
}

/** admin_dashboard.views.PendingApprovalsView.get */
export interface PendingApproval {
  id: string;
  username: string;
  full_name: string;
  phone: string;
  email: string;
  created_at: string | null;
  signup_ip: string | null;
  current_plan: {
    code: PlanCode;
    name: string;
    price_inr: number;
    regular_links: number;
    test_links: number;
  } | null;
  latest_order: {
    id: string;
    order_number: string;
    status: string;
    payment_amount: number;
    payment_method: string;
  } | null;
}

// ---------------------------------------------------------------------------
// Request inputs
// ---------------------------------------------------------------------------
/** accounts.UserRegistrationSerializer */
export interface RegisterInput {
  phone: string;
  username: string;
  password: string;
  password_confirm: string;
  email?: string;
  full_name?: string;
}

/** invitations.InvitationCreateSerializer (image/music uploads not supported from the UI yet) */
export interface InvitationCreateInput {
  order_id: string;
  template_id: string;
  event_title: string;
  event_date: string;
  event_venue: string;
  host_name: string;
  event_address?: string;
  event_map_link?: string;
  host_phone?: string;
  custom_message?: string;
}

/** invitations.InvitationUpdateSerializer */
export type InvitationUpdateInput = Partial<Omit<InvitationCreateInput, 'order_id' | 'template_id'>>;

/** invitations.GuestRegistrationSerializer */
export interface GuestRegisterInput {
  name: string;
  fingerprint: string;
  phone?: string;
  message?: string;
  attending?: boolean | null;
  is_test?: boolean;
  screen_resolution?: string;
  timezone_offset?: string;
  languages?: string;
  canvas_hash?: string;
  session_id?: string;
}

export type UserStatusFilter = 'pending' | 'approved' | 'blocked';
