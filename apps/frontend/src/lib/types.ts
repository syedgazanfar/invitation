// Types matching the NestJS backend responses

export type PlanCode = 'BASIC' | 'PREMIUM' | 'LUXURY';
export type EventStatus = 'DRAFT' | 'ACTIVE' | 'EXPIRED';

export interface Plan {
  id: string;
  code: PlanCode;
  name: string;
  description: string;
  basePriceUsd: number;
  maxRegularGuests: number;
  maxTestGuests: number;
  features: string[];
}

export interface Template {
  id: string;
  name: string;
  description: string;
  planCode: PlanCode;
  previewUrl: string;
  category: string;
}

export interface Payment {
  id: string;
  amount: number;
  currency: string;
  countryCode: string;
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  paymentMethod: string;
  transactionId: string;
  createdAt: string;
}

export interface GuestStats {
  regularGuests: { current: number; max: number; remaining: number };
  testGuests: { current: number; max: number; remaining: number };
  total: { current: number; max: number; remaining: number };
}

export interface Event {
  id: string;
  userId: string;
  planCode: PlanCode;
  templateId: string;
  status: EventStatus;
  slug: string | null;
  brideName: string;
  groomName: string;
  weddingDate: string;
  startTime: string;
  timezone: string;
  venueName: string;
  address: string;
  city: string;
  country: string;
  lat: number | null;
  lng: number | null;
  message: string | null;
  activatedAt: string | null;
  expiresAt: string | null;
  createdAt: string;
  updatedAt: string;
  plan: Plan;
  template: Template;
  payment: Payment | null;
  guestStats?: GuestStats;
  inviteUrl?: string | null;
}

export interface Guest {
  id: string;
  eventId: string;
  guestName: string;
  isTest: boolean;
  ip: string | null;
  userAgent: string | null;
  createdAt: string;
}

export interface GuestAnalytics {
  summary: {
    total: number;
    regularCount: number;
    testCount: number;
    uniqueIPs: number;
    firstRegistration: string | null;
    lastRegistration: string | null;
    avgPerDay: number;
    peakDay: { date: string; count: number } | null;
    peakHour: number | null;
  };
  timeline: Array<{ date: string; regular: number; test: number }>;
  hourlyDistribution: Array<{ hour: number; count: number }>;
  devices: Array<{ name: string; count: number; pct: number }>;
  browsers: Array<{ name: string; count: number; pct: number }>;
  os: Array<{ name: string; count: number; pct: number }>;
}

// Meta returned by GET /invite/:slug
export interface InvitationMeta {
  slug: string;
  status: EventStatus;
  expiresAt: string;
  templateName: string;
  templatePreviewUrl: string;
}

// Data returned by POST /invite/:slug/register-guest
export interface InvitationData {
  guest: { id: string; name: string };
  event: {
    brideName: string;
    groomName: string;
    weddingDate: string;
    startTime: string;
    timezone: string;
    venueName: string;
    address: string;
    city: string;
    country: string;
    lat: number | null;
    lng: number | null;
    message: string | null;
  };
}
