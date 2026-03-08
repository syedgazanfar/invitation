'use client';

import { useEffect, useState } from 'react';
import { adminAPI } from '@/lib/api';

interface Stats {
  users: { total: number; newToday: number; newThisMonth: number };
  events: { total: number; draft: number; active: number; expired: number };
  guests: { total: number; today: number };
  revenue: { totalCompleted: number; totalAmount: number; totalPayments: number };
}

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color: string }) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    adminAPI.getStats()
      .then((res) => setStats(res.data.data))
      .catch((err) => setError(err.response?.data?.message || 'Failed to load stats'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-16 text-gray-500">Loading dashboard...</div>;

  if (error) return (
    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
      {error} — Make sure you are logged in as an admin.
    </div>
  );

  if (!stats) return null;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>

      {/* Users */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Users</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard label="Total Users" value={stats.users.total} color="text-blue-600" />
          <StatCard label="New Today" value={stats.users.newToday} color="text-green-600" />
          <StatCard label="New This Month" value={stats.users.newThisMonth} color="text-indigo-600" />
        </div>
      </section>

      {/* Events */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Events</h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard label="Total" value={stats.events.total} color="text-gray-800" />
          <StatCard label="Draft" value={stats.events.draft} color="text-yellow-600" />
          <StatCard label="Active" value={stats.events.active} color="text-green-600" />
          <StatCard label="Expired" value={stats.events.expired} color="text-red-500" />
        </div>
      </section>

      {/* Guests */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Guests</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <StatCard label="Total Guests" value={stats.guests.total} color="text-purple-600" />
          <StatCard label="Guests Today" value={stats.guests.today} color="text-pink-600" />
        </div>
      </section>

      {/* Revenue */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-widest mb-3">Revenue</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatCard
            label="Total Revenue"
            value={`$${stats.revenue.totalAmount.toFixed(2)}`}
            color="text-green-700"
            sub={`${stats.revenue.totalCompleted} completed payments`}
          />
          <StatCard label="Total Payments" value={stats.revenue.totalPayments} color="text-gray-700" />
          <StatCard
            label="Failed / Pending"
            value={stats.revenue.totalPayments - stats.revenue.totalCompleted}
            color="text-orange-500"
          />
        </div>
      </section>

      {/* Quick links */}
      <section className="card">
        <h2 className="text-lg font-semibold mb-4">Quick Actions</h2>
        <div className="flex gap-3 flex-wrap">
          <a href="/admin/users" className="btn-primary text-sm">Manage Users</a>
          <a href="/admin/events" className="btn-secondary text-sm">View All Events</a>
          <a href="/dashboard" className="btn-secondary text-sm">Organizer Dashboard</a>
        </div>
      </section>
    </div>
  );
}
