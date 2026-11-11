'use client';

/**
 * Public landing page: services, process, a short enquiry
 * form (name, WhatsApp number, event date) and "Chat on WhatsApp".
 * Visual language: ivory paper, deep maroon, muted gold, serif display type.
 */
import { useEffect, useState } from 'react';
import axios from 'axios';
import { enquiriesAPI, apiErrorMessage } from '@/lib/api';
import {
  BUSINESS_WHATSAPP_DISPLAY,
  landingEnquiryErrors,
  landingEnquiryPayload,
  whatsappChatUrl,
  type LandingEnquiryErrors,
  type LandingEnquiryForm,
} from '@/lib/landing';

/* ------------------------------------------------------------------ content */

const OCCASIONS = [
  { title: 'Weddings', text: 'Haldi, mehendi, sangeet and the big day, in one invitation or a set.' },
  { title: 'Engagement & Roka', text: 'Share the announcement with family near and far.' },
  { title: 'Birthdays', text: 'First birthdays, milestone birthdays and surprise parties.' },
  { title: 'Festivals & Pujas', text: 'Diwali, Eid, griha pravesh, naamkaran and satyanarayan puja.' },
  { title: 'Anniversaries', text: 'Silver and golden jubilees, renewals of vows.' },
  { title: 'Corporate & Social', text: 'Launches, annual days and community gatherings.' },
];

const INCLUDED = [
  { title: 'Opens from WhatsApp', text: 'One link, no app to download. Works on any phone.' },
  { title: 'Personal welcome', text: 'Each guest is greeted by name when they open it.' },
  { title: 'Venue & directions', text: 'Address and a one-tap Google Maps link.' },
  { title: 'RSVP tracking', text: 'See who opened the invitation and who is attending.' },
  { title: 'Your photos & message', text: 'A banner photo, gallery and a note in your own words.' },
  { title: 'Guest list export', text: 'Download everyone who responded as a spreadsheet.' },
];

const STEPS = [
  { title: 'Tell us about your event', text: 'Fill in the short form or message us on WhatsApp with the date and occasion.' },
  { title: 'We design it with you', text: 'Choose a design; we add names, venue, photos and your message, and refine it with you.' },
  { title: 'Share one link', text: 'Send the link to your guests on WhatsApp and watch the RSVPs come in.' },
];

const FAQS = [
  {
    q: 'How do my guests receive the invitation?',
    a: 'You get a single link. Share it on WhatsApp, SMS, email or social media. Guests open it in their phone browser; nothing to install.',
  },
  {
    q: 'Can I see who has opened it?',
    a: 'Yes. Your dashboard shows each guest who opened the invitation, their RSVP, and lets you export the list.',
  },
  {
    q: 'How long does the link stay active?',
    a: 'Your link is active for 15 days from the day it goes live. If you need it for longer, tell us when you enquire.',
  },
  {
    q: 'Can you match our wedding colours or theme?',
    a: 'Yes. Share your colours, card design or inspiration on WhatsApp and we will tailor the invitation to it.',
  },
  {
    q: 'Can I make changes after it is shared?',
    a: 'Details like the venue, time and message can be updated, and guests always see the latest version on the same link.',
  },
];

const EMPTY: LandingEnquiryForm = { name: '', phone: '', event_date: '', website: '' };

/* -------------------------------------------------------------------- icons */

function WhatsAppIcon({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden="true">
      <path d="M17.47 14.38c-.3-.15-1.75-.86-2.02-.96-.27-.1-.47-.15-.67.15-.2.3-.77.96-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.25-.46-2.38-1.47-.88-.79-1.47-1.76-1.65-2.06-.17-.3-.02-.46.13-.6.14-.14.3-.35.45-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.61-.92-2.2-.24-.58-.49-.5-.67-.51h-.57c-.2 0-.52.07-.79.37-.27.3-1.04 1.02-1.04 2.48s1.06 2.88 1.21 3.08c.15.2 2.1 3.2 5.08 4.48.71.31 1.26.49 1.69.63.71.22 1.36.19 1.87.12.57-.09 1.75-.72 2-1.41.25-.7.25-1.29.17-1.41-.07-.13-.27-.2-.57-.35zM12.04 21.8h-.01a9.8 9.8 0 0 1-5-1.37l-.36-.21-3.72.97 1-3.62-.24-.37a9.78 9.78 0 0 1-1.5-5.22c0-5.41 4.41-9.81 9.84-9.81a9.78 9.78 0 0 1 9.83 9.82c0 5.41-4.41 9.81-9.84 9.81zm8.37-18.18A11.76 11.76 0 0 0 12.04.18C5.52.18.21 5.48.2 12c0 2.09.55 4.12 1.59 5.92L.1 24l6.23-1.63a11.8 11.8 0 0 0 5.71 1.46h.01c6.52 0 11.83-5.3 11.84-11.83a11.76 11.76 0 0 0-3.48-8.38z" />
    </svg>
  );
}

function Check({ className = 'w-4 h-4' }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" className={className} fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
      <path d="M4 10.5l3.5 3.5L16 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/** Thin gold divider with a small diamond, used under section headings. */
function Ornament({ className = '' }: { className?: string }) {
  return (
    <div className={`flex items-center gap-3 text-gold-500 ${className}`} aria-hidden="true">
      <span className="h-px w-10 bg-current opacity-60" />
      <svg viewBox="0 0 12 12" className="w-2.5 h-2.5" fill="currentColor">
        <path d="M6 0l6 6-6 6-6-6z" />
      </svg>
      <span className="h-px w-10 bg-current opacity-60" />
    </div>
  );
}

function SectionHeading({ eyebrow, title, intro, light = false }: { eyebrow: string; title: string; intro?: string; light?: boolean }) {
  return (
    <div className="max-w-2xl">
      <p className={`text-xs font-semibold tracking-[0.25em] uppercase mb-4 ${light ? 'text-gold-300' : 'text-gold-600'}`}>{eyebrow}</p>
      <h2 className={`font-serif text-4xl md:text-5xl leading-[1.08] font-medium ${light ? 'text-ivory' : 'text-ink'}`}>{title}</h2>
      {intro && <p className={`mt-5 text-lg leading-relaxed ${light ? 'text-ivory/75' : 'text-ink-muted'}`}>{intro}</p>}
    </div>
  );
}

/* ------------------------------------------------- hero invitation mockup */

function InvitationMockup() {
  return (
    <div className="relative mx-auto w-[270px] sm:w-[300px]">
      {/* paper card behind the phone */}
      <div
        className="absolute -left-20 top-12 hidden sm:block w-56 h-72 rotate-[-8deg] rounded-sm bg-ivory-100 shadow-[0_20px_40px_-20px_rgba(58,15,24,0.35)] border border-gold-300/60"
        aria-hidden="true"
      >
        <div className="absolute inset-3 border border-gold-400/50" />
        {/* text runs vertically along the edge that stays visible beside the phone */}
        <div className="absolute inset-y-0 left-5 flex items-center">
          <p className="rotate-180 [writing-mode:vertical-rl] whitespace-nowrap">
            <span className="font-serif italic text-maroon-700 text-xl">Save the Date</span>
            <span className="mt-3 text-[10px] tracking-[0.3em] uppercase text-ink-muted"> · 14 · 02 · 2027</span>
          </p>
        </div>
      </div>

      {/* phone */}
      <div className="relative rounded-[2.6rem] bg-ink p-2.5 shadow-[0_40px_80px_-30px_rgba(58,15,24,0.6)]">
        <div className="absolute left-1/2 top-3 -translate-x-1/2 h-5 w-24 rounded-full bg-ink z-10" aria-hidden="true" />
        <div className="relative overflow-hidden rounded-[2.1rem] bg-maroon-800 aspect-[9/19]">
          {/* arch frame */}
          <div className="absolute inset-4 rounded-t-[999px] border border-gold-400/70" />
          <div className="absolute inset-6 rounded-t-[999px] border border-gold-400/30" />
          <div className="relative h-full flex flex-col items-center justify-center text-center px-8">
            <p className="text-[9px] tracking-[0.35em] uppercase text-gold-300">Together with their families</p>
            <p className="mt-5 font-serif text-[2.1rem] leading-none text-ivory">Ananya</p>
            <p className="my-1.5 font-serif italic text-gold-300 text-xl">&amp;</p>
            <p className="font-serif text-[2.1rem] leading-none text-ivory">Rohan</p>
            <Ornament className="mt-5 scale-75" />
            <p className="mt-4 text-[10px] tracking-[0.25em] uppercase text-ivory/80">Sunday, 14 February 2027</p>
            <p className="mt-1 text-[11px] text-ivory/70">The Leela Palace, Udaipur</p>
            <div className="mt-6 flex gap-2">
              <span className="rounded-full bg-gold-400 px-4 py-1.5 text-[10px] font-semibold tracking-wider uppercase text-maroon-900">RSVP</span>
              <span className="rounded-full border border-gold-400/70 px-4 py-1.5 text-[10px] font-semibold tracking-wider uppercase text-gold-300">Directions</span>
            </div>
            <p className="absolute bottom-6 text-[10px] text-ivory/50">Welcome, Priya</p>
          </div>
        </div>
      </div>

      {/* RSVP toast */}
      <div className="absolute -right-6 sm:-right-14 bottom-16 rounded-xl bg-white px-4 py-3 shadow-[0_15px_35px_-12px_rgba(35,28,25,0.35)] border border-ivory-200">
        <p className="text-[11px] text-ink-muted">New RSVP</p>
        <p className="text-sm font-semibold text-ink">Priya Sharma · Attending</p>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------------- page */

function todayISO() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
}

export default function LandingPage() {
  const [form, setForm] = useState<LandingEnquiryForm>(EMPTY);
  const [errors, setErrors] = useState<LandingEnquiryErrors>({});
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState('');
  const [minDate, setMinDate] = useState('');

  useEffect(() => {
    setMinDate(todayISO());
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
        setFormError('You have already sent a few enquiries. Please message us on WhatsApp instead.');
      } else {
        const fields = (axios.isAxiosError(err) ? err.response?.data?.errors : undefined) as Record<string, string[]> | undefined;
        if (fields) setErrors({ name: fields.name?.[0], phone: fields.phone?.[0], event_date: fields.event_date?.[0] });
        setFormError(apiErrorMessage(err, 'Could not send your enquiry. Please try again or message us on WhatsApp.'));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const chatUrl = whatsappChatUrl('Hi! I would like to know more about your digital invitations.');

  const inputClass = (bad?: string) =>
    `w-full rounded-lg border bg-white px-4 py-3 text-ink placeholder:text-ink-muted/60 focus:outline-none focus:ring-2 focus:ring-maroon-600/30 focus:border-maroon-600 transition ${
      bad ? 'border-red-400' : 'border-ivory-200'
    }`;

  return (
    <main className="min-h-screen overflow-x-clip bg-ivory text-ink antialiased">
      {/* ------------------------------------------------------------ header */}
      <header className="sticky top-0 z-30 border-b border-ivory-200/80 bg-ivory/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <a href="#top" className="font-serif text-2xl font-semibold tracking-tight text-maroon-700">
            Invvite<span className="text-gold-500">.</span>
          </a>
          <nav className="hidden md:flex items-center gap-8 text-sm text-ink-muted">
            <a href="#occasions" className="hover:text-maroon-700 transition">Occasions</a>
            <a href="#process" className="hover:text-maroon-700 transition">How it works</a>
            <a href="#faq" className="hover:text-maroon-700 transition">FAQ</a>
          </nav>
          <div className="flex items-center gap-2">
            <a
              href={chatUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:inline-flex items-center gap-2 rounded-full border border-ink/15 px-4 py-2 text-sm font-medium text-ink hover:border-maroon-700 hover:text-maroon-700 transition"
            >
              <WhatsAppIcon className="w-4 h-4 text-[#25D366]" /> WhatsApp
            </a>
            <a href="#enquire" className="rounded-full bg-maroon-700 px-5 py-2 text-sm font-semibold text-ivory hover:bg-maroon-800 transition">
              Enquire
            </a>
          </div>
        </div>
      </header>

      {/* -------------------------------------------------------------- hero */}
      <section id="top" className="relative overflow-hidden">
        <div className="mx-auto grid max-w-6xl items-center gap-16 px-5 pb-20 pt-14 md:pt-20 lg:grid-cols-[1.1fr_0.9fr] lg:pb-28">
          <div>
            <p className="text-xs font-semibold tracking-[0.25em] uppercase text-gold-600">Digital invitations · Designed in India</p>
            <h1 className="mt-6 font-serif text-5xl leading-[1.02] font-medium sm:text-6xl lg:text-7xl">
              Invitations worth <em className="text-maroon-700">opening.</em>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-muted">
              We design elegant digital invitations for weddings, engagements, birthdays and festivals. Your guests open
              them from a single WhatsApp link, are welcomed by name, and RSVP in a tap.
            </p>
            <div className="mt-10 flex flex-col gap-3 sm:flex-row">
              <a href="#enquire" className="inline-flex items-center justify-center rounded-full bg-maroon-700 px-8 py-4 font-semibold text-ivory shadow-[0_12px_30px_-12px_rgba(100,28,41,0.7)] hover:bg-maroon-800 transition">
                Plan my invitation
              </a>
              <a
                href={chatUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-full border border-ink/15 bg-white px-8 py-4 font-semibold text-ink hover:border-maroon-700 transition"
              >
                <WhatsAppIcon className="w-5 h-5 text-[#25D366]" /> Chat on WhatsApp
              </a>
            </div>
            <ul className="mt-10 flex flex-wrap gap-x-8 gap-y-3 text-sm text-ink-muted">
              {['Shared as one link', 'No app for guests', 'RSVPs in one place'].map((t) => (
                <li key={t} className="flex items-center gap-2">
                  <Check className="w-4 h-4 text-gold-500" /> {t}
                </li>
              ))}
            </ul>
          </div>
          <InvitationMockup />
        </div>
      </section>

      {/* --------------------------------------------------------- occasions */}
      <section id="occasions" className="border-t border-ivory-200 bg-white">
        <div className="mx-auto max-w-6xl px-5 py-20 md:py-28">
          <SectionHeading
            eyebrow="Occasions"
            title="For every celebration worth gathering for"
            intro="Each invitation is designed around your event and your family, not picked from a generic template."
          />
          <div className="mt-14 grid gap-px overflow-hidden rounded-2xl border border-ivory-200 bg-ivory-200 sm:grid-cols-2 lg:grid-cols-3">
            {OCCASIONS.map((o, i) => (
              <div key={o.title} className="group bg-white p-8 transition hover:bg-ivory">
                <p className="font-serif text-sm text-gold-500">{String(i + 1).padStart(2, '0')}</p>
                <h3 className="mt-3 font-serif text-2xl font-medium text-ink group-hover:text-maroon-700 transition">{o.title}</h3>
                <p className="mt-2 leading-relaxed text-ink-muted">{o.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- included */}
      <section className="bg-maroon-800 text-ivory">
        <div className="mx-auto grid max-w-6xl gap-14 px-5 py-20 md:py-28 lg:grid-cols-[0.9fr_1.1fr]">
          <SectionHeading
            light
            eyebrow="Every invitation includes"
            title="Thoughtful for you, effortless for your guests"
            intro="Guests feel personally invited. You know exactly who is coming."
          />
          <dl className="grid gap-x-10 gap-y-9 sm:grid-cols-2">
            {INCLUDED.map((f) => (
              <div key={f.title} className="border-t border-gold-400/30 pt-5">
                <dt className="flex items-center gap-2 font-medium text-ivory">
                  <Check className="w-4 h-4 text-gold-400" /> {f.title}
                </dt>
                <dd className="mt-2 leading-relaxed text-ivory/70">{f.text}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ----------------------------------------------------------- process */}
      <section id="process" className="mx-auto max-w-6xl px-5 py-20 md:py-28">
        <SectionHeading eyebrow="How it works" title="From first message to RSVPs" />
        <ol className="mt-14 grid gap-10 md:grid-cols-3">
          {STEPS.map((s, i) => (
            <li key={s.title} className="relative">
              <div className="flex items-center gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-gold-500 font-serif text-lg text-maroon-700">
                  {i + 1}
                </span>
                {i < STEPS.length - 1 && <span className="hidden h-px flex-1 bg-gold-400/50 md:block" aria-hidden="true" />}
              </div>
              <h3 className="mt-6 font-serif text-2xl font-medium">{s.title}</h3>
              <p className="mt-2 leading-relaxed text-ink-muted">{s.text}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* ----------------------------------------------------------- enquiry */}
      <section id="enquire" className="mx-auto max-w-6xl px-5 py-20 md:py-28">
        <div className="grid overflow-hidden rounded-3xl border border-ivory-200 bg-white shadow-[0_40px_80px_-50px_rgba(58,15,24,0.5)] lg:grid-cols-[0.9fr_1.1fr]">
          <div className="relative bg-maroon-800 p-10 text-ivory md:p-12">
            <div className="absolute inset-5 rounded-2xl border border-gold-400/25" aria-hidden="true" />
            <div className="relative">
              <p className="text-xs font-semibold tracking-[0.25em] uppercase text-gold-300">Enquire</p>
              <h2 className="mt-4 font-serif text-4xl md:text-5xl leading-[1.08] font-medium">Let&apos;s create your invitation</h2>
              <p className="mt-5 leading-relaxed text-ivory/75">
                Leave your name, WhatsApp number and event date. We&apos;ll message you on WhatsApp to understand your
                event and share designs.
              </p>
              <div className="mt-10 border-t border-gold-400/30 pt-8">
                <p className="text-sm text-ivory/60">Prefer to talk now?</p>
                <a
                  href={chatUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-3 inline-flex items-center gap-3 rounded-full bg-[#25D366] px-6 py-3 font-semibold text-white hover:bg-[#1ebe5b] transition"
                >
                  <WhatsAppIcon /> {BUSINESS_WHATSAPP_DISPLAY}
                </a>
              </div>
            </div>
          </div>

          <div className="p-8 md:p-12">
            {sent ? (
              <div className="flex h-full flex-col items-center justify-center py-10 text-center" role="status">
                <span className="flex h-14 w-14 items-center justify-center rounded-full border border-gold-500 text-maroon-700">
                  <Check className="w-6 h-6" />
                </span>
                <p className="mt-6 font-serif text-3xl">Thank you</p>
                <p className="mt-3 max-w-sm text-ink-muted">{sent}</p>
                <button type="button" onClick={() => setSent('')} className="mt-8 text-sm font-semibold text-maroon-700 underline underline-offset-4">
                  Send another enquiry
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} noValidate className="space-y-6">
                {formError && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">{formError}</div>
                )}

                <div>
                  <label htmlFor="name" className="mb-2 block text-sm font-medium text-ink">Your name</label>
                  <input id="name" type="text" autoComplete="name" required placeholder="Full name" className={inputClass(errors.name)} value={form.name} onChange={update('name')} />
                  {errors.name && <p className="mt-1.5 text-sm text-red-600">{errors.name}</p>}
                </div>

                <div>
                  <label htmlFor="phone" className="mb-2 block text-sm font-medium text-ink">WhatsApp number</label>
                  <input
                    id="phone"
                    type="tel"
                    inputMode="tel"
                    autoComplete="tel"
                    required
                    placeholder="+91 98765 43210"
                    className={inputClass(errors.phone)}
                    value={form.phone}
                    onChange={update('phone')}
                  />
                  {errors.phone ? (
                    <p className="mt-1.5 text-sm text-red-600">{errors.phone}</p>
                  ) : (
                    <p className="mt-1.5 text-xs text-ink-muted">We&apos;ll reply on this number.</p>
                  )}
                </div>

                <div>
                  <label htmlFor="event_date" className="mb-2 block text-sm font-medium text-ink">
                    Date of event <span className="font-normal text-ink-muted">(optional)</span>
                  </label>
                  <input id="event_date" type="date" min={minDate || undefined} className={inputClass(errors.event_date)} value={form.event_date} onChange={update('event_date')} />
                  {errors.event_date && <p className="mt-1.5 text-sm text-red-600">{errors.event_date}</p>}
                </div>

                {/* Honeypot: hidden from people, bots fill it in */}
                <div className="absolute -left-[10000px] h-px w-px overflow-hidden" aria-hidden="true">
                  <label htmlFor="website">Website</label>
                  <input id="website" type="text" tabIndex={-1} autoComplete="off" value={form.website} onChange={update('website')} />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full rounded-full bg-maroon-700 py-4 font-semibold text-ivory transition hover:bg-maroon-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {submitting ? 'Sending…' : 'Send enquiry'}
                </button>
                <p className="text-center text-xs text-ink-muted">We only use your number to reply to this enquiry.</p>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* --------------------------------------------------------------- faq */}
      <section id="faq" className="border-t border-ivory-200 bg-white">
        <div className="mx-auto grid max-w-6xl gap-12 px-5 py-20 md:py-28 lg:grid-cols-[0.8fr_1.2fr]">
          <SectionHeading eyebrow="FAQ" title="Questions, answered" />
          <div className="divide-y divide-ivory-200 border-y border-ivory-200">
            {FAQS.map((f) => (
              <details key={f.q} className="group py-6">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-6 font-serif text-xl font-medium text-ink">
                  {f.q}
                  <span className="text-2xl leading-none text-gold-500 transition group-open:rotate-45" aria-hidden="true">+</span>
                </summary>
                <p className="mt-3 max-w-2xl leading-relaxed text-ink-muted">{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------ footer */}
      <footer className="bg-maroon-900 text-ivory/70">
        <div className="mx-auto flex max-w-6xl flex-col gap-8 px-5 py-14 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="font-serif text-3xl font-semibold text-ivory">
              Invvite<span className="text-gold-400">.</span>
            </p>
            <p className="mt-3 max-w-sm text-sm leading-relaxed">Digital invitations for weddings, celebrations and festivals.</p>
          </div>
          <div className="text-sm md:text-right">
            <a href={chatUrl} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 text-ivory hover:text-gold-300 transition">
              <WhatsAppIcon className="w-4 h-4" /> {BUSINESS_WHATSAPP_DISPLAY}
            </a>
            <p className="mt-3">© {new Date().getFullYear()} Invvite. All rights reserved.</p>
          </div>
        </div>
      </footer>

      {/* -------------------------------------------------- floating WhatsApp */}
      <a
        href={chatUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Chat with us on WhatsApp at ${BUSINESS_WHATSAPP_DISPLAY}`}
        className="fixed bottom-5 right-5 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-[0_12px_30px_-8px_rgba(0,0,0,0.35)] transition hover:scale-105"
      >
        <WhatsAppIcon className="w-7 h-7" />
      </a>
    </main>
  );
}
