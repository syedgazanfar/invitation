'use client';

import { useEffect, useState } from 'react';
import { adminAPI } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

interface AdminUser {
  id: string;
  email: string;
  preferredCountry: string;
  preferredCurrency: string;
  isAdmin: boolean;
  createdAt: string;
  eventCount: number;
}

export default function AdminUsersPage() {
  const { user: currentUser } = useAuthStore();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [toggling, setToggling] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async (q = '') => {
    setLoading(true);
    try {
      const res = await adminAPI.getUsers(q || undefined);
      setUsers(res.data.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadUsers(search);
  };

  const handleToggleAdmin = async (userId: string, email: string, current: boolean) => {
    const action = current ? 'remove admin from' : 'make admin';
    if (!confirm(`Are you sure you want to ${action} ${email}?`)) return;
    setToggling(userId);
    try {
      const res = await adminAPI.toggleAdmin(userId);
      if (res.data.success) {
        setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, isAdmin: !u.isAdmin } : u));
      }
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to update user');
    } finally {
      setToggling(null);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Users</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>
      )}

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3">
        <input
          type="text"
          className="input-field flex-1 max-w-sm"
          placeholder="Search by email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className="btn-primary">Search</button>
        {search && (
          <button type="button" className="btn-secondary" onClick={() => { setSearch(''); loadUsers(''); }}>
            Clear
          </button>
        )}
      </form>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {['Email', 'Country', 'Currency', 'Events', 'Role', 'Joined', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-500">Loading...</td></tr>
              ) : users.length === 0 ? (
                <tr><td colSpan={7} className="text-center py-8 text-gray-500">No users found</td></tr>
              ) : users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {u.email}
                    {u.id === currentUser?.id && (
                      <span className="ml-2 text-xs text-gray-400">(you)</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.preferredCountry}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.preferredCurrency}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{u.eventCount}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      u.isAdmin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-700'
                    }`}>
                      {u.isAdmin ? 'Admin' : 'User'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(u.createdAt).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    {u.id !== currentUser?.id && (
                      <button
                        onClick={() => handleToggleAdmin(u.id, u.email, u.isAdmin)}
                        disabled={toggling === u.id}
                        className={`text-xs px-3 py-1 rounded-lg font-medium disabled:opacity-50 transition-colors ${
                          u.isAdmin
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                        }`}
                      >
                        {toggling === u.id ? '...' : u.isAdmin ? 'Remove Admin' : 'Make Admin'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <p className="text-sm text-gray-500">{users.length} user{users.length !== 1 ? 's' : ''} shown</p>
    </div>
  );
}
