export enum PlanCode {
  BASIC = 'BASIC',
  PREMIUM = 'PREMIUM',
  LUXURY = 'LUXURY',
}

export enum EventStatus {
  DRAFT = 'DRAFT',
  ACTIVE = 'ACTIVE',
  EXPIRED = 'EXPIRED',
}

export enum PaymentStatus {
  PENDING = 'PENDING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  REFUNDED = 'REFUNDED',
}

export interface Plan {
  code: PlanCode;
  name: string;
  basePriceUsd: number;
  maxRegularGuests: number;
  maxTestGuests: number;
  totalGuestLimit: number;
}

export interface PriceBreakdown {
  planCode: PlanCode;
  planName: string;
  countryCode: string;
  currency: string;
  basePriceUsd: number;
  basePriceLocal: number;
  adjustedPrice: number;
  tax: number;
  serviceFee: number;
  finalPrice: number;
}

export interface Template {
  id: string;
  planCode: PlanCode;
  name: string;
  previewUrl: string;
  description?: string;
}

export interface Event {
  id: string;
  userId: string;
  planCode: PlanCode;
  templateId: string;
  brideName: string;
  groomName: string;
  weddingDate: string;
  startTime: string;
  timezone: string;
  venueName: string;
  address: string;
  city: string;
  country: string;
  lat?: number;
  lng?: number;
  message?: string;
  status: EventStatus;
  slug?: string;
  activatedAt?: string;
  expiresAt?: string;
  createdAt: string;
  updatedAt: string;
  plan?: Plan;
  template?: Template;
  inviteUrl?: string;
  guestStats?: GuestStats;
}

export interface GuestStats {
  regularGuests: {
    current: number;
    max: number;
    remaining: number;
  };
  testGuests: {
    current: number;
    max: number;
    remaining: number;
  };
  total: {
    current: number;
    max: number;
    remaining: number;
  };
}

export interface Guest {
  id: string;
  eventId: string;
  guestName: string;
  isTest: boolean;
  userAgent?: string;
  ip?: string;
  createdAt: string;
}

export interface InvitationData {
  guest: {
    id: string;
    name: string;
  };
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
    lat?: number;
    lng?: number;
    message?: string;
  };
}
