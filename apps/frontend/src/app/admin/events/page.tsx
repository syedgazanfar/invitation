'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { adminAPI } from '@/lib/api';

interface AdminEvent {
  id: string;
  brideName: string;
  groomName: string;
  weddingDate: string;
  status: string;
  planName: string;
  slug: string | null;
  createdAt: string;
  expiresAt: string | null;
  user: { id: string; email: string };
  payment: { status: string; amount: number; currency: string } | null;
  guestCount: number;
}

interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

const STATUS_OPTIONS = ['', 'DRAFT', 'ACTIVE', 'EXPIRED'];

const statusStyle = (s: string) => ({
  DRAFT: 'bg-gray-100 text-gray-700',
  ACTIVE: 'bg-green-100 text-green-700',
  EXPIRED: 'bg-red-100 text-red-600',
}[s] || 'bg-gray-100 text-gray-700');

const paymentStyle = (s: string) => ({
  COMPLETED: 'bg-green-100 text-green-700',
  FAILED: 'bg-red-100 text-red-600',
  PENDING: 'bg-yellow-100 text-yellow-700',
}[s] || 'bg-gray-100 text-gray-600');

export default function AdminEventsPage() {
  const [events, setEvents] = useState<AdminEvent[]>([]);
  const [pagination, setPagination] = useState<Pagination>({ page: 1, limit: 20, total: 0, totalPages: 0 });
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEvents(1);
  }, [statusFilter]);

  const loadEvents = async (page: number) => {
    setLoading(true);
    try {
      const res = await adminAPI.getEvents(statusFilter || undefined, page);
      setEvents(res.data.data.events);
      setPagination(res.data.data.pagination);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">All Events</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>
      )}

      <div className="flex gap-2 flex-wrap">
        {STATUS_OPTIONS.map((s) => (
          <button
            key={s || 'all'}
            onClick={() => setStatusFilter(s)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              statusFilter === s
                ? 'bg-primary-600 text-white border-primary-600'
                : 'bg-white text-gray-600 border-gray-300 hover:border-primary-400'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
        <span className="ml-auto text-sm text-gray-500 self-center">
          {pagination.total} event{pagination.total !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {['Couple', 'Date', 'Status', 'Plan', 'Owner', 'Payment', 'Guests', 'Created', 'Link'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={9} className="text-center py-8 text-gray-500">Loading...</td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-8 text-gray-500">No events found</td></tr>
              ) : events.map((ev) => (
                <tr key={ev.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="text-sm font-medium text-gray-900">{ev.brideName} & {ev.groomName}</p>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 whitespace-nowrap">
                    {new Date(ev.weddingDate).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusStyle(ev.status)}`}>
                      {ev.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{ev.planName}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate" title={ev.user.email}>
                    {ev.user.email}
                  </td>
                  <td className="px-4 py-3">
                    {ev.payment ? (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${paymentStyle(ev.payment.status)}`}>
                        {ev.payment.currency} {Number(ev.payment.amount).toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-xs text-gray-400">None</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-700 text-center">{ev.guestCount}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                    {new Date(ev.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {ev.slug ? (
                      <Link href={`/invite/${ev.slug}`} target="_blank" className="text-xs text-primary-600 hover:underline">
                        View
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {pagination.totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">Page {pagination.page} of {pagination.totalPages}</p>
          <div className="flex gap-2">
            <button onClick={() => loadEvents(pagination.page - 1)} disabled={pagination.page === 1} className="btn-secondary text-sm disabled:opacity-40">Previous</button>
            <button onClick={() => loadEvents(pagination.page + 1)} disabled={pagination.page === pagination.totalPages} className="btn-secondary text-sm disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
