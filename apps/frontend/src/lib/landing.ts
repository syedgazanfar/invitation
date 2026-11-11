/** Logic for the single public landing page (src/app/page.tsx). */
import { normalizePhone } from './forms';

/** Business WhatsApp number shown on the site ("Chat on WhatsApp"). */
export const BUSINESS_WHATSAPP = '+919923928181';

/** Display form of BUSINESS_WHATSAPP. */
export const BUSINESS_WHATSAPP_DISPLAY = '+91 99239 28181';

/** wa.me deep link to chat with the business, optionally with a pre-filled message. */
export function whatsappChatUrl(message?: string): string {
  const base = `https://wa.me/${BUSINESS_WHATSAPP.replace(/\D/g, '')}`;
  return message ? `${base}?text=${encodeURIComponent(message)}` : base;
}

export interface LandingEnquiryForm {
  name: string;
  phone: string;
  event_date: string;
  website: string; // honeypot: must stay empty
}

export type LandingEnquiryErrors = Partial<Record<'name' | 'phone' | 'event_date', string>>;

export function landingEnquiryErrors(form: LandingEnquiryForm): LandingEnquiryErrors {
  const errors: LandingEnquiryErrors = {};
  if (form.name.trim().length < 2) errors.name = 'Please enter your name.';
  if (normalizePhone(form.phone).replace(/^\+/, '').length < 10) errors.phone = 'Please enter a valid WhatsApp number.';
  return errors;
}

/** Body for POST /api/v1/enquiries/ (event_type is left to the backend default). */
export function landingEnquiryPayload(form: LandingEnquiryForm) {
  return {
    name: form.name.trim(),
    phone: normalizePhone(form.phone),
    event_date: form.event_date || null,
    website: form.website,
  };
}
