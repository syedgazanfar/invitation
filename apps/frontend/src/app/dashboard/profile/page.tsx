'use client';

import { useState, useEffect } from 'react';
import { userAPI, plansAPI } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';

export default function ProfilePage() {
  const { user, updateUser } = useAuthStore();

  const [countries, setCountries] = useState<{ countryCode: string; countryName: string; currency: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    preferredCountry: user?.preferredCountry || 'US',
    preferredCurrency: user?.preferredCurrency || 'USD',
  });

  useEffect(() => {
    Promise.all([loadProfile(), loadCountries()]).finally(() => setLoading(false));
  }, []);

  const loadProfile = async () => {
    try {
      const response = await userAPI.getProfile();
      const profile = response.data.data;
      setFormData({
        preferredCountry: profile.preferredCountry,
        preferredCurrency: profile.preferredCurrency,
      });
    } catch (err) {
      console.error('Failed to load profile:', err);
    }
  };

  const loadCountries = async () => {
    try {
      const response = await plansAPI.getCountries();
      setCountries(response.data.data);
    } catch (err) {
      console.error('Failed to load countries:', err);
    }
  };

  const handleCountryChange = (countryCode: string) => {
    const country = countries.find((c) => c.countryCode === countryCode);
    setFormData({
      preferredCountry: countryCode,
      preferredCurrency: country?.currency || formData.preferredCurrency,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    setSuccess(false);

    try {
      const response = await userAPI.updateProfile(formData);
      updateUser({ ...user!, ...response.data.data });
      setSuccess(true);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading profile...</div>;

  return (
    <div className="max-w-lg">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Profile Settings</h1>

      <div className="card">
        <div className="mb-6 pb-6 border-b border-gray-200">
          <p className="text-sm text-gray-600 mb-1">Email Address</p>
          <p className="font-medium text-gray-900">{user?.email}</p>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Country</label>
            <select
              className="input-field"
              value={formData.preferredCountry}
              onChange={(e) => handleCountryChange(e.target.value)}
            >
              {countries.map((country) => (
                <option key={country.countryCode} value={country.countryCode}>
                  {country.countryName} ({country.currency})
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Used for pricing calculations.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Currency</label>
            <input
              type="text"
              className="input-field"
              value={formData.preferredCurrency}
              onChange={(e) =>
                setFormData({ ...formData, preferredCurrency: e.target.value.toUpperCase().slice(0, 3) })
              }
              placeholder="USD"
              maxLength={3}
            />
            <p className="text-xs text-gray-500 mt-1">Auto-set when you change country.</p>
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
