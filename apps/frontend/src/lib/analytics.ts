/** Google Tag Manager setup (loaded on every page from src/app/layout.tsx). */

export const GTM_ID = 'GTM-PK33GN4K';

export const gtmScriptSrc = (id: string = GTM_ID) => `https://www.googletagmanager.com/gtm.js?id=${id}`;
export const gtmNoscriptSrc = (id: string = GTM_ID) => `https://www.googletagmanager.com/ns.html?id=${id}`;

/**
 * Inline bootstrap, run before gtm.js loads. The 'gtm.js' start event is what
 * GTM's built-in "All Pages" / page-view trigger listens for. gtag() is kept as
 * a convenience for pushing events (e.g. gtag('event', 'enquiry_submitted')).
 */
export function gtmInitScript(): string {
  return [
    'window.dataLayer = window.dataLayer || [];',
    "window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js' });",
    'window.gtag = window.gtag || function gtag(){ window.dataLayer.push(arguments); };',
    "window.gtag('js', new Date());",
  ].join('\n');
}
