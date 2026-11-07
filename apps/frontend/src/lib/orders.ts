import type { OrderCreateInput, OrderSummary } from './types';

/**
 * Body for POST /invitations/orders/create/. Django's Order model requires both
 * event_type and event_type_name (neither is blank=True). The create page is
 * wedding-only, so both are fixed.
 */
export function orderCreatePayload(planCode: string): OrderCreateInput {
  return { plan_code: planCode, event_type: 'WEDDING', event_type_name: 'Wedding' };
}

const PENDING = new Set(['PENDING_PAYMENT', 'PENDING_APPROVAL']);

/**
 * The order a new invitation should attach to, or null if a new order is needed.
 *
 * Django only lets an invitation attach to an APPROVED order with links left
 * (Order.can_create_invitation), and admins approve the user's latest order.
 * So reuse an approved, unused order first; otherwise reuse a pending one rather
 * than piling up new unapproved orders on every visit.
 */
export function pickReusableOrder(orders: OrderSummary[]): OrderSummary | null {
  const unused = orders.filter((o) => !o.has_invitation);
  return (
    unused.find((o) => o.status === 'APPROVED') ??
    unused.find((o) => PENDING.has(o.status)) ??
    null
  );
}
