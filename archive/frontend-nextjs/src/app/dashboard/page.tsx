'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { eventsAPI } from '@/lib/api';
import { Event } from '@/types';

export default function DashboardPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      const response = await eventsAPI.getAll();
      setEvents(response.data.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      DRAFT: 'bg-gray-200 text-gray-800',
      ACTIVE: 'bg-green-200 text-green-800',
      EXPIRED: 'bg-red-200 text-red-800',
    };
    return styles[status as keyof typeof styles] || 'bg-gray-200 text-gray-800';
  };

  if (loading) {
    return <div className="text-center py-12">Loading events...</div>;
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900">My Events</h1>
        <Link href="/dashboard/events/new" className="btn-primary">
          Create New Event
        </Link>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {events.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-600 mb-4">You haven't created any events yet.</p>
          <Link href="/dashboard/events/new" className="btn-primary">
            Create Your First Event
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {events.map((event) => (
            <div key={event.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {event.brideName} & {event.groomName}
                  </h3>
                  <p className="text-gray-600">
                    {new Date(event.weddingDate).toLocaleDateString()} at {event.startTime}
                  </p>
                  <p className="text-gray-500 text-sm">{event.venueName}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadge(event.status)}`}>
                  {event.status}
                </span>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div>
                  <p className="text-sm text-gray-600">Plan</p>
                  <p className="font-medium">{event.plan?.name || event.planCode}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Template</p>
                  <p className="font-medium">{event.template?.name || 'N/A'}</p>
                </div>
                {event.guestStats && (
                  <>
                    <div>
                      <p className="text-sm text-gray-600">Guests</p>
                      <p className="font-medium">
                        {event.guestStats.regularGuests.current} / {event.guestStats.regularGuests.max}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Test Opens</p>
                      <p className="font-medium">
                        {event.guestStats.testGuests.current} / {event.guestStats.testGuests.max}
                      </p>
                    </div>
                  </>
                )}
              </div>

              {event.status === 'ACTIVE' && event.inviteUrl && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-600 mb-2">Invitation URL</p>
                  <div className="flex items-center justify-between">
                    <code className="text-sm bg-white px-3 py-2 rounded border flex-1 mr-2 overflow-x-auto">
                      {event.inviteUrl}
                    </code>
                    <button
                      onClick={() => navigator.clipboard.writeText(event.inviteUrl!)}
                      className="btn-secondary text-sm whitespace-nowrap"
                    >
                      Copy
                    </button>
                  </div>
                  {event.expiresAt && (
                    <p className="text-xs text-gray-500 mt-2">
                      Expires: {new Date(event.expiresAt).toLocaleString()}
                    </p>
                  )}
                </div>
              )}

              <div className="flex gap-2">
                <Link
                  href={`/dashboard/events/${event.id}`}
                  className="btn-primary text-sm"
                >
                  View Details
                </Link>
                {event.status === 'DRAFT' && (
                  <Link
                    href={`/dashboard/events/${event.id}/edit`}
                    className="btn-secondary text-sm"
                  >
                    Edit
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
