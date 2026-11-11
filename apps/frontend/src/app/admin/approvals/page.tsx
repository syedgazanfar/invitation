'use client';

import { useEffect, useState } from 'react';
import { adminAPI, apiErrorMessage } from '@/lib/api';
import type { ApiEnvelope, PendingApproval } from '@/lib/types';

type RowState = { notes: string; rejecting: boolean; reason: string; blockUser: boolean; busy: boolean; error: string };
const freshRow = (): RowState => ({ notes: '', rejecting: false, reason: '', blockUser: true, busy: false, error: '' });

export default function AdminApprovalsPage() {
  const [pending, setPending] = useState<PendingApproval[]>([]);
  const [rows, setRows] = useState<Record<string, RowState>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [done, setDone] = useState('');

  useEffect(() => {
    adminAPI
      .getPendingApprovals()
      .then((res) => {
        const list = (res.data as ApiEnvelope<PendingApproval[]>).data ?? [];
        setPending(list);
        setRows(Object.fromEntries(list.map((p) => [p.id, freshRow()])));
      })
      .catch((err) => setError(apiErrorMessage(err, 'Failed to load pending approvals')))
      .finally(() => setLoading(false));
  }, []);

  const patchRow = (id: string, patch: Partial<RowState>) =>
    setRows((prev) => ({ ...prev, [id]: { ...(prev[id] ?? freshRow()), ...patch } }));

  const removeRow = (id: string, message: string) => {
    setPending((prev) => prev.filter((p) => p.id !== id));
    setDone(message);
  };

  const approve = async (p: PendingApproval) => {
    const row = rows[p.id] ?? freshRow();
    patchRow(p.id, { busy: true, error: '' });
    try {
      await adminAPI.approveUser(p.id, row.notes.trim() ? { notes: row.notes.trim() } : undefined);
      removeRow(p.id, `Approved ${p.full_name || p.username}.`);
    } catch (err) {
      patchRow(p.id, { busy: false, error: apiErrorMessage(err, 'Approval failed') });
    }
  };

  const reject = async (p: PendingApproval) => {
    const row = rows[p.id] ?? freshRow();
    if (!row.reason.trim()) {
      patchRow(p.id, { error: 'A rejection reason is required.' });
      return;
    }
    patchRow(p.id, { busy: true, error: '' });
    try {
      await adminAPI.rejectUser(p.id, { reason: row.reason.trim(), block_user: row.blockUser });
      removeRow(p.id, `Rejected ${p.full_name || p.username}.`);
    } catch (err) {
      patchRow(p.id, { busy: false, error: apiErrorMessage(err, 'Rejection failed') });
    }
  };

  if (loading) return <div className="text-center py-16 text-gray-500">Loading approvals...</div>;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Pending Approvals</h1>

      {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
      {done && <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">{done}</div>}

      {pending.length === 0 && !error ? (
        <div className="card text-center py-12 text-gray-500">No users are waiting for approval.</div>
      ) : (
        <div className="space-y-4">
          {pending.map((p) => {
            const row = rows[p.id] ?? freshRow();
            return (
              <div key={p.id} className="card space-y-4">
                <div className="grid md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">User</p>
                    <p className="font-semibold text-gray-900">{p.full_name || p.username}</p>
                    <p className="text-sm text-gray-600">@{p.username} · {p.phone}</p>
                    {p.email && <p className="text-sm text-gray-600">{p.email}</p>}
                    {p.created_at && <p className="text-xs text-gray-400 mt-1">Signed up {new Date(p.created_at).toLocaleString()}</p>}
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Plan</p>
                    {p.current_plan ? (
                      <>
                        <p className="font-semibold text-gray-900">{p.current_plan.name}</p>
                        <p className="text-sm text-gray-600">₹{p.current_plan.price_inr.toLocaleString('en-IN')}</p>
                        <p className="text-xs text-gray-500">
                          {p.current_plan.regular_links} links · {p.current_plan.test_links} test links
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-gray-500">No plan selected yet</p>
                    )}
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Latest order</p>
                    {p.latest_order ? (
                      <>
                        <p className="font-semibold text-gray-900">{p.latest_order.order_number}</p>
                        <p className="text-sm text-gray-600">{p.latest_order.status.replace(/_/g, ' ')}</p>
                        <p className="text-xs text-gray-500">
                          ₹{p.latest_order.payment_amount.toLocaleString('en-IN')}
                          {p.latest_order.payment_method ? ` · ${p.latest_order.payment_method}` : ''}
                        </p>
                      </>
                    ) : (
                      <p className="text-sm text-gray-500">No order yet</p>
                    )}
                  </div>
                </div>

                {row.error && <p className="text-sm text-red-600">{row.error}</p>}

                {row.rejecting ? (
                  <div className="space-y-3 border-t pt-4">
                    <label className="block">
                      <span className="block text-sm font-medium text-gray-700 mb-1">Rejection reason *</span>
                      <textarea
                        rows={2}
                        className="input-field"
                        value={row.reason}
                        onChange={(e) => patchRow(p.id, { reason: e.target.value })}
                      />
                    </label>
                    <label className="flex items-center gap-2 text-sm text-gray-700">
                      <input type="checkbox" checked={row.blockUser} onChange={(e) => patchRow(p.id, { blockUser: e.target.checked })} />
                      Block this user
                    </label>
                    <div className="flex gap-2">
                      <button
                        disabled={row.busy}
                        onClick={() => reject(p)}
                        className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
                      >
                        {row.busy ? 'Rejecting...' : 'Confirm reject'}
                      </button>
                      <button disabled={row.busy} onClick={() => patchRow(p.id, { rejecting: false, error: '' })} className="btn-secondary">
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-wrap gap-2 items-center border-t pt-4">
                    <input
                      type="text"
                      className="input-field flex-1 min-w-[12rem]"
                      placeholder="Approval notes (optional), e.g. paid via UPI"
                      value={row.notes}
                      onChange={(e) => patchRow(p.id, { notes: e.target.value })}
                    />
                    <button disabled={row.busy} onClick={() => approve(p)} className="btn-primary disabled:opacity-50">
                      {row.busy ? 'Approving...' : 'Approve'}
                    </button>
                    <button
                      disabled={row.busy}
                      onClick={() => patchRow(p.id, { rejecting: true, error: '' })}
                      className="px-4 py-2 rounded-lg text-sm font-semibold bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50"
                    >
                      Reject
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
