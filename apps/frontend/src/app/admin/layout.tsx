'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';
import { authAPI } from '@/lib/api';

const NAV_LINKS = [
  { href: '/admin/dashboard', label: 'Dashboard' },
  { href: '/admin/users', label: 'Users' },
  { href: '/admin/approvals', label: 'Approvals' },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, clearAuth, user, refreshToken } = useAuthStore();
  const isStaff = Boolean(user?.is_staff);

  useEffect(() => {
    if (!isAuthenticated) router.push('/login');
    else if (!isStaff) router.push('/dashboard');
  }, [isAuthenticated, isStaff, router]);

  const handleLogout = async () => {
    try {
      if (refreshToken) await authAPI.logout(refreshToken);
    } catch {
      // Token may already be expired/blacklisted; log out locally regardless.
    } finally {
      clearAuth();
      router.push('/');
    }
  };

  if (!isAuthenticated || !isStaff) return null;

  return (
    <div className="min-h-screen bg-gray-100 flex">
      <aside className="w-56 bg-gray-900 text-white flex flex-col fixed inset-y-0">
        <div className="px-6 py-5 border-b border-gray-700">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">Admin Panel</p>
          <p className="text-white font-bold text-sm truncate">{user?.full_name || user?.username}</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                pathname === link.href ? 'bg-primary-600 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="px-3 py-4 border-t border-gray-700 space-y-2">
          <Link
            href="/dashboard"
            className="block px-3 py-2 rounded-lg text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors"
          >
            Organizer Dashboard
          </Link>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-700 hover:text-white transition-colors"
          >
            Logout
          </button>
        </div>
      </aside>

      <main className="ml-56 flex-1 p-8">{children}</main>
    </div>
  );
}
