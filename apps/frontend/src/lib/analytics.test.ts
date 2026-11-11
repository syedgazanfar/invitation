import { afterEach, describe, expect, it } from 'vitest';
import { GTM_ID, gtmInitScript, gtmNoscriptSrc, gtmScriptSrc, trackEnquirySubmitted } from './analytics';

type W = Window & { dataLayer?: unknown[]; gtag?: (...args: unknown[]) => void };

afterEach(() => {
  delete (window as W).dataLayer;
  delete (window as W).gtag;
});

describe('Google Tag Manager', () => {
  it('uses the GTM-PK33GN4K container', () => {
    expect(GTM_ID).toBe('GTM-PK33GN4K');
    expect(gtmScriptSrc()).toBe('https://www.googletagmanager.com/gtm.js?id=GTM-PK33GN4K');
    expect(gtmNoscriptSrc()).toBe('https://www.googletagmanager.com/ns.html?id=GTM-PK33GN4K');
  });

  it('init script pushes the gtm.js start event (needed for the All Pages trigger) and defines gtag()', () => {
    // eslint-disable-next-line no-new-func
    new Function(gtmInitScript())();
    const w = window as W;
    expect(Array.isArray(w.dataLayer)).toBe(true);
    const start = w.dataLayer![0] as { event: string; 'gtm.start': number };
    expect(start.event).toBe('gtm.js');
    expect(typeof start['gtm.start']).toBe('number');
    expect(typeof w.gtag).toBe('function');
    w.gtag!('event', 'enquiry_submitted');
    expect(w.dataLayer).toHaveLength(3); // gtm.js start, gtag('js'), the event
  });

  it('keeps an existing dataLayer instead of replacing it', () => {
    (window as W).dataLayer = [{ event: 'earlier' }];
    // eslint-disable-next-line no-new-func
    new Function(gtmInitScript())();
    expect((window as W).dataLayer![0]).toEqual({ event: 'earlier' });
  });
});

describe('trackEnquirySubmitted', () => {
  it('pushes an enquiry_submitted event to the dataLayer', () => {
    trackEnquirySubmitted({ hasEventDate: true });
    expect((window as W).dataLayer).toEqual([{ event: 'enquiry_submitted', enquiry_has_event_date: true }]);
  });

  it('never sends the visitor name or phone number to Google', () => {
    trackEnquirySubmitted({ hasEventDate: false });
    const pushed = JSON.stringify((window as W).dataLayer);
    expect(pushed).not.toMatch(/name|phone|\+91/i);
  });

  it('works before GTM has loaded (creates the dataLayer)', () => {
    expect((window as W).dataLayer).toBeUndefined();
    trackEnquirySubmitted({ hasEventDate: false });
    expect((window as W).dataLayer).toHaveLength(1);
  });
});
