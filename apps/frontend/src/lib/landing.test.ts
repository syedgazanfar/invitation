import { describe, expect, it } from 'vitest';
import { BUSINESS_WHATSAPP, landingEnquiryPayload, landingEnquiryErrors, whatsappChatUrl } from './landing';

describe('whatsappChatUrl', () => {
  it('opens a chat with the business number in wa.me format (digits only, no +)', () => {
    expect(whatsappChatUrl()).toBe('https://wa.me/919923928181');
  });

  it('pre-fills the message, URL-encoded', () => {
    expect(whatsappChatUrl('Hi, I want a wedding invite & more')).toBe(
      'https://wa.me/919923928181?text=Hi%2C%20I%20want%20a%20wedding%20invite%20%26%20more',
    );
  });

  it('uses the configured business number', () => {
    expect(BUSINESS_WHATSAPP).toBe('+919923928181');
  });
});

describe('landingEnquiryPayload', () => {
  it('sends name, normalised WhatsApp number and event date to the enquiry API', () => {
    expect(landingEnquiryPayload({ name: '  Asha  ', phone: '+91 98765 43210', event_date: '2027-02-14', website: '' })).toEqual({
      name: 'Asha',
      phone: '+919876543210',
      event_date: '2027-02-14',
      website: '',
    });
  });

  it('sends a missing date as null (the field is optional on the backend)', () => {
    expect(landingEnquiryPayload({ name: 'Asha', phone: '9876543210', event_date: '', website: '' }).event_date).toBeNull();
  });
});

describe('landingEnquiryErrors', () => {
  it('requires a name and a 10+ digit WhatsApp number', () => {
    expect(landingEnquiryErrors({ name: ' ', phone: '123', event_date: '', website: '' })).toEqual({
      name: 'Please enter your name.',
      phone: 'Please enter a valid WhatsApp number.',
    });
  });

  it('accepts a valid form', () => {
    expect(landingEnquiryErrors({ name: 'Asha', phone: '+91 98765 43210', event_date: '', website: '' })).toEqual({});
  });
});
