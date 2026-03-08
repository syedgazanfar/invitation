'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { eventsAPI } from '@/lib/api';
import { Event, Guest, GuestAnalytics } from '@/types';

type Tab = 'overview' | 'guests' | 'analytics';

export default function EventDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const eventId = params.id as string;

  const [event, setEvent] = useState<Event | null>(null);
  const [guests, setGuests] = useState<Guest[]>([]);
  const [analytics, setAnalytics] = useState<GuestAnalytics | null>(null);
  const [pagination, setPagination] = useState({ page: 1, limit: 50, total: 0, totalPages: 0 });
  const [loading, setLoading] = useState(true);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  useEffect(() => {
    loadEvent();
    loadGuests();
  }, [eventId]);

  useEffect(() => {
    if (activeTab === 'analytics' && !analytics) loadAnalytics();
  }, [activeTab]);

  const loadEvent = async () => {
    try {
      const res = await eventsAPI.getOne(eventId);
      setEvent(res.data.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load event');
    } finally {
      setLoading(false);
    }
  };

  const loadGuests = async (page = 1) => {
    try {
      const res = await eventsAPI.getGuests(eventId, page);
      setGuests(res.data.data.guests);
      setPagination(res.data.data.pagination);
    } catch { /* handled silently */ }
  };

  const loadAnalytics = async () => {
    setAnalyticsLoading(true);
    try {
      const res = await eventsAPI.getAnalytics(eventId);
      setAnalytics(res.data.data);
    } catch { /* handled silently */ } finally {
      setAnalyticsLoading(false);
    }
  };

  const handleExportCSV = async () => {
    try {
      const res = await eventsAPI.exportGuestsCSV(eventId);
      const blob = new Blob([res.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `event-${eventId}-guests.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch { /* handled silently */ }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this event? This cannot be undone.')) return;
    try {
      await eventsAPI.delete(eventId);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete event');
    }
  };

  if (loading) return <div className="text-center py-12">Loading event...</div>;
  if (error || !event) return <div className="card"><p className="text-red-600">{error || 'Event not found'}</p></div>;

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'guests', label: `Guests (${event.guestStats?.total.current ?? 0})` },
    { id: 'analytics', label: 'Analytics' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-1">
            {event.brideName} & {event.groomName}
          </h1>
          <p className="text-gray-500">{new Date(event.weddingDate).toLocaleDateString()} at {event.startTime}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`px-4 py-1.5 rounded-full text-sm font-semibold ${
            event.status === 'ACTIVE' ? 'bg-green-100 text-green-800' :
            event.status === 'DRAFT'  ? 'bg-gray-100 text-gray-700' :
            'bg-red-100 text-red-700'
          }`}>{event.status}</span>
          {event.status === 'DRAFT' && (
            <>
              <Link href={`/dashboard/events/${eventId}/edit`} className="btn-secondary text-sm">Edit</Link>
              <button onClick={handleDelete} className="px-4 py-2 rounded-lg text-sm font-medium bg-red-100 text-red-700 hover:bg-red-200">Delete</button>
            </>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-6">
          {tabs.map((t) => (
            <button key={t.id} onClick={() => setActiveTab(t.id)}
              className={`pb-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === t.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {/* ── OVERVIEW TAB ── */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Event Details</h2>
            <div className="grid md:grid-cols-2 gap-4">
              <Detail label="Plan" value={event.plan?.name ?? event.planCode} />
              <Detail label="Template" value={event.template?.name ?? '—'} />
              <Detail label="Venue" value={event.venueName} />
              <Detail label="Location" value={`${event.city}, ${event.country}`} />
              <Detail label="Address" value={event.address} span />
              {event.message && <Detail label="Message" value={event.message} span />}
            </div>
          </div>

          {event.status === 'ACTIVE' && event.inviteUrl && (
            <div className="card bg-green-50 border border-green-200">
              <h2 className="text-lg font-semibold mb-3">Invitation URL</h2>
              <div className="flex items-center gap-3 bg-white rounded-lg p-3 mb-2">
                <code className="text-sm flex-1 break-all text-gray-700">{event.inviteUrl}</code>
                <button onClick={() => navigator.clipboard.writeText(event.inviteUrl!)} className="btn-secondary text-sm whitespace-nowrap">Copy</button>
              </div>
              {event.expiresAt && (
                <p className="text-sm text-gray-500">Expires: {new Date(event.expiresAt).toLocaleString()}</p>
              )}
            </div>
          )}

          {event.guestStats && (
            <div className="grid md:grid-cols-3 gap-4">
              <StatCard label="Regular Guests" value={event.guestStats.regularGuests.current} max={event.guestStats.regularGuests.max} color="blue" />
              <StatCard label="Test Opens" value={event.guestStats.testGuests.current} max={event.guestStats.testGuests.max} color="purple" />
              <StatCard label="Total Opens" value={event.guestStats.total.current} max={event.guestStats.total.max} color="green" />
            </div>
          )}
        </div>
      )}

      {/* ── GUESTS TAB ── */}
      {activeTab === 'guests' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Guest List</h2>
            <button onClick={handleExportCSV} className="btn-secondary text-sm">Export CSV</button>
          </div>
          {guests.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No guests registered yet.</p>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {['#', 'Name', 'Type', 'Registered', 'IP Address'].map((h) => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {guests.map((g, i) => (
                      <tr key={g.id} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm text-gray-400">{(pagination.page - 1) * pagination.limit + i + 1}</td>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">{g.guestName}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${g.isTest ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>
                            {g.isTest ? 'Test' : 'Regular'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">{new Date(g.createdAt).toLocaleString()}</td>
                        <td className="px-4 py-3 text-sm text-gray-400 font-mono">{g.ip || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {pagination.totalPages > 1 && (
                <div className="flex justify-between items-center mt-4 pt-3 border-t">
                  <p className="text-sm text-gray-500">Page {pagination.page} of {pagination.totalPages} · {pagination.total} guests total</p>
                  <div className="flex gap-2">
                    <button onClick={() => loadGuests(pagination.page - 1)} disabled={pagination.page === 1} className="btn-secondary text-sm disabled:opacity-40">Previous</button>
                    <button onClick={() => loadGuests(pagination.page + 1)} disabled={pagination.page === pagination.totalPages} className="btn-secondary text-sm disabled:opacity-40">Next</button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* ── ANALYTICS TAB ── */}
      {activeTab === 'analytics' && (
        analyticsLoading ? (
          <div className="text-center py-16 text-gray-500">Loading analytics...</div>
        ) : !analytics || analytics.summary.total === 0 ? (
          <div className="card text-center py-16">
            <p className="text-4xl mb-3">📊</p>
            <p className="text-lg font-medium text-gray-700 mb-1">No data yet</p>
            <p className="text-sm text-gray-500">Analytics will appear once guests start registering.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <SummaryCard label="Total Registrations" value={analytics.summary.total} />
              <SummaryCard label="Regular Guests" value={analytics.summary.regularCount} sub={`${Math.round((analytics.summary.regularCount / analytics.summary.total) * 100)}%`} />
              <SummaryCard label="Unique IPs" value={analytics.summary.uniqueIPs} />
              <SummaryCard label="Avg / Day" value={analytics.summary.avgPerDay} />
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {analytics.summary.peakDay && (
                <div className="card flex items-center gap-4">
                  <span className="text-3xl">🏆</span>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Peak Day</p>
                    <p className="text-xl font-bold text-gray-800">{analytics.summary.peakDay.date}</p>
                    <p className="text-sm text-gray-500">{analytics.summary.peakDay.count} registrations</p>
                  </div>
                </div>
              )}
              {analytics.summary.peakHour !== null && (
                <div className="card flex items-center gap-4">
                  <span className="text-3xl">⏰</span>
                  <div>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">Peak Hour (UTC)</p>
                    <p className="text-xl font-bold text-gray-800">{formatHour(analytics.summary.peakHour)}</p>
                    <p className="text-sm text-gray-500">{analytics.hourlyDistribution[analytics.summary.peakHour].count} registrations</p>
                  </div>
                </div>
              )}
            </div>

            {/* Timeline */}
            {analytics.timeline.length > 0 && (
              <div className="card">
                <h3 className="text-base font-semibold text-gray-800 mb-5">Registration Timeline</h3>
                <TimelineChart data={analytics.timeline} />
              </div>
            )}

            {/* Hourly distribution */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-800 mb-5">Registrations by Hour (UTC)</h3>
              <HourlyChart data={analytics.hourlyDistribution} />
            </div>

            {/* Breakdown grids */}
            <div className="grid md:grid-cols-3 gap-4">
              <BreakdownCard title="Devices" data={analytics.devices} />
              <BreakdownCard title="Browsers" data={analytics.browsers} />
              <BreakdownCard title="Operating Systems" data={analytics.os} />
            </div>

            {/* First / last */}
            <div className="card">
              <h3 className="text-base font-semibold text-gray-800 mb-4">Registration Window</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <Detail label="First Registration" value={analytics.summary.firstRegistration ? new Date(analytics.summary.firstRegistration).toLocaleString() : '—'} />
                <Detail label="Last Registration" value={analytics.summary.lastRegistration ? new Date(analytics.summary.lastRegistration).toLocaleString() : '—'} />
              </div>
            </div>
          </div>
        )
      )}
    </div>
  );
}

// ─── Small helper components ─────────────────────────────────────────────────

function Detail({ label, value, span }: { label: string; value: string; span?: boolean }) {
  return (
    <div className={span ? 'md:col-span-2' : ''}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm font-medium text-gray-800">{value}</p>
    </div>
  );
}

function StatCard({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  const colors: Record<string, string> = { blue: 'bg-blue-50 text-blue-700', purple: 'bg-purple-50 text-purple-700', green: 'bg-green-50 text-green-700' };
  const barColors: Record<string, string> = { blue: 'bg-blue-500', purple: 'bg-purple-500', green: 'bg-green-500' };
  return (
    <div className={`rounded-xl p-5 ${colors[color]}`}>
      <p className="text-xs font-medium uppercase tracking-wide opacity-70 mb-1">{label}</p>
      <p className="text-3xl font-bold mb-1">{value}<span className="text-base font-normal opacity-60"> / {max}</span></p>
      <div className="w-full bg-white bg-opacity-50 rounded-full h-1.5 mt-2">
        <div className={`h-1.5 rounded-full ${barColors[color]}`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-xs opacity-60 mt-1">{max - value} remaining</p>
    </div>
  );
}

function SummaryCard({ label, value, sub }: { label: string; value: number; sub?: string }) {
  return (
    <div className="card text-center py-5">
      <p className="text-3xl font-bold text-gray-800">{value}</p>
      {sub && <p className="text-sm text-primary-600 font-medium">{sub}</p>}
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function TimelineChart({ data }: { data: { date: string; regular: number; test: number }[] }) {
  const maxVal = Math.max(...data.map((d) => d.regular + d.test), 1);
  const barW = Math.max(20, Math.min(48, Math.floor(600 / data.length) - 6));
  const chartH = 120;

  return (
    <div className="overflow-x-auto">
      <div style={{ minWidth: data.length * (barW + 6) }} className="flex flex-col gap-2">
        <div className="flex items-end gap-1.5" style={{ height: chartH }}>
          {data.map((d) => {
            const total = d.regular + d.test;
            const rH = maxVal > 0 ? Math.round((d.regular / maxVal) * chartH) : 0;
            const tH = maxVal > 0 ? Math.round((d.test / maxVal) * chartH) : 0;
            return (
              <div key={d.date} className="flex flex-col items-center justify-end group relative" style={{ width: barW }}>
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 hidden group-hover:flex flex-col items-center z-10">
                  <div className="bg-gray-800 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                    {d.date}: {total} ({d.regular}R · {d.test}T)
                  </div>
                  <div className="w-2 h-2 bg-gray-800 rotate-45 -mt-1" />
                </div>
                {tH > 0 && <div className="w-full rounded-t bg-purple-400" style={{ height: tH }} />}
                {rH > 0 && <div className={`w-full bg-blue-500 ${tH === 0 ? 'rounded-t' : ''}`} style={{ height: rH }} />}
                {total === 0 && <div className="w-full bg-gray-100 rounded-t" style={{ height: 2 }} />}
              </div>
            );
          })}
        </div>
        {/* X-axis labels */}
        <div className="flex gap-1.5">
          {data.map((d) => (
            <div key={d.date} className="text-center text-gray-400 truncate" style={{ width: barW, fontSize: 9 }}>
              {d.date.slice(5)}
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mt-1">
          <LegendDot color="bg-blue-500" label="Regular" />
          <LegendDot color="bg-purple-400" label="Test" />
        </div>
      </div>
    </div>
  );
}

function HourlyChart({ data }: { data: { hour: number; count: number }[] }) {
  const maxVal = Math.max(...data.map((d) => d.count), 1);
  const chartH = 80;
  return (
    <div className="flex items-end gap-0.5" style={{ height: chartH + 24 }}>
      {data.map((d) => {
        const h = maxVal > 0 ? Math.max(Math.round((d.count / maxVal) * chartH), d.count > 0 ? 3 : 0) : 0;
        return (
          <div key={d.hour} className="flex-1 flex flex-col items-center justify-end group relative">
            <div className="absolute bottom-full mb-1 hidden group-hover:block z-10">
              <div className="bg-gray-800 text-white text-xs rounded px-1.5 py-0.5 whitespace-nowrap">
                {formatHour(d.hour)}: {d.count}
              </div>
            </div>
            <div className={`w-full rounded-t transition-all ${d.count > 0 ? 'bg-indigo-500' : 'bg-gray-100'}`} style={{ height: Math.max(h, 2) }} />
            <span className="text-gray-400 mt-1" style={{ fontSize: 8 }}>
              {d.hour % 3 === 0 ? formatHour(d.hour) : ''}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function BreakdownCard({ title, data }: { title: string; data: { name: string; count: number; pct: number }[] }) {
  const palette = ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-amber-500', 'bg-rose-500', 'bg-cyan-500'];
  return (
    <div className="card">
      <h4 className="text-sm font-semibold text-gray-700 mb-4">{title}</h4>
      {data.length === 0 ? (
        <p className="text-sm text-gray-400">No data</p>
      ) : (
        <div className="space-y-3">
          {data.map((item, i) => (
            <div key={item.name}>
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span className="font-medium">{item.name}</span>
                <span className="text-gray-400">{item.count} · {item.pct}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2">
                <div className={`h-2 rounded-full ${palette[i % palette.length]}`} style={{ width: `${item.pct}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function LegendDot({ color, label }: { color: string; label: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className={`w-3 h-3 rounded-sm ${color}`} />
      <span className="text-xs text-gray-500">{label}</span>
    </div>
  );
}

function formatHour(h: number) {
  if (h === 0) return '12am';
  if (h < 12) return `${h}am`;
  if (h === 12) return '12pm';
  return `${h - 12}pm`;
}
