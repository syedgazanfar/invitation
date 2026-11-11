'use client';

import { useState, useEffect } from 'react';
import { userAPI, apiErrorMessage } from '@/lib/api';
import { profileUpdatePayload } from '@/lib/forms';
import type { ApiEnvelope, Profile } from '@/lib/types';
import { useAuthStore } from '@/store/authStore';

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    username: user?.username || '',
  });

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await userAPI.getProfile();
      const profile = (response.data as ApiEnvelope<Profile>).data;
      setFormData({
        full_name: profile.full_name || '',
        email: profile.email || '',
        username: profile.username || '',
      });
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to load profile'));
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess(false);

    try {
      const response = await userAPI.updateProfile(profileUpdatePayload(formData));
      const saved = (response.data as ApiEnvelope<Profile>).data ?? (response.data as Profile);
      updateUser({ full_name: saved.full_name, email: saved.email });
      setSuccess(true);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to update profile'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading profile...</div>;

  return (
    <div className="max-w-lg">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Profile Settings</h1>

      <div className="card">
        <div className="mb-6 pb-6 border-b border-gray-200 space-y-2">
          <div>
            <p className="text-xs text-gray-500">Phone</p>
            <p className="font-medium text-gray-900">{user?.phone}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Username</p>
            <p className="font-medium text-gray-900">{formData.username}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Account status</p>
            <p className="font-medium text-gray-900">
              {user?.is_approved ? 'Approved' : 'Pending approval'}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
              Profile updated successfully.
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
            <input
              type="text"
              className="input-field"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email Address</label>
            <input
              type="email"
              className="input-field"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            />
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
