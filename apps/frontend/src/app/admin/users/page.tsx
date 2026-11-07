'use client';

import { useCallback, useEffect, useState } from 'react';
import { adminAPI, apiErrorMessage } from '@/lib/api';
import type { AdminUser, ApiEnvelope, UserStatusFilter } from '@/lib/types';

const FILTERS: Array<{ value: UserStatusFilter | ''; label: string }> = [
  { value: '', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'approved', label: 'Approved' },
  { value: 'blocked', label: 'Blocked' },
];

const fmt = (iso: string | null) => (iso ? new Date(iso).toLocaleDateString() : '—');

export default function AdminUsersPage() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState<UserStatusFilter | ''>('');
  const [error, setError] = useState('');

  const loadUsers = useCallback((q: string, s: UserStatusFilter | '') => {
    setLoading(true);
    setError('');
    adminAPI
      .getUsers({ ...(q ? { search: q } : {}), ...(s ? { status: s } : {}) })
      .then((res) => setUsers((res.data as ApiEnvelope<AdminUser[]>).data ?? []))
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load users')))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    loadUsers('', status);
    // search is applied on submit; status applies immediately
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status, loadUsers]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers(search.trim(), status);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Users</h1>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}

      <div className="flex flex-wrap gap-4 items-center justify-between">
        <div className="flex gap-2 flex-wrap">
          {FILTERS.map((f) => (
            <button
              key={f.label}
              onClick={() => setStatus(f.value)}
              className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
                status === f.value ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="search"
            className="input-field w-64"
            placeholder="Username, name, phone or email"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit" className="btn-primary">Search</button>
        </form>
      </div>

      <div className="card overflow-x-auto p-0">
        {loading ? (
          <p className="p-6 text-gray-500">Loading users...</p>
        ) : users.length === 0 ? (
          <p className="p-6 text-gray-500">No users found.</p>
        ) : (
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="text-left text-gray-500">
                <th className="px-4 py-3">User</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Plan</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Joined</th>
                <th className="px-4 py-3">Last login</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-t">
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{u.full_name || u.username}</p>
                    <p className="text-gray-500 text-xs">@{u.username}</p>
                  </td>
                  <td className="px-4 py-3">{u.phone}</td>
                  <td className="px-4 py-3">{u.email || '—'}</td>
                  <td className="px-4 py-3">{u.current_plan?.name ?? '—'}</td>
                  <td className="px-4 py-3">
                    {u.is_blocked ? (
                      <span className="px-2 py-0.5 rounded-full bg-red-100 text-red-700 text-xs font-medium">Blocked</span>
                    ) : u.is_approved ? (
                      <span className="px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-xs font-medium">Approved</span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 text-xs font-medium">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3">{fmt(u.created_at)}</td>
                  <td className="px-4 py-3">{fmt(u.last_login)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
