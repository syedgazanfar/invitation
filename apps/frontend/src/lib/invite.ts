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

/** State to show after POST /invite/<slug>/check/. */
export function inviteViewStateForCheck(result: GuestCheckResult): InviteViewState {
  if (result.already_registered) return 'welcome-back';
  if (!result.can_register) return 'limit-reached';
  return 'form';
}
