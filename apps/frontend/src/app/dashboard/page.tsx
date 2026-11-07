'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { eventsAPI, apiErrorMessage } from '@/lib/api';
import type { InvitationListItem, Paginated } from '@/lib/types';

function statusOf(inv: InvitationListItem): { label: string; className: string } {
  if (inv.is_expired) return { label: 'Expired', className: 'bg-red-200 text-red-800' };
  if (inv.is_active) return { label: 'Active', className: 'bg-green-200 text-green-800' };
  const label = (inv.order_status || 'Draft').replace(/_/g, ' ').toLowerCase();
  return { label: label.charAt(0).toUpperCase() + label.slice(1), className: 'bg-yellow-100 text-yellow-800' };
}

export default function DashboardPage() {
  const [invitations, setInvitations] = useState<InvitationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [welcome, setWelcome] = useState(false);

  useEffect(() => {
    // Read the query string directly (useSearchParams would need a Suspense boundary).
    setWelcome(new URLSearchParams(window.location.search).get('welcome') === '1');

    eventsAPI
      .getAll()
      .then((res) => setInvitations((res.data as Paginated<InvitationListItem>).results ?? []))
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load invitations')))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="text-center py-12">Loading invitations...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Invitations</h1>
        <Link href="/dashboard/events/new" className="btn-primary">
          Create Invitation
        </Link>
      </div>

      {welcome && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded-lg mb-6">
          Your account has been created. An admin will review and approve it before your invitation link goes live.
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">{error}</div>
      )}

      {invitations.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-4">You haven&apos;t created any invitations yet.</p>
          <Link href="/dashboard/events/new" className="btn-primary">
            Create Your First Invitation
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {invitations.map((inv) => {
            const status = statusOf(inv);
            return (
              <div key={inv.id} className="card hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start gap-4 mb-4">
                  <div className="flex gap-4 items-start min-w-0">
                    {inv.template_thumbnail && (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={inv.template_thumbnail}
                        alt={inv.template_name}
                        className="w-16 h-16 rounded object-cover flex-shrink-0"
                      />
                    )}
                    <div className="min-w-0">
                      <h3 className="text-xl font-semibold text-gray-900 mb-1 truncate">{inv.event_title}</h3>
                      <p className="text-gray-600">{new Date(inv.event_date).toLocaleString()}</p>
                      <p className="text-gray-500 text-sm">{inv.template_name}</p>
                    </div>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${status.className}`}>
                    {status.label}
                  </span>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Guests</p>
                    <p className="font-medium">{inv.unique_guests}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Views</p>
                    <p className="font-medium">{inv.total_views}</p>
                  </div>
                  {inv.link_expires_at && (
                    <div>
                      <p className="text-sm text-gray-600">Link expires</p>
                      <p className="font-medium">{new Date(inv.link_expires_at).toLocaleDateString()}</p>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Link href={`/dashboard/events/${inv.slug}`} className="btn-primary text-sm">
                    View Details
                  </Link>
                  <Link href={`/dashboard/events/${inv.slug}/edit`} className="btn-secondary text-sm">
                    Edit
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
