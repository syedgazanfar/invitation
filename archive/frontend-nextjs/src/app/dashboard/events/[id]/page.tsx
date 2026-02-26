'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { eventsAPI } from '@/lib/api';
import { Event, Guest } from '@/types';

export default function EventDetailsPage() {
  const params = useParams();
  const eventId = params.id as string;

  const [event, setEvent] = useState<Event | null>(null);
  const [guests, setGuests] = useState<Guest[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
    total: 0,
    totalPages: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadEvent();
    loadGuests();
  }, [eventId]);

  const loadEvent = async () => {
    try {
      const response = await eventsAPI.getOne(eventId);
      setEvent(response.data.data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load event');
    } finally {
      setLoading(false);
    }
  };

  const loadGuests = async (page = 1) => {
    try {
      const response = await eventsAPI.getGuests(eventId, page);
      setGuests(response.data.data.guests);
      setPagination(response.data.data.pagination);
    } catch (err) {
      console.error('Failed to load guests:', err);
    }
  };

  const handleExportCSV = async () => {
    try {
      const response = await eventsAPI.exportGuestsCSV(eventId);
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `event-${eventId}-guests.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export CSV:', err);
    }
  };

  if (loading) {
    return <div className="text-center py-12">Loading event...</div>;
  }

  if (error || !event) {
    return (
      <div className="card">
        <p className="text-red-600">{error || 'Event not found'}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {event.brideName} & {event.groomName}
          </h1>
          <p className="text-gray-600">
            {new Date(event.weddingDate).toLocaleDateString()} at {event.startTime}
          </p>
        </div>
        <span className={`px-4 py-2 rounded-full text-sm font-medium ${
          event.status === 'ACTIVE' ? 'bg-green-200 text-green-800' :
          event.status === 'DRAFT' ? 'bg-gray-200 text-gray-800' :
          'bg-red-200 text-red-800'
        }`}>
          {event.status}
        </span>
      </div>

      {/* Event Details */}
      <div className="card">
        <h2 className="text-xl font-semibold mb-4">Event Details</h2>

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600">Plan</p>
            <p className="font-medium">{event.plan?.name || event.planCode}</p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Template</p>
            <p className="font-medium">{event.template?.name}</p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Venue</p>
            <p className="font-medium">{event.venueName}</p>
          </div>

          <div>
            <p className="text-sm text-gray-600">Location</p>
            <p className="font-medium">{event.city}, {event.country}</p>
          </div>

          <div className="md:col-span-2">
            <p className="text-sm text-gray-600">Address</p>
            <p className="font-medium">{event.address}</p>
          </div>

          {event.message && (
            <div className="md:col-span-2">
              <p className="text-sm text-gray-600">Message</p>
              <p className="font-medium">{event.message}</p>
            </div>
          )}
        </div>
      </div>

      {/* Invitation URL */}
      {event.status === 'ACTIVE' && event.inviteUrl && (
        <div className="card bg-green-50 border-2 border-green-200">
          <h2 className="text-xl font-semibold mb-4">Invitation URL</h2>

          <div className="bg-white rounded-lg p-4 mb-4">
            <div className="flex items-center justify-between">
              <code className="text-sm flex-1 mr-4 break-all">{event.inviteUrl}</code>
              <button
                onClick={() => navigator.clipboard.writeText(event.inviteUrl!)}
                className="btn-secondary text-sm whitespace-nowrap"
              >
                Copy URL
              </button>
            </div>
          </div>

          {event.expiresAt && (
            <p className="text-sm text-gray-600">
              Expires: {new Date(event.expiresAt).toLocaleString()}
            </p>
          )}
        </div>
      )}

      {/* Guest Statistics */}
      {event.guestStats && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Guest Statistics</h2>
            <button onClick={handleExportCSV} className="btn-secondary text-sm">
              Export CSV
            </button>
          </div>

          <div className="grid md:grid-cols-3 gap-6 mb-6">
            <div className="bg-blue-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Regular Guests</p>
              <p className="text-3xl font-bold text-blue-600">
                {event.guestStats.regularGuests.current}
                <span className="text-lg text-gray-600"> / {event.guestStats.regularGuests.max}</span>
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {event.guestStats.regularGuests.remaining} remaining
              </p>
            </div>

            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Test Opens</p>
              <p className="text-3xl font-bold text-purple-600">
                {event.guestStats.testGuests.current}
                <span className="text-lg text-gray-600"> / {event.guestStats.testGuests.max}</span>
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {event.guestStats.testGuests.remaining} remaining
              </p>
            </div>

            <div className="bg-green-50 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-1">Total Opens</p>
              <p className="text-3xl font-bold text-green-600">
                {event.guestStats.total.current}
                <span className="text-lg text-gray-600"> / {event.guestStats.total.max}</span>
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {event.guestStats.total.remaining} remaining
              </p>
            </div>
          </div>

          {/* Guest List */}
          {guests.length > 0 && (
            <div>
              <h3 className="font-semibold mb-3">Guest List</h3>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date/Time
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        IP Address
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {guests.map((guest) => (
                      <tr key={guest.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {guest.guestName}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            guest.isTest ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                          }`}>
                            {guest.isTest ? 'Test' : 'Regular'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(guest.createdAt).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {guest.ip || 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {pagination.totalPages > 1 && (
                <div className="flex justify-between items-center mt-4">
                  <p className="text-sm text-gray-600">
                    Page {pagination.page} of {pagination.totalPages} ({pagination.total} total guests)
                  </p>
                  <div className="space-x-2">
                    <button
                      onClick={() => loadGuests(pagination.page - 1)}
                      disabled={pagination.page === 1}
                      className="btn-secondary text-sm disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => loadGuests(pagination.page + 1)}
                      disabled={pagination.page === pagination.totalPages}
                      className="btn-secondary text-sm disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
