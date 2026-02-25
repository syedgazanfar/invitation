'use client';

import { useEffect, useState, useRef } from 'react';
import { useParams } from 'next/navigation';
import { invitationsAPI } from '@/lib/api';
import { InvitationData } from '@/types';
import { gsap } from 'gsap';

type ViewState = 'loading' | 'name-entry' | 'animation' | 'error' | 'expired' | 'limit-reached';

export default function InvitationPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [viewState, setViewState] = useState<ViewState>('loading');
  const [guestName, setGuestName] = useState('');
  const [isTestGuest, setIsTestGuest] = useState(false);
  const [invitationData, setInvitationData] = useState<InvitationData | null>(null);
  const [error, setError] = useState('');

  const animationRef = useRef<HTMLDivElement>(null);
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    checkInvitation();
  }, [slug]);

  useEffect(() => {
    if (viewState === 'animation' && invitationData) {
      playAnimations();
    }
  }, [viewState, invitationData]);

  const checkInvitation = async () => {
    try {
      await invitationsAPI.getMeta(slug);
      setViewState('name-entry');
    } catch (err: any) {
      const message = err.response?.data?.message || 'Invitation not found';
      if (message.includes('expired')) {
        setViewState('expired');
      } else {
        setError(message);
        setViewState('error');
      }
    }
  };

  const handleNameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!guestName.trim()) {
      setError('Please enter your name');
      return;
    }

    setError('');

    try {
      const response = await invitationsAPI.registerGuest(slug, {
        guestName: guestName.trim(),
        isTest: isTestGuest,
      });

      setInvitationData(response.data.data);
      setViewState('animation');
    } catch (err: any) {
      const message = err.response?.data?.message || 'Failed to register';
      if (message.includes('limit reached')) {
        setViewState('limit-reached');
      } else {
        setError(message);
      }
    }
  };

  const playAnimations = () => {
    if (!animationRef.current || !invitationData) return;

    const timeline = gsap.timeline({
      onComplete: () => {
        setCurrentStep(5);
      },
    });

    // Step 1: Welcome guest
    timeline.to('.step-1', {
      opacity: 1,
      y: 0,
      duration: 1.2,
      ease: 'power3.out',
      onStart: () => setCurrentStep(1),
    });

    // Step 2: Show couple names
    timeline.to('.step-2', {
      opacity: 1,
      scale: 1,
      duration: 1.5,
      ease: 'back.out(1.7)',
      onStart: () => setCurrentStep(2),
    }, '+=1');

    // Step 3: Show date and time
    timeline.to('.step-3', {
      opacity: 1,
      y: 0,
      duration: 1,
      ease: 'power2.out',
      onStart: () => setCurrentStep(3),
    }, '+=1');

    // Step 4: Show venue details
    timeline.to('.step-4', {
      opacity: 1,
      y: 0,
      duration: 1,
      ease: 'power2.out',
      onStart: () => setCurrentStep(4),
    }, '+=0.8');
  };

  if (viewState === 'loading') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading invitation...</p>
        </div>
      </div>
    );
  }

  if (viewState === 'expired') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center px-4">
        <div className="card max-w-md text-center">
          <div className="text-6xl mb-4">⏰</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Invitation Expired</h1>
          <p className="text-gray-600">
            This invitation has expired. Please contact the couple for more information.
          </p>
        </div>
      </div>
    );
  }

  if (viewState === 'limit-reached') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center px-4">
        <div className="card max-w-md text-center">
          <div className="text-6xl mb-4">🚫</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Guest Limit Reached</h1>
          <p className="text-gray-600">
            The maximum number of guests for this invitation has been reached.
            Please contact the couple if you believe this is an error.
          </p>
        </div>
      </div>
    );
  }

  if (viewState === 'error') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center px-4">
        <div className="card max-w-md text-center">
          <div className="text-6xl mb-4">❌</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Error</h1>
          <p className="text-gray-600">{error || 'Failed to load invitation'}</p>
        </div>
      </div>
    );
  }

  if (viewState === 'name-entry') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 flex items-center justify-center px-4">
        <div className="card max-w-md w-full">
          <div className="text-center mb-8">
            <div className="text-6xl mb-4">💝</div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              You're Invited!
            </h1>
            <p className="text-gray-600">
              Please enter your name to view the invitation
            </p>
          </div>

          <form onSubmit={handleNameSubmit} className="space-y-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="guestName" className="block text-sm font-medium text-gray-700 mb-2">
                Your Name
              </label>
              <input
                id="guestName"
                type="text"
                required
                autoFocus
                className="input-field text-center text-lg"
                placeholder="Enter your full name"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
              />
            </div>

            <div className="flex items-center justify-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="mr-2"
                  checked={isTestGuest}
                  onChange={(e) => setIsTestGuest(e.target.checked)}
                />
                <span className="text-sm text-gray-600">This is a test view</span>
              </label>
            </div>

            <button type="submit" className="w-full btn-primary text-lg py-3">
              View Invitation
            </button>
          </form>
        </div>
      </div>
    );
  }

  if (viewState === 'animation' && invitationData) {
    const { guest, event } = invitationData;

    return (
      <div
        ref={animationRef}
        className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50 overflow-hidden"
      >
        <div className="min-h-screen flex items-center justify-center px-4 py-12">
          <div className="max-w-4xl w-full space-y-12">
            {/* Step 1: Welcome Guest */}
            <div className="step-1 opacity-0 translate-y-8 text-center">
              <h1 className="text-4xl md:text-6xl font-bold text-primary-600 mb-4">
                Welcome, {guest.name}!
              </h1>
            </div>

            {/* Step 2: Couple Names */}
            <div className="step-2 opacity-0 scale-95 text-center">
              <div className="bg-white rounded-2xl shadow-2xl p-12">
                <p className="text-gray-600 text-lg mb-4">You are cordially invited to celebrate the wedding of</p>
                <h2 className="text-5xl md:text-7xl font-serif font-bold text-gray-900 mb-2">
                  {event.brideName}
                </h2>
                <p className="text-3xl text-gray-600 my-6">&</p>
                <h2 className="text-5xl md:text-7xl font-serif font-bold text-gray-900">
                  {event.groomName}
                </h2>
              </div>
            </div>

            {/* Step 3: Date and Time */}
            <div className="step-3 opacity-0 translate-y-8 text-center">
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="text-6xl mb-4">📅</div>
                <p className="text-2xl font-semibold text-gray-900 mb-2">
                  {new Date(event.weddingDate).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </p>
                <p className="text-xl text-gray-600">
                  at {event.startTime}
                </p>
              </div>
            </div>

            {/* Step 4: Venue */}
            <div className="step-4 opacity-0 translate-y-8">
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="text-center mb-6">
                  <div className="text-6xl mb-4">📍</div>
                  <h3 className="text-3xl font-bold text-gray-900 mb-2">
                    {event.venueName}
                  </h3>
                  <p className="text-lg text-gray-600">
                    {event.address}
                  </p>
                  <p className="text-lg text-gray-600">
                    {event.city}, {event.country}
                  </p>
                </div>

                {/* Embedded Map */}
                {event.lat && event.lng && (
                  <div className="w-full h-64 bg-gray-200 rounded-lg overflow-hidden">
                    <iframe
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      style={{ border: 0 }}
                      src={`https://www.google.com/maps?q=${event.lat},${event.lng}&output=embed`}
                      allowFullScreen
                    />
                  </div>
                )}

                {/* Message */}
                {event.message && (
                  <div className="mt-6 p-6 bg-pink-50 rounded-lg">
                    <p className="text-gray-700 text-center italic">
                      "{event.message}"
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Final Message */}
            {currentStep >= 5 && (
              <div className="text-center animate-fade-in">
                <p className="text-2xl font-semibold text-gray-900 mb-2">
                  We can't wait to celebrate with you!
                </p>
                <p className="text-gray-600">
                  Save the date and see you there!
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return null;
}
