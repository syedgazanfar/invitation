'use client';

/**
 * Public enquiry form.
 *
 * POSTs to /api/v1/enquiries/. The backend stores the enquiry and notifies the
 * team (and the visitor) on WhatsApp through the WA-AKG gateway.
 */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
const ENQUIRY_URL = `${API_URL.replace(/\/$/, '')}/enquiries/`;

type EventOption = { value: string; label: string };

const DEFAULT_EVENT_TYPES: EventOption[] = [
  { value: 'WEDDING', label: 'Wedding' },
  { value: 'ENGAGEMENT', label: 'Engagement' },
  { value: 'BIRTHDAY', label: 'Birthday' },
  { value: 'PARTY', label: 'Party' },
  { value: 'RELIGIOUS', label: 'Religious / Festival' },
  { value: 'OTHER', label: 'Other' },
];

type FormState = {
  name: string;
  phone: string;
  email: string;
  event_type: string;
  event_date: string;
  message: string;
  website: string; // honeypot: must stay empty
};

type FieldErrors = Partial<Record<keyof FormState, string>>;

const EMPTY_FORM: FormState = {
  name: '',
  phone: '',
  email: '',
  event_type: 'WEDDING',
  event_date: '',
  message: '',
  website: '',
};

function todayISO() {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
}

export default function EnquiryPage() {
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [eventTypes, setEventTypes] = useState<EventOption[]>(DEFAULT_EVENT_TYPES);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [minDate, setMinDate] = useState('');

  useEffect(() => {
    setMinDate(todayISO());
    axios
      .get(ENQUIRY_URL)
      .then((res) => {
        const opts = res.data?.data?.event_types;
        if (Array.isArray(opts) && opts.length) setEventTypes(opts);
      })
      .catch(() => {
        /* keep defaults */
      });
  }, []);

  const update = (field: keyof FormState) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
      setForm((prev) => ({ ...prev, [field]: e.target.value }));
      if (fieldErrors[field]) setFieldErrors((prev) => ({ ...prev, [field]: undefined }));
    };

  const validate = () => {
    const errs: FieldErrors = {};
    if (form.name.trim().length < 2) errs.name = 'Please enter your name.';
    if (form.phone.replace(/\D/g, '').length < 10) errs.phone = 'Enter a valid WhatsApp number.';
    if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Enter a valid email.';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!validate()) return;

    setLoading(true);
    try {
      const res = await axios.post(ENQUIRY_URL, {
        ...form,
        event_date: form.event_date || null,
      });
      setSuccess(res.data?.message || "Thanks! We'll contact you on WhatsApp shortly.");
      setForm(EMPTY_FORM);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response) {
        if (err.response.status === 429) {
          setError('Too many enquiries from this device. Please try again later.');
        } else if (err.response.data?.errors) {
          const mapped: FieldErrors = {};
          Object.entries(err.response.data.errors as Record<string, string[] | string>).forEach(([k, v]) => {
            mapped[k as keyof FormState] = Array.isArray(v) ? v[0] : String(v);
          });
          setFieldErrors(mapped);
          setError(err.response.data.message || 'Please correct the errors below.');
        } else {
          setError('Something went wrong. Please try again.');
        }
      } else {
        setError('Could not send your enquiry. Please check your connection and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fieldClass = (field: keyof FormState) =>
    `input-field ${fieldErrors[field] ? 'border-red-400 focus:ring-red-400' : ''}`;

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 via-purple-50 to-blue-50 flex items-center justify-center px-4 py-12">
      <div className="max-w-lg w-full">
        {success ? (
          <div className="card text-center">
            <div className="text-5xl mb-4" aria-hidden="true">✅</div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Enquiry sent</h1>
            <p className="text-gray-600 mb-6">{success}</p>
            <div className="flex justify-center gap-3 flex-wrap">
              <button type="button" className="btn-secondary" onClick={() => setSuccess('')}>
                Send another
              </button>
              <Link href="/" className="btn-primary">
                Back to home
              </Link>
            </div>
          </div>
        ) : (
          <>
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Send us an enquiry</h1>
              <p className="text-gray-600">
                Tell us about your event and we&apos;ll reply on{' '}
                <span className="font-semibold text-[#128C7E]">WhatsApp</span>.
              </p>
            </div>

            <div className="card">
              <form onSubmit={handleSubmit} noValidate className="space-y-5">
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg" role="alert">
                    {error}
                  </div>
                )}

                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                    Your name *
                  </label>
                  <input
                    id="name"
                    type="text"
                    autoComplete="name"
                    required
                    className={fieldClass('name')}
                    value={form.name}
                    onChange={update('name')}
                  />
                  {fieldErrors.name && <p className="error-message">{fieldErrors.name}</p>}
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                    WhatsApp number *
                  </label>
                  <input
                    id="phone"
                    type="tel"
                    autoComplete="tel"
                    placeholder="+91 98765 43210"
                    required
                    className={fieldClass('phone')}
                    value={form.phone}
                    onChange={update('phone')}
                  />
                  {fieldErrors.phone ? (
                    <p className="error-message">{fieldErrors.phone}</p>
                  ) : (
                    <p className="text-gray-500 text-xs mt-1">We&apos;ll reply on this number.</p>
                  )}
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email <span className="text-gray-400 font-normal">(optional)</span>
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    className={fieldClass('email')}
                    value={form.email}
                    onChange={update('email')}
                  />
                  {fieldErrors.email && <p className="error-message">{fieldErrors.email}</p>}
                </div>

                <div className="grid sm:grid-cols-2 gap-5">
                  <div>
                    <label htmlFor="event_type" className="block text-sm font-medium text-gray-700 mb-2">
                      Event type
                    </label>
                    <select
                      id="event_type"
                      className={`${fieldClass('event_type')} bg-white`}
                      value={form.event_type}
                      onChange={update('event_type')}
                    >
                      {eventTypes.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    {fieldErrors.event_type && <p className="error-message">{fieldErrors.event_type}</p>}
                  </div>

                  <div>
                    <label htmlFor="event_date" className="block text-sm font-medium text-gray-700 mb-2">
                      Event date <span className="text-gray-400 font-normal">(optional)</span>
                    </label>
                    <input
                      id="event_date"
                      type="date"
                      min={minDate || undefined}
                      className={fieldClass('event_date')}
                      value={form.event_date}
                      onChange={update('event_date')}
                    />
                    {fieldErrors.event_date && <p className="error-message">{fieldErrors.event_date}</p>}
                  </div>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    rows={4}
                    maxLength={2000}
                    placeholder="Language, design style, number of guests, anything else…"
                    className={fieldClass('message')}
                    value={form.message}
                    onChange={update('message')}
                  />
                  {fieldErrors.message && <p className="error-message">{fieldErrors.message}</p>}
                </div>

                {/* Honeypot: hidden from people, bots fill it in */}
                <div className="absolute -left-[10000px] w-px h-px overflow-hidden" aria-hidden="true">
                  <label htmlFor="website">Website</label>
                  <input
                    id="website"
                    type="text"
                    tabIndex={-1}
                    autoComplete="off"
                    value={form.website}
                    onChange={update('website')}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary py-3 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sending…' : 'Send enquiry'}
                </button>
              </form>

              <div className="mt-6 text-center">
                <Link href="/" className="text-gray-500 hover:text-gray-700 text-sm">
                  Back to home
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
