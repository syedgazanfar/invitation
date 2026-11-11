import type { Metadata } from 'next';
import localFont from 'next/font/local';
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

export const metadata: Metadata = {
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
    <html lang="en" className={`${sans.variable} ${serif.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}
