'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { eventsAPI, apiErrorMessage } from '@/lib/api';
import type { ApiEnvelope, Guest, InvitationDetail, InvitationStats, Paginated } from '@/lib/types';

type Tab = 'overview' | 'guests' | 'stats';
const GUESTS_PAGE_SIZE = 20; // REST_FRAMEWORK.PAGE_SIZE

export default function InvitationDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [invitation, setInvitation] = useState<InvitationDetail | null>(null);
  const [stats, setStats] = useState<InvitationStats | null>(null);
  const [guests, setGuests] = useState<Paginated<Guest> | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    eventsAPI
      .getOne(slug)
      .then((res) => setInvitation(res.data as InvitationDetail))
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load invitation')))
      .finally(() => setLoading(false));
  }, [slug]);

  const loadGuests = useCallback(
    (p: number) => {
      eventsAPI
        .getGuests(slug, p)
        .then((res) => {
          setGuests(res.data as Paginated<Guest>);
          setPage(p);
        })
        .catch((err) => setError(apiErrorMessage(err, 'Failed to load guests')));
    },
    [slug],
  );

  useEffect(() => {
    if (activeTab === 'guests' && !guests) loadGuests(1);
    if (activeTab === 'stats' && !stats) {
      eventsAPI
        .getStats(slug)
        .then((res) => setStats((res.data as ApiEnvelope<InvitationStats>).data))
        .catch((err) => setError(apiErrorMessage(err, 'Failed to load stats')));
    }
  }, [activeTab, guests, stats, slug, loadGuests]);

  const handleExportCSV = async () => {
    try {
      const res = await eventsAPI.exportGuestsCSV(slug);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `guests-${slug}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to export guests'));
    }
  };

  const copyShareUrl = async () => {
    if (!invitation?.share_url) return;
    await navigator.clipboard.writeText(invitation.share_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <div className="text-center py-12">Loading invitation...</div>;
  if (!invitation) {
    return (
      <div className="card">
        <p className="text-red-600">{error || 'Invitation not found'}</p>
        <Link href="/dashboard" className="btn-secondary text-sm mt-4 inline-block">Back to dashboard</Link>
      </div>
    );
  }

  const status = invitation.is_expired
    ? { label: 'Expired', className: 'bg-red-100 text-red-700' }
    : invitation.is_active
      ? { label: 'Active', className: 'bg-green-100 text-green-800' }
      : { label: 'Awaiting approval', className: 'bg-yellow-100 text-yellow-800' };

  const totalPages = guests ? Math.max(1, Math.ceil(guests.count / GUESTS_PAGE_SIZE)) : 1;
  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'guests', label: `Guests (${invitation.unique_guests})` },
    { id: 'stats', label: 'Stats' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start gap-4 flex-wrap">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">{invitation.event_title}</h1>
          <p className="text-gray-500">{new Date(invitation.event_date).toLocaleString()}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${status.className}`}>{status.label}</span>
          <Link href={`/dashboard/events/${slug}/edit`} className="btn-secondary text-sm">Edit</Link>
        </div>
      </div>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}

      <div className="border-b border-gray-200">
        <nav className="flex space-x-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Invitation link</h2>
            {invitation.is_active && !invitation.is_expired ? (
              <>
                <div className="flex items-center gap-2 bg-gray-50 border rounded-lg p-3 mb-2">
                  <code className="text-sm flex-1 break-all text-gray-700">{invitation.share_url}</code>
                  <button onClick={copyShareUrl} className="btn-secondary text-sm whitespace-nowrap">
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                </div>
                {invitation.link_expires_at && (
                  <p className="text-sm text-gray-500">Expires: {new Date(invitation.link_expires_at).toLocaleString()}</p>
                )}
              </>
            ) : (
              <p className="text-gray-600">
                {invitation.is_expired
                  ? 'This invitation link has expired.'
                  : 'Your link becomes shareable once an admin approves your order.'}
              </p>
            )}
          </div>

          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Event details</h2>
            <dl className="grid sm:grid-cols-2 gap-4">
              <Detail label="Template" value={invitation.template?.name} />
              <Detail label="Host" value={invitation.host_name} />
              <Detail label="Host phone" value={invitation.host_phone} />
              <Detail label="Venue" value={invitation.event_venue} />
              <Detail label="Address" value={invitation.event_address} span />
              {invitation.event_map_link && (
                <div className="sm:col-span-2">
                  <dt className="text-sm text-gray-500">Map</dt>
                  <dd>
                    <a href={invitation.event_map_link} target="_blank" rel="noreferrer" className="text-primary-600 hover:underline break-all">
                      {invitation.event_map_link}
                    </a>
                  </dd>
                </div>
              )}
              <Detail label="Message" value={invitation.custom_message} span />
            </dl>
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            <StatCard label="Guests" value={invitation.unique_guests} />
            <StatCard
              label="Regular links used"
              value={`${invitation.regular_links_used} / ${invitation.regular_links_used + invitation.remaining_regular_links}`}
            />
            <StatCard
              label="Test links used"
              value={`${invitation.test_links_used} / ${invitation.test_links_used + invitation.remaining_test_links}`}
            />
          </div>
        </div>
      )}

      {activeTab === 'guests' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Guest list</h2>
            <button onClick={handleExportCSV} className="btn-secondary text-sm" disabled={!guests?.count}>
              Export CSV
            </button>
          </div>
          {!guests ? (
            <p className="text-gray-500">Loading guests...</p>
          ) : guests.count === 0 ? (
            <p className="text-gray-500">No guests have opened this invitation yet.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2 pr-4">Name</th>
                      <th className="py-2 pr-4">Phone</th>
                      <th className="py-2 pr-4">Attending</th>
                      <th className="py-2 pr-4">Device</th>
                      <th className="py-2 pr-4">Opened</th>
                    </tr>
                  </thead>
                  <tbody>
                    {guests.results.map((g) => (
                      <tr key={g.id} className="border-b last:border-0">
                        <td className="py-2 pr-4 font-medium">{g.name}</td>
                        <td className="py-2 pr-4">{g.phone || '—'}</td>
                        <td className="py-2 pr-4">{g.attending === null ? '—' : g.attending ? 'Yes' : 'No'}</td>
                        <td className="py-2 pr-4">{[g.device_type, g.browser, g.os].filter(Boolean).join(' · ') || '—'}</td>
                        <td className="py-2 pr-4">{new Date(g.viewed_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {totalPages > 1 && (
                <div className="flex justify-between items-center mt-4">
                  <button className="btn-secondary text-sm" disabled={!guests.previous} onClick={() => loadGuests(page - 1)}>
                    Previous
                  </button>
                  <span className="text-sm text-gray-500">Page {page} of {totalPages}</span>
                  <button className="btn-secondary text-sm" disabled={!guests.next} onClick={() => loadGuests(page + 1)}>
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeTab === 'stats' && (
        !stats ? (
          <div className="text-center py-12 text-gray-500">Loading stats...</div>
        ) : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard label="Total views" value={stats.total_views} />
            <StatCard label="Unique guests" value={stats.unique_guests} />
            <StatCard label="Regular links left" value={stats.remaining_regular_links} />
            <StatCard label="Test links left" value={stats.remaining_test_links} />
            <StatCard label="Link valid" value={stats.is_link_valid ? 'Yes' : 'No'} />
            <StatCard label="Days until expiry" value={stats.is_link_valid ? stats.expires_in_days : '—'} />
          </div>
        )
      )}
    </div>
  );
}

function Detail({ label, value, span }: { label: string; value?: string | null; span?: boolean }) {
  return (
    <div className={span ? 'sm:col-span-2' : ''}>
      <dt className="text-sm text-gray-500">{label}</dt>
      <dd className="text-gray-900 whitespace-pre-line">{value || '—'}</dd>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="card">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
