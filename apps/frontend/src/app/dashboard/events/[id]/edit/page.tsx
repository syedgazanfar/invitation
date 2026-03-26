'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { eventsAPI } from '@/lib/api';
import { Event } from '@/types';

export default function EditEventPage() {
  const router = useRouter();
  const params = useParams();
  const eventId = params.id as string;

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [eventStatus, setEventStatus] = useState('');

  const [formData, setFormData] = useState({
    brideName: '',
    groomName: '',
    weddingDate: '',
    startTime: '',
    timezone: 'UTC',
    venueName: '',
    address: '',
    city: '',
    country: '',
    lat: '',
    lng: '',
    message: '',
  });

  useEffect(() => {
    loadEvent();
  }, [eventId]);

  const loadEvent = async () => {
    try {
      const response = await eventsAPI.getOne(eventId);
      const ev: Event = response.data;

      setEventStatus(ev.status);

      if (ev.status !== 'DRAFT') {
        setLoading(false);
        return;
      }

      setFormData({
        brideName: ev.brideName,
        groomName: ev.groomName,
        weddingDate: ev.weddingDate.split('T')[0],
        startTime: ev.startTime,
        timezone: ev.timezone,
        venueName: ev.venueName,
        address: ev.address,
        city: ev.city,
        country: ev.country,
        lat: ev.lat != null ? String(ev.lat) : '',
        lng: ev.lng != null ? String(ev.lng) : '',
        message: ev.message ?? '',
      });
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load event');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');

    try {
      await eventsAPI.update(eventId, {
        ...formData,
        lat: formData.lat !== '' ? parseFloat(formData.lat) : undefined,
        lng: formData.lng !== '' ? parseFloat(formData.lng) : undefined,
        message: formData.message || undefined,
      });
      router.push(`/dashboard/events/${eventId}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to update event');
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading event...</div>;

  if (eventStatus && eventStatus !== 'DRAFT') {
    return (
      <div className="card max-w-lg">
        <p className="text-red-600 mb-4">
          Only DRAFT events can be edited. This event is {eventStatus}.
        </p>
        <Link href={`/dashboard/events/${eventId}`} className="btn-secondary">
          Back to Event
        </Link>
      </div>
    );
  }

  if (error && !formData.brideName) {
    return (
      <div className="card max-w-lg">
        <p className="text-red-600 mb-4">{error}</p>
        <Link href={`/dashboard/events/${eventId}`} className="btn-secondary">Back to Event</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Edit Event</h1>
        <Link href={`/dashboard/events/${eventId}`} className="btn-secondary">Cancel</Link>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Bride Name *</label>
              <input type="text" required className="input-field" value={formData.brideName}
                onChange={(e) => setFormData({ ...formData, brideName: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Groom Name *</label>
              <input type="text" required className="input-field" value={formData.groomName}
                onChange={(e) => setFormData({ ...formData, groomName: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Wedding Date *</label>
              <input type="date" required className="input-field" value={formData.weddingDate}
                onChange={(e) => setFormData({ ...formData, weddingDate: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Start Time *</label>
              <input type="time" required className="input-field" value={formData.startTime}
                onChange={(e) => setFormData({ ...formData, startTime: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Venue Name *</label>
              <input type="text" required className="input-field" value={formData.venueName}
                onChange={(e) => setFormData({ ...formData, venueName: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Address *</label>
              <input type="text" required className="input-field" value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">City *</label>
              <input type="text" required className="input-field" value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Country *</label>
              <input type="text" required className="input-field" value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Latitude <span className="text-gray-400 font-normal">(optional, for map)</span>
              </label>
              <input type="number" step="any" min="-90" max="90" className="input-field"
                placeholder="e.g. 40.7128" value={formData.lat}
                onChange={(e) => setFormData({ ...formData, lat: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Longitude <span className="text-gray-400 font-normal">(optional, for map)</span>
              </label>
              <input type="number" step="any" min="-180" max="180" className="input-field"
                placeholder="e.g. -74.0060" value={formData.lng}
                onChange={(e) => setFormData({ ...formData, lng: e.target.value })} />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Message <span className="text-gray-400 font-normal">(optional)</span>
              </label>
              <textarea rows={4} className="input-field" value={formData.message}
                onChange={(e) => setFormData({ ...formData, message: e.target.value })} />
            </div>
          </div>

          <div className="flex justify-end gap-4 pt-2">
            <Link href={`/dashboard/events/${eventId}`} className="btn-secondary">Cancel</Link>
            <button type="submit" disabled={saving}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
