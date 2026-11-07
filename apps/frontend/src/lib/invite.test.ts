import { describe, expect, it } from 'vitest';
import { inviteNotice, inviteViewStateForCheck, inviteViewStateForError } from './invite';

describe('inviteViewStateForError', () => {
  it('maps 410 Gone to the expired state', () => {
    expect(inviteViewStateForError(410)).toBe('expired');
  });

  it('maps 404 to not-found', () => {
    expect(inviteViewStateForError(404)).toBe('not-found');
  });

  it('maps 403 (guest limit reached) to limit-reached', () => {
    expect(inviteViewStateForError(403)).toBe('limit-reached');
  });

  it('maps network errors and anything else to error', () => {
    expect(inviteViewStateForError(undefined)).toBe('error');
    expect(inviteViewStateForError(500)).toBe('error');
  });
});

describe('inviteViewStateForCheck', () => {
  it('greets a returning guest instead of showing the form', () => {
    expect(
      inviteViewStateForCheck({ already_registered: true, guest_name: 'Asha', viewed_at: '2027-01-01T00:00:00Z', message: 'Welcome back, Asha!' }),
    ).toBe('welcome-back');
  });

  it('shows limit-reached when the invitation is full', () => {
    expect(inviteViewStateForCheck({ already_registered: false, can_register: false, remaining_links: 0 })).toBe('limit-reached');
  });

  it('shows the form to a new guest when there is room', () => {
    expect(inviteViewStateForCheck({ already_registered: false, can_register: true, remaining_links: 3 })).toBe('form');
  });
});

describe('inviteNotice', () => {
  it('tells guests a 404 link may simply have expired (Django returns 404 once an invitation is marked expired)', () => {
    const n = inviteNotice('not-found');
    expect(n.title).toMatch(/not available/i);
    expect(n.body).toMatch(/expired/i);
  });

  it('explains expiry and guest limits', () => {
    expect(inviteNotice('expired').title).toMatch(/expired/i);
    expect(inviteNotice('limit-reached').title).toMatch(/limit/i);
  });
});
