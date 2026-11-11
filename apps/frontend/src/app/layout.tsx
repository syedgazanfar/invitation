import type { Metadata } from 'next';
import localFont from 'next/font/local';
import Script from 'next/script';
import { gtmInitScript, gtmNoscriptSrc, gtmScriptSrc } from '@/lib/analytics';
import './globals.css';

// Fonts are self-hosted (src/app/fonts, latin subset, OFL-licensed) so production
// builds never depend on reaching Google Fonts; next/font/google failed
// intermittently inside the Docker build.
const sans = localFont({
  src: [{ path: './fonts/inter-variable.woff2', weight: '100 900', style: 'normal' }],
  variable: '--font-sans',
  display: 'swap',
});

const serif = localFont({
  src: [
    { path: './fonts/cormorant-garamond-variable.woff2', weight: '300 700', style: 'normal' },
    { path: './fonts/cormorant-garamond-variable-italic.woff2', weight: '300 700', style: 'italic' },
  ],
  variable: '--font-serif',
  display: 'swap',
});

// Devanagari (Hindi / Marathi pages). unicode-range means browsers only download
// these when Devanagari text is on the page, so the English page stays light.
// (next/font requires literal values, so the range is repeated in both calls.)

const sansDeva = localFont({
  src: [{ path: './fonts/noto-sans-devanagari-variable.woff2', weight: '400 700', style: 'normal' }],
  variable: '--font-sans-deva',
  display: 'swap',
  declarations: [{ prop: 'unicode-range', value: 'U+0900-097F, U+1CD0-1CF9, U+200C-200D, U+20B9, U+25CC, U+A830-A839, U+A8E0-A8FF' }],
});

const serifDeva = localFont({
  src: [{ path: './fonts/noto-serif-devanagari-variable.woff2', weight: '400 700', style: 'normal' }],
  variable: '--font-serif-deva',
  display: 'swap',
  declarations: [{ prop: 'unicode-range', value: 'U+0900-097F, U+1CD0-1CF9, U+200C-200D, U+20B9, U+25CC, U+A830-A839, U+A8E0-A8FF' }],
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://app.invvite.heystartup.co.uk'),
  title: 'Invvite · Digital Invitations for Weddings, Birthdays & Festivals',
  description:
    'Elegant digital invitations for weddings, engagements, birthdays and festivals, designed for you and shared as one WhatsApp link. Enquire or chat with us on WhatsApp.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${sans.variable} ${serif.variable} ${sansDeva.variable} ${serifDeva.variable}`}>
      <body className="font-sans">
        {/* Google Tag Manager (noscript fallback) */}
        <noscript>
          <iframe src={gtmNoscriptSrc()} height="0" width="0" style={{ display: 'none', visibility: 'hidden' }} />
        </noscript>
        {children}
        {/* Google Tag Manager */}
        <Script id="gtm-init" strategy="afterInteractive">
          {gtmInitScript()}
        </Script>
        <Script id="gtm" src={gtmScriptSrc()} strategy="afterInteractive" />
      </body>
    </html>
  );
}
