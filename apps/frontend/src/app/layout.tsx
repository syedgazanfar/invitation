import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Invvite · Digital Invitations for Weddings, Birthdays & Festivals',
  description:
    'Beautiful animated digital invitations for weddings, engagements, birthdays and festivals, shared in one WhatsApp link. Enquire or chat with us on WhatsApp.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
