'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { eventsAPI, apiErrorMessage } from '@/lib/api';
import type { InvitationDetail, InvitationUpdateInput } from '@/lib/types';

type FormState = Required<InvitationUpdateInput>;

const EMPTY: FormState = {
  event_title: '',
  event_date: '',
  event_venue: '',
  event_address: '',
  event_map_link: '',
  host_name: '',
  host_phone: '',
  custom_message: '',
};

/** ISO datetime → value for <input type="datetime-local"> in the browser's timezone. */
function toLocalInput(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
}

export default function EditInvitationPage() {
  const router = useRouter();
  const params = useParams();
  const slug = params.slug as string;

  const [formData, setFormData] = useState<FormState>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [expired, setExpired] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    eventsAPI
      .getOne(slug)
      .then((res) => {
        const inv = res.data as InvitationDetail;
        setExpired(inv.is_expired);
        setFormData({
          event_title: inv.event_title,
          event_date: toLocalInput(inv.event_date),
          event_venue: inv.event_venue,
          event_address: inv.event_address,
          event_map_link: inv.event_map_link,
          host_name: inv.host_name,
          host_phone: inv.host_phone,
          custom_message: inv.custom_message,
        });
      })
      .catch((err) => setLoadError(apiErrorMessage(err, 'Failed to load invitation')))
      .finally(() => setLoading(false));
  }, [slug]);

  const update = (name: keyof FormState) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setFormData((prev) => ({ ...prev, [name]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await eventsAPI.update(slug, {
        ...formData,
        event_date: new Date(formData.event_date).toISOString(),
      });
      router.push(`/dashboard/events/${slug}`);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to update invitation'));
      setSaving(false);
    }
  };

  if (loading) return <div className="text-center py-12">Loading invitation...</div>;

  if (loadError || expired) {
    return (
      <div className="card max-w-lg">
        <p className="text-red-600 mb-4">{loadError || 'Expired invitations can no longer be edited.'}</p>
        <Link href={`/dashboard/events/${slug}`} className="btn-secondary">Back to invitation</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Edit Invitation</h1>
        <Link href={`/dashboard/events/${slug}`} className="btn-secondary">Cancel</Link>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}

          <div className="grid md:grid-cols-2 gap-6">
            <Field label="Event title *" className="md:col-span-2">
              <input type="text" required maxLength={200} className="input-field" value={formData.event_title} onChange={update('event_title')} />
            </Field>
            <Field label="Date & time *">
              <input type="datetime-local" required className="input-field" value={formData.event_date} onChange={update('event_date')} />
            </Field>
            <Field label="Host name *">
              <input type="text" required maxLength={200} className="input-field" value={formData.host_name} onChange={update('host_name')} />
            </Field>
            <Field label="Venue *" className="md:col-span-2">
              <input type="text" required className="input-field" value={formData.event_venue} onChange={update('event_venue')} />
            </Field>
            <Field label="Address" className="md:col-span-2">
              <input type="text" className="input-field" value={formData.event_address} onChange={update('event_address')} />
            </Field>
            <Field label="Map link">
              <input type="url" className="input-field" placeholder="https://maps.google.com/..." value={formData.event_map_link} onChange={update('event_map_link')} />
            </Field>
            <Field label="Host phone">
              <input type="tel" maxLength={15} className="input-field" value={formData.host_phone} onChange={update('host_phone')} />
            </Field>
            <Field label="Message" className="md:col-span-2">
              <textarea rows={4} className="input-field" value={formData.custom_message} onChange={update('custom_message')} />
            </Field>
          </div>

          <div className="flex justify-end gap-4 pt-2">
            <Link href={`/dashboard/events/${slug}`} className="btn-secondary">Cancel</Link>
            <button type="submit" disabled={saving} className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed">
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function Field({ label, className = '', children }: { label: string; className?: string; children: React.ReactNode }) {
  return (
    <label className={`block ${className}`}>
      <span className="block text-sm font-medium text-gray-700 mb-2">{label}</span>
      {children}
    </label>
  );
}
