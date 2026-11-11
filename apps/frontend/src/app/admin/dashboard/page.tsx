'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { adminAPI, apiErrorMessage } from '@/lib/api';
import type { AdminStats, ApiEnvelope } from '@/lib/types';

function StatCard({ label, value, color, href }: { label: string; value: number; color: string; href?: string }) {
  const body = (
    <div className={`card ${href ? 'hover:shadow-lg transition-shadow' : ''}`}>
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  );
  return href ? <Link href={href}>{body}</Link> : body;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section>
      <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">{title}</h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-5 gap-4">{children}</div>
    </section>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    adminAPI
      .getStats()
      .then((res) => setStats((res.data as ApiEnvelope<AdminStats>).data))
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load stats')))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-16 text-gray-500">Loading dashboard...</div>;
  if (error || !stats) {
    return <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error || 'No data'}</div>;
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>

      <Section title="Users">
        <StatCard label="Total users" value={stats.users.total} color="text-blue-600" href="/admin/users" />
        <StatCard label="New today" value={stats.users.new_today} color="text-green-600" />
        <StatCard label="Pending approval" value={stats.users.pending_approval} color="text-yellow-600" href="/admin/approvals" />
      </Section>

      <Section title="Orders">
        <StatCard label="Total" value={stats.orders.total} color="text-gray-900" />
        <StatCard label="Pending payment" value={stats.orders.pending_payment} color="text-orange-600" />
        <StatCard label="Pending approval" value={stats.orders.pending_approval} color="text-yellow-600" href="/admin/approvals" />
        <StatCard label="Approved" value={stats.orders.approved} color="text-green-600" />
        <StatCard label="Rejected" value={stats.orders.rejected} color="text-red-600" />
      </Section>

      <Section title="Invitations">
        <StatCard label="Total" value={stats.invitations.total} color="text-gray-900" />
        <StatCard label="Active" value={stats.invitations.active} color="text-green-600" />
        <StatCard label="Expired" value={stats.invitations.expired} color="text-red-600" />
      </Section>

      <Section title="Links">
        <StatCard label="Granted" value={stats.links.total_granted} color="text-indigo-600" />
        <StatCard label="Used" value={stats.links.total_used} color="text-purple-600" />
        <StatCard label="Remaining" value={stats.links.total_remaining} color="text-blue-600" />
      </Section>
    </div>
  );
}
