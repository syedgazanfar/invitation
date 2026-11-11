'use client';

/**
 * Single public landing page: what we offer, a short enquiry form
 * (name, WhatsApp number, event date) and "Chat on WhatsApp".
 */
import { useEffect, useState } from 'react';
import axios from 'axios';
import { enquiriesAPI, plansAPI, apiErrorMessage } from '@/lib/api';
import {
  BUSINESS_WHATSAPP_DISPLAY,
  landingEnquiryErrors,
  landingEnquiryPayload,
  whatsappChatUrl,
  type LandingEnquiryErrors,
  type LandingEnquiryForm,
} from '@/lib/landing';
import type { Paginated, Plan } from '@/lib/types';

const SERVICES = [
  { icon: '💍', title: 'Wedding Invitations', text: 'Animated digital wedding cards your guests open with a single link.' },
  { icon: '💐', title: 'Engagement & Roka', text: 'Announce the big news with an elegant, shareable invite.' },
  { icon: '🎂', title: 'Birthdays', text: 'Fun, colourful invitations for kids and milestone birthdays.' },
  { icon: '🪔', title: 'Festivals & Pujas', text: 'Diwali, Eid, griha pravesh, naming ceremonies and more.' },
  { icon: '🎉', title: 'Parties & Events', text: 'Anniversaries, get-togethers and corporate celebrations.' },
  { icon: '📊', title: 'Guest Tracking', text: 'See who opened your invite and collect RSVPs in one place.' },
];

const STEPS = [
  { n: 1, title: 'Tell us about your event', text: 'Send the form below or message us on WhatsApp.' },
  { n: 2, title: 'We design your invitation', text: 'Pick a template; we add your names, venue, photos and message.' },
  { n: 3, title: 'Share one link', text: 'Send it on WhatsApp to all your guests and track RSVPs.' },
];

const EMPTY: LandingEnquiryForm = { name: '', phone: '', event_date: '', website: '' };

function todayISO() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
}

function WhatsAppIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden="true">
      <path d="M17.47 14.38c-.3-.15-1.75-.86-2.02-.96-.27-.1-.47-.15-.67.15-.2.3-.77.96-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.25-.46-2.38-1.47-.88-.79-1.47-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.14-.14.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.61-.92-2.2-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.06 2.88 1.21 3.08c.15.2 2.1 3.2 5.08 4.48.71.31 1.26.49 1.69.63.71.22 1.36.19 1.87.12.57-.09 1.75-.72 2-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35zM12.04 21.8h-.01a9.8 9.8 0 0 1-5-1.37l-.36-.21-3.72.97 1-3.62-.24-.37a9.78 9.78 0 0 1-1.5-5.22c0-5.41 4.41-9.81 9.84-9.81a9.78 9.78 0 0 1 9.83 9.82c0 5.41-4.41 9.81-9.84 9.81zm8.37-18.18A11.76 11.76 0 0 0 12.04.18C5.52.18.21 5.48.2 12c0 2.09.55 4.12 1.59 5.92L.1 24l6.23-1.63a11.8 11.8 0 0 0 5.71 1.46h.01c6.52 0 11.83-5.3 11.84-11.83a11.76 11.76 0 0 0-3.48-8.38z" />
    </svg>
  );
}

export default function LandingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [form, setForm] = useState<LandingEnquiryForm>(EMPTY);
  const [errors, setErrors] = useState<LandingEnquiryErrors>({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState('');
  const [minDate, setMinDate] = useState('');

  useEffect(() => {
    setMinDate(todayISO());
    plansAPI
      .getAll()
      .then((res) => setPlans((res.data as Paginated<Plan>).results ?? []))
      .catch(() => setPlans([])); // pricing section simply hides
  }, []);

  const update = (field: keyof LandingEnquiryForm) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    if (errors[field as keyof LandingEnquiryErrors]) setErrors((prev) => ({ ...prev, [field]: undefined }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');
    const found = landingEnquiryErrors(form);
    setErrors(found);
    if (Object.keys(found).length) return;

    setSubmitting(true);
    try {
      const res = await enquiriesAPI.submit(landingEnquiryPayload(form));
      setSent(res.data?.message || "Thank you! We'll contact you on WhatsApp shortly.");
      setForm(EMPTY);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 429) {
        setFormError('You have sent several enquiries already. Please chat with us on WhatsApp instead.');
      } else {
        const fields = (axios.isAxiosError(err) ? err.response?.data?.errors : undefined) as Record<string, string[]> | undefined;
        if (fields) {
          setErrors({
            name: fields.name?.[0],
            phone: fields.phone?.[0],
            event_date: fields.event_date?.[0],
          });
        }
        setFormError(apiErrorMessage(err, 'Could not send your enquiry. Please try again or chat with us on WhatsApp.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const chatUrl = whatsappChatUrl('Hi! I would like to know more about your digital invitations.');

  return (
    <main className="min-h-screen bg-white text-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-pink-100">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="#top" className="text-xl font-bold text-primary-600">Invvite</a>
          <nav className="hidden sm:flex items-center gap-6 text-sm font-medium text-gray-600">
            <a href="#services" className="hover:text-primary-600">Services</a>
            <a href="#how" className="hover:text-primary-600">How it works</a>
            {plans.length > 0 && <a href="#pricing" className="hover:text-primary-600">Pricing</a>}
            <a href="#enquire" className="hover:text-primary-600">Enquire</a>
          </nav>
          <a
            href={chatUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-lg bg-[#25D366] hover:bg-[#1ebe5b] text-white text-sm font-semibold px-3 py-2"
          >
            <WhatsAppIcon className="w-4 h-4" />
            <span className="hidden sm:inline">Chat on WhatsApp</span>
            <span className="sm:hidden">Chat</span>
          </a>
        </div>
      </header>

      {/* Hero */}
      <section id="top" className="bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
        <div className="max-w-6xl mx-auto px-4 py-16 md:py-24 text-center">
          <p className="text-sm font-semibold tracking-widest uppercase text-primary-600 mb-4">Digital invitations</p>
          <h1 className="text-4xl md:text-6xl font-bold leading-tight mb-6">
            Beautiful invitations,<br className="hidden sm:block" /> shared in one link
          </h1>
          <p className="text-lg md:text-xl text-gray-600 max-w-2xl mx-auto mb-10">
            Weddings, engagements, birthdays and festivals. We design a stunning animated invitation your guests open
            straight from WhatsApp.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a href="#enquire" className="btn-primary text-lg px-8 py-3">Send an enquiry</a>
            <a
              href={chatUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-[#25D366] hover:bg-[#1ebe5b] text-white text-lg font-semibold px-8 py-3"
            >
              <WhatsAppIcon />
              Chat on WhatsApp
            </a>
          </div>
        </div>
      </section>

      {/* Services */}
      <section id="services" className="max-w-6xl mx-auto px-4 py-16 md:py-20">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-3">What we offer</h2>
        <p className="text-gray-600 text-center mb-12">Every invitation is mobile-friendly, animated and ready to share.</p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {SERVICES.map((s) => (
            <div key={s.title} className="card">
              <div className="text-4xl mb-3" aria-hidden="true">{s.icon}</div>
              <h3 className="text-lg font-semibold mb-1">{s.title}</h3>
              <p className="text-gray-600">{s.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section id="how" className="bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 py-16 md:py-20">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">How it works</h2>
          <ol className="grid md:grid-cols-3 gap-6">
            {STEPS.map((s) => (
              <li key={s.n} className="card text-center">
                <span className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary-600 text-white font-bold mb-3">
                  {s.n}
                </span>
                <h3 className="text-lg font-semibold mb-1">{s.title}</h3>
                <p className="text-gray-600">{s.text}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Pricing (live from /api/v1/plans/) */}
      {plans.length > 0 && (
        <section id="pricing" className="max-w-6xl mx-auto px-4 py-16 md:py-20">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-12">Plans</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {plans.map((p) => (
              <div key={p.id} className="card flex flex-col">
                <h3 className="text-xl font-bold">{p.name}</h3>
                <p className="text-3xl font-bold text-primary-600 my-3">{p.display_price}</p>
                <p className="text-gray-600 mb-4">{p.description}</p>
                <ul className="space-y-1 text-sm text-gray-700 mb-6 flex-1">
                  <li>✓ Up to {p.regular_links} guests</li>
                  {(p.features ?? []).slice(0, 5).map((f) => (
                    <li key={f}>✓ {f}</li>
                  ))}
                </ul>
                <a href="#enquire" className="btn-secondary text-center">Enquire about {p.name}</a>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Enquiry form */}
      <section id="enquire" className="bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50">
        <div className="max-w-xl mx-auto px-4 py-16 md:py-20">
          <h2 className="text-3xl md:text-4xl font-bold text-center mb-3">Enquire now</h2>
          <p className="text-gray-600 text-center mb-8">Leave your details and we&apos;ll get back to you on WhatsApp.</p>

          <div className="card">
            {sent ? (
              <div className="text-center py-6" role="status">
                <div className="text-5xl mb-3" aria-hidden="true">✅</div>
                <p className="text-lg font-semibold mb-2">Enquiry sent</p>
                <p className="text-gray-600 mb-6">{sent}</p>
                <button type="button" className="btn-secondary" onClick={() => setSent('')}>Send another</button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} noValidate className="space-y-5">
                {formError && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">{formError}</div>
                )}

                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">Your name *</label>
                  <input id="name" type="text" autoComplete="name" required className="input-field" value={form.name} onChange={update('name')} />
                  {errors.name && <p className="error-message">{errors.name}</p>}
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">WhatsApp number *</label>
                  <input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    inputMode="tel"
                    placeholder="+91 98765 43210"
                    required
                    className="input-field"
                    value={form.phone}
                    onChange={update('phone')}
                  />
                  {errors.phone && <p className="error-message">{errors.phone}</p>}
                </div>

                <div>
                  <label htmlFor="event_date" className="block text-sm font-medium text-gray-700 mb-2">Date of event</label>
                  <input
                    id="event_date"
                    type="date"
                    min={minDate || undefined}
                    className="input-field"
                    value={form.event_date}
                    onChange={update('event_date')}
                  />
                  {errors.event_date && <p className="error-message">{errors.event_date}</p>}
                </div>

                {/* Honeypot: hidden from people, bots fill it in */}
                <div className="absolute -left-[10000px] w-px h-px overflow-hidden" aria-hidden="true">
                  <label htmlFor="website">Website</label>
                  <input id="website" type="text" tabIndex={-1} autoComplete="off" value={form.website} onChange={update('website')} />
                </div>

                <button type="submit" disabled={submitting} className="w-full btn-primary py-3 text-lg disabled:opacity-50 disabled:cursor-not-allowed">
                  {submitting ? 'Sending…' : 'Send enquiry'}
                </button>
              </form>
            )}
          </div>

          <p className="text-center text-gray-600 mt-6">
            Prefer to chat?{' '}
            <a href={chatUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-[#128C7E] hover:underline">
              Message us on WhatsApp at {BUSINESS_WHATSAPP_DISPLAY}
            </a>
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-8 flex flex-col sm:flex-row gap-3 items-center justify-between text-sm text-gray-500">
          <p>© {new Date().getFullYear()} Invvite · Digital invitations</p>
          <a href={chatUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 hover:text-[#128C7E]">
            <WhatsAppIcon className="w-4 h-4" /> {BUSINESS_WHATSAPP_DISPLAY}
          </a>
        </div>
      </footer>

      {/* Floating WhatsApp button */}
      <a
        href={chatUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label="Chat with us on WhatsApp"
        className="fixed bottom-5 right-5 z-40 w-14 h-14 rounded-full bg-[#25D366] hover:bg-[#1ebe5b] text-white shadow-lg flex items-center justify-center"
      >
        <WhatsAppIcon className="w-7 h-7" />
      </a>
    </main>
  );
}
