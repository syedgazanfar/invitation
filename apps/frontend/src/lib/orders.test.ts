import { describe, expect, it } from 'vitest';
import { orderCreatePayload, pickReusableOrder } from './orders';
import type { OrderSummary } from './types';

const order = (o: Partial<OrderSummary>): OrderSummary => ({
  id: 'o',
  order_number: 'ORD-1',
  plan_name: 'Basic',
  event_type: 'WEDDING',
  event_type_name: '',
  status: 'PENDING_PAYMENT',
  payment_status: 'PENDING',
  approved_at: null,
  created_at: '2026-11-01T00:00:00Z',
  has_invitation: false,
  invitation_slug: null,
  granted_regular_links: 0,
  granted_test_links: 0,
  ...o,
});

describe('pickReusableOrder', () => {
  it('prefers an approved order that has no invitation yet', () => {
    const approved = order({ id: 'a', status: 'APPROVED', granted_regular_links: 100 });
    expect(pickReusableOrder([order({ id: 'p' }), approved])?.id).toBe('a');
  });

  it('reuses a pending order instead of creating another one', () => {
    expect(pickReusableOrder([order({ id: 'p', status: 'PENDING_APPROVAL' })])?.id).toBe('p');
  });

  it('never reuses an order that already has an invitation, or a rejected/expired one', () => {
    expect(
      pickReusableOrder([
        order({ id: 'used', status: 'APPROVED', has_invitation: true }),
        order({ id: 'rej', status: 'REJECTED' }),
        order({ id: 'exp', status: 'EXPIRED' }),
      ]),
    ).toBeNull();
  });

  it('returns null when there are no orders', () => {
    expect(pickReusableOrder([])).toBeNull();
  });
});

describe('orderCreatePayload', () => {
  it('sends every field Django OrderCreateSerializer requires (event_type and event_type_name)', () => {
    expect(orderCreatePayload('PREMIUM')).toEqual({
      plan_code: 'PREMIUM',
      event_type: 'WEDDING',
      event_type_name: 'Wedding',
    });
  });
});
