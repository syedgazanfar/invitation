/** Pure view-state helpers for the public invitation page (src/app/invite/[slug]). */
import type { GuestCheckResult } from './types';

export type InviteViewState =
  | 'loading'
  | 'form'
  | 'animation'
  | 'welcome-back'
  | 'limit-reached'
  | 'expired'
  | 'not-found'
  | 'error';

/** State to show when a guest API call fails with this HTTP status. */
export function inviteViewStateForError(status: number | undefined): InviteViewState {
  switch (status) {
    case 410:
      return 'expired';
    case 404:
      return 'not-found';
    case 403:
      return 'limit-reached';
    default:
      return 'error';
  }
}

export interface InviteNotice {
  icon: string;
  title: string;
  body: string;
}

/**
 * Copy for the full-page notices. Note: once Django marks an invitation expired
 * it answers 404 (not 410) for every later visit, so the not-found copy must
 * cover expiry too.
 */
export function inviteNotice(state: 'expired' | 'limit-reached' | 'not-found'): InviteNotice {
  switch (state) {
    case 'expired':
      return { icon: '⏰', title: 'Invitation Expired', body: 'This invitation has expired. Please contact the host for more information.' };
    case 'limit-reached':
      return {
        icon: '🚫',
        title: 'Guest Limit Reached',
        body: 'The maximum number of guests for this invitation has been reached. Please contact the host if you believe this is an error.',
      };
    case 'not-found':
      return {
        icon: '🔍',
        title: 'Invitation Not Available',
        body: 'This invitation link has expired or is no longer active. Please contact the host for an updated link.',
      };
  }
}

/** State to show after POST /invite/<slug>/check/. */
export function inviteViewStateForCheck(result: GuestCheckResult): InviteViewState {
  if (result.already_registered) return 'welcome-back';
  if (!result.can_register) return 'limit-reached';
  return 'form';
}
