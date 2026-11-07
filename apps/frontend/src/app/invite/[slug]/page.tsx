'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'next/navigation';
import axios from 'axios';
import { gsap } from 'gsap';
import { invitationsAPI, apiErrorMessage } from '@/lib/api';
import { getFingerprint, type FingerprintResult } from '@/lib/fingerprint';
import { inviteViewStateForCheck, inviteViewStateForError, type InviteViewState } from '@/lib/invite';
import type { ApiEnvelope, GuestCheckResult, GuestRegisterResult, PublicInvitation, PublicInviteResponse } from '@/lib/types';

const statusOf = (err: unknown) => (axios.isAxiosError(err) ? err.response?.status : undefined);

export default function InvitationPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [viewState, setViewState] = useState<InviteViewState>('loading');
  const [invitation, setInvitation] = useState<PublicInvitation | null>(null);
  const [fingerprint, setFingerprint] = useState<FingerprintResult | null>(null);
  const [guestName, setGuestName] = useState('');
  const [isTestGuest, setIsTestGuest] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [rsvp, setRsvp] = useState<boolean | null>(null);
  const [animationDone, setAnimationDone] = useState(false);
  const animationRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setIsTestGuest(new URLSearchParams(window.location.search).get('test') === '1');

    (async () => {
      try {
        const res = await invitationsAPI.get(slug);
        setInvitation((res.data as ApiEnvelope<PublicInviteResponse>).data.invitation);

        const fp = await getFingerprint();
        setFingerprint(fp);
        const check = (await invitationsAPI.check(slug, { fingerprint: fp.fingerprint })).data as ApiEnvelope<GuestCheckResult>;
        if (check.data.already_registered) setGuestName(check.data.guest_name);
        setViewState(inviteViewStateForCheck(check.data));
      } catch (err) {
        setError(apiErrorMessage(err, 'Failed to load invitation'));
        setViewState(inviteViewStateForError(statusOf(err)));
      }
    })();
  }, [slug]);

  const playAnimations = useCallback(() => {
    if (!animationRef.current) return;
    gsap.set(['.step-1', '.step-3', '.step-4'], { opacity: 0, y: 32 });
    gsap.set('.step-2', { opacity: 0, scale: 0.95 });
    gsap
      .timeline({ onComplete: () => setAnimationDone(true) })
      .to('.step-1', { opacity: 1, y: 0, duration: 1.2, ease: 'power3.out' })
      .to('.step-2', { opacity: 1, scale: 1, duration: 1.5, ease: 'back.out(1.7)' }, '+=0.6')
      .to('.step-3', { opacity: 1, y: 0, duration: 1, ease: 'power2.out' }, '+=0.6')
      .to('.step-4', { opacity: 1, y: 0, duration: 1, ease: 'power2.out' }, '+=0.4');
  }, []);

  useEffect(() => {
    if (viewState === 'animation' && invitation) playAnimations();
    if (viewState === 'welcome-back') setAnimationDone(true);
  }, [viewState, invitation, playAnimations]);

  const handleNameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!guestName.trim()) {
      setError('Please enter your name');
      return;
    }
    if (!fingerprint) {
      setError('Still preparing the invitation, please try again in a moment.');
      return;
    }
    setError('');
    setSubmitting(true);
    try {
      const { fingerprint: fp, ...components } = fingerprint;
      const res = await invitationsAPI.register(slug, {
        name: guestName.trim(),
        fingerprint: fp,
        is_test: isTestGuest,
        ...components,
      });
      const result = (res.data as ApiEnvelope<GuestRegisterResult>).data;
      setGuestName(result.guest_name);
      setViewState(result.already_registered ? 'welcome-back' : 'animation');
    } catch (err) {
      const state = inviteViewStateForError(statusOf(err));
      if (state === 'limit-reached' || state === 'expired' || state === 'not-found') {
        setViewState(state);
      } else {
        setError(apiErrorMessage(err, 'Failed to register. Please try again.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleRsvp = async (attending: boolean) => {
    if (!fingerprint) return;
    try {
      await invitationsAPI.rsvp(slug, { fingerprint: fingerprint.fingerprint, attending });
      setRsvp(attending);
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not save your RSVP'));
    }
  };

  if (viewState === 'loading') {
    return (
      <Screen>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading invitation...</p>
        </div>
      </Screen>
    );
  }

  if (viewState === 'expired') {
    return <Notice icon="⏰" title="Invitation Expired" body="This invitation has expired. Please contact the host for more information." />;
  }
  if (viewState === 'limit-reached') {
    return (
      <Notice
        icon="🚫"
        title="Guest Limit Reached"
        body="The maximum number of guests for this invitation has been reached. Please contact the host if you believe this is an error."
      />
    );
  }
  if (viewState === 'not-found') {
    return <Notice icon="🔍" title="Invitation Not Found" body="This invitation link is not valid. Please check the link you received." />;
  }
  if (viewState === 'error' || !invitation) {
    return <Notice icon="❌" title="Something went wrong" body={error || 'Failed to load invitation'} />;
  }

  if (viewState === 'form') {
    return (
      <Screen>
        <div className="card max-w-md w-full">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">💝</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">You&apos;re Invited!</h1>
            <p className="text-gray-600">Please enter your name to view the invitation</p>
          </div>
          <form onSubmit={handleNameSubmit} className="space-y-6">
            {error && <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
            <div>
              <label htmlFor="guestName" className="block text-sm font-medium text-gray-700 mb-2">Your Name</label>
              <input
                id="guestName"
                type="text"
                required
                autoFocus
                maxLength={200}
                className="input-field text-center text-lg"
                placeholder="Enter your full name"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
              />
            </div>
            {isTestGuest && <p className="text-center text-sm text-purple-600">Test view: counts against test links</p>}
            <button type="submit" disabled={submitting} className="w-full btn-primary text-lg py-3 disabled:opacity-50">
              {submitting ? 'Opening...' : 'View Invitation'}
            </button>
          </form>
        </div>
      </Screen>
    );
  }

  // 'animation' (first visit) or 'welcome-back' (returning device)
  const theme = invitation.template_theme ?? {};
  const eventDate = new Date(invitation.event_date);

  return (
    <div
      ref={animationRef}
      className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50 overflow-hidden"
      style={theme.background ? { background: theme.background } : undefined}
    >
      <div className="min-h-screen flex items-center justify-center px-4 py-12">
        <div className="max-w-4xl w-full space-y-10">
          <div className="step-1 text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-primary-600 mb-4" style={theme.primary ? { color: theme.primary } : undefined}>
              {viewState === 'welcome-back' ? `Welcome back, ${guestName}!` : `Welcome, ${guestName}!`}
            </h1>
          </div>

          <div className="step-2 text-center">
            <div className="bg-white rounded-2xl shadow-2xl overflow-hidden">
              {invitation.banner_image && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={invitation.banner_image} alt="" className="w-full max-h-80 object-cover" />
              )}
              <div className="p-10">
                <p className="text-gray-600 text-lg mb-4">You are cordially invited to</p>
                <h2 className="text-4xl md:text-6xl font-serif font-bold text-gray-900">{invitation.event_title}</h2>
                {invitation.host_name && <p className="text-gray-600 mt-4">Hosted by {invitation.host_name}</p>}
              </div>
            </div>
          </div>

          <div className="step-3 text-center">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="text-6xl mb-4">📅</div>
              <p className="text-2xl font-semibold text-gray-900 mb-2">
                {eventDate.toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
              <p className="text-xl text-gray-600">
                at {eventDate.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' })}
              </p>
            </div>
          </div>

          <div className="step-4">
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="text-center mb-6">
                <div className="text-6xl mb-4">📍</div>
                <h3 className="text-3xl font-bold text-gray-900 mb-2">{invitation.event_venue}</h3>
                {invitation.event_address && <p className="text-lg text-gray-600 whitespace-pre-line">{invitation.event_address}</p>}
                {invitation.event_map_link && (
                  <a href={invitation.event_map_link} target="_blank" rel="noreferrer" className="btn-secondary inline-block mt-4">
                    Open in Maps
                  </a>
                )}
              </div>
              {invitation.custom_message && (
                <div className="mt-6 p-6 bg-pink-50 rounded-lg">
                  <p className="text-gray-700 text-center italic whitespace-pre-line">&ldquo;{invitation.custom_message}&rdquo;</p>
                </div>
              )}
              {invitation.gallery_images?.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-6">
                  {invitation.gallery_images.map((src) => (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img key={src} src={src} alt="" className="w-full h-32 object-cover rounded-lg" />
                  ))}
                </div>
              )}
            </div>
          </div>

          {invitation.background_music && <audio src={invitation.background_music} autoPlay loop controls className="mx-auto" />}

          {animationDone && (
            <div className="text-center space-y-4">
              <p className="text-2xl font-semibold text-gray-900">Will you be attending?</p>
              {error && <p className="text-red-600">{error}</p>}
              {rsvp === null ? (
                <div className="flex justify-center gap-4">
                  <button onClick={() => handleRsvp(true)} className="btn-primary px-8">Yes, I&apos;ll be there</button>
                  <button onClick={() => handleRsvp(false)} className="btn-secondary px-8">Sorry, can&apos;t make it</button>
                </div>
              ) : (
                <p className="text-gray-700">
                  {rsvp ? "Wonderful! We can't wait to celebrate with you." : "Thanks for letting us know. You'll be missed!"}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center px-4">
      {children}
    </div>
  );
}

function Notice({ icon, title, body }: { icon: string; title: string; body: string }) {
  return (
    <Screen>
      <div className="card max-w-md text-center">
        <div className="text-6xl mb-4">{icon}</div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{title}</h1>
        <p className="text-gray-600">{body}</p>
      </div>
    </Screen>
  );
}
