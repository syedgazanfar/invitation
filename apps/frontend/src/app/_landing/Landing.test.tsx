/**
 * The landing page, driven the way real visitors use it.
 * Each `describe` is one way a real user breaks the enquiry flow.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AxiosError, AxiosHeaders } from 'axios';
import { LANDING_COPY, type Locale } from '@/lib/i18n';

const submit = vi.fn();
const track = vi.fn();
vi.mock('@/lib/api', () => ({
  enquiriesAPI: { submit: (...args: unknown[]) => submit(...args) },
  apiErrorMessage: (_e: unknown, fallback: string) => fallback,
}));
vi.mock('@/lib/analytics', () => ({ trackEnquirySubmitted: (...args: unknown[]) => track(...args) }));

import Landing from './Landing';

const ok = () => ({ data: { success: true, message: 'ok', data: { id: 'e1' } } });

function httpError(status: number, data: unknown) {
  const config = { headers: new AxiosHeaders() };
  return new AxiosError('Request failed', 'ERR_BAD_REQUEST', config, {}, { status, statusText: '', headers: {}, config, data });
}

function setup(locale: Locale = 'en') {
  const user = userEvent.setup();
  render(<Landing locale={locale} />);
  const t = LANDING_COPY[locale];
  const form = screen.getByRole('button', { name: t.enquiry.submit }).closest('form')!;
  const ui = within(form);
  return {
    user,
    t,
    name: ui.getByLabelText(t.enquiry.nameLabel) as HTMLInputElement,
    phone: ui.getByLabelText(t.enquiry.phoneLabel) as HTMLInputElement,
    date: ui.getByLabelText(new RegExp(t.enquiry.dateLabel)) as HTMLInputElement,
    button: () => screen.queryByRole('button', { name: new RegExp(`${t.enquiry.submit}|${t.enquiry.sending}`) }) as HTMLButtonElement,
    form,
  };
}

beforeEach(() => {
  submit.mockReset();
  track.mockReset();
});

describe('Break #1: impatient double-tap on "Send enquiry" over a slow connection', () => {
  it('sends exactly one enquiry and fires one conversion event', async () => {
    let resolve!: (v: unknown) => void;
    submit.mockImplementation(() => new Promise((r) => (resolve = r)));
    const { user, t, name, phone, button } = setup();

    await user.type(name, 'Asha Patil');
    await user.type(phone, '9876543210');
    await user.dblClick(button());
    await user.click(button()); // and once more for good measure

    expect(submit).toHaveBeenCalledTimes(1);
    resolve(ok());
    expect(await screen.findByText(t.enquiry.thanksTitle)).toBeTruthy();
    expect(track).toHaveBeenCalledTimes(1);
  });
});

describe('Break #2: phone number typed on a Hindi/Marathi keyboard or with formatting', () => {
  it('accepts Devanagari digits and sends a clean +91 number', async () => {
    submit.mockResolvedValue(ok());
    const { user, name, phone, button } = setup('hi');

    await user.type(name, 'राहुल शर्मा');
    await user.type(phone, '+९१ ९८७६५ ४३२१०');
    await user.click(button());

    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1));
    expect(submit.mock.calls[0][0]).toMatchObject({ name: 'राहुल शर्मा', phone: '+919876543210' });
  });

  it('shows the phone error in the page language for a too-short number, without calling the server', async () => {
    const { user, t, name, phone, button } = setup('mr');
    await user.type(name, 'प्रिया');
    await user.type(phone, '९८७६५');
    await user.click(button());

    expect(await screen.findByText(t.errors.phone)).toBeTruthy();
    expect(submit).not.toHaveBeenCalled();
  });
});

describe('Break #3: browser autofill fills the hidden anti-spam field', () => {
  it('the trap field gives autofill nothing to recognise', () => {
    const { form } = setup();
    const trap = form.querySelector('input[tabindex="-1"]') as HTMLInputElement;
    expect(trap).toBeTruthy();
    const label = trap.id ? form.querySelector(`label[for="${trap.id}"]`)?.textContent ?? '' : '';
    const signals = [trap.id, trap.name, trap.getAttribute('autocomplete') ?? '', label, trap.type].join(' ');
    expect(signals).not.toMatch(/web|site|url|mail|name|phone|tel|address|company|org|city|zip/i);
    expect(trap.getAttribute('autocomplete')).toBe('off');
  });

  it('a normal visitor’s enquiry is sent with an empty trap value', async () => {
    submit.mockResolvedValue(ok());
    const { user, name, phone, button } = setup();
    await user.type(name, 'Asha');
    await user.type(phone, '9876543210');
    await user.click(button());
    await waitFor(() => expect(submit).toHaveBeenCalledTimes(1));
    expect(submit.mock.calls[0][0].website).toBe('');
  });
});

describe('Break #4: mobile data drops while sending', () => {
  it('explains the problem, keeps what they typed, and lets them retry', async () => {
    submit.mockRejectedValueOnce(new AxiosError('Network Error', 'ERR_NETWORK')).mockResolvedValueOnce(ok());
    const { user, t, name, phone, button } = setup('mr');

    await user.type(name, 'सुनील');
    await user.type(phone, '9876543210');
    await user.click(button());

    expect(await screen.findByText(t.errors.network)).toBeTruthy();
    expect(name.value).toBe('सुनील');
    expect(phone.value).toBe('9876543210');
    expect(button().disabled).toBe(false);

    await user.click(button());
    expect(await screen.findByText(t.enquiry.thanksTitle)).toBeTruthy();
    expect(submit).toHaveBeenCalledTimes(2);
  });

  it('says "use WhatsApp instead" when the hourly enquiry limit is hit (HTTP 429)', async () => {
    submit.mockRejectedValue(httpError(429, { detail: 'Request was throttled.' }));
    const { user, t, name, phone, button } = setup('hi');
    await user.type(name, 'Asha');
    await user.type(phone, '9876543210');
    await user.click(button());
    expect(await screen.findByText(t.errors.tooMany)).toBeTruthy();
  });
});

describe('Break #5: input the server rejects (past date typed by hand, very long name)', () => {
  it('shows the past-date error next to the date field, in the page language', async () => {
    submit.mockRejectedValue(httpError(400, { success: false, errors: { event_date: ['Event date cannot be in the past.'] } }));
    const { user, t, name, phone, date, button } = setup('hi');

    await user.type(name, 'Asha');
    await user.type(phone, '9876543210');
    await user.type(date, '2020-01-01'); // typing bypasses the date picker's min
    await user.click(button());

    const msg = await screen.findByText(t.errors.datePast);
    expect(date.closest('div')!.contains(msg)).toBe(true);
  });

  it('stops a name longer than the server allows (120 characters) at the input', async () => {
    const { user, name } = setup();
    await user.type(name, 'A'.repeat(130));
    expect(name.value.length).toBe(120);
  });
});

describe('Three languages', () => {
  it.each(['en', 'hi', 'mr'] as Locale[])('%s: headline, form labels and WhatsApp message are in that language', (locale) => {
    const { t } = setup(locale);
    expect(screen.getByRole('heading', { level: 1 }).textContent).toContain(t.hero.titleEm);
    const chat = screen.getAllByRole('link', { name: new RegExp(t.hero.ctaWhatsapp) })[0] as HTMLAnchorElement;
    expect(decodeURIComponent(chat.href)).toContain(t.whatsappMessage);
    expect(chat.href).toContain('wa.me/919923928181');
  });

  it('sets the document language so screen readers and Google read it correctly', () => {
    setup('mr');
    expect(document.documentElement.lang).toBe('mr');
  });

  it('language switcher links to every version and marks the current one', () => {
    setup('hi');
    const nav = screen.getByRole('navigation', { name: /language|भाषा/i });
    const links = within(nav).getAllByRole('link') as HTMLAnchorElement[];
    expect(links.map((a) => a.getAttribute('href'))).toEqual(['/', '/hi', '/mr']);
    expect(links.map((a) => a.textContent)).toEqual(['English', 'हिंदी', 'मराठी']);
    expect(links[1].getAttribute('aria-current')).toBe('page');
  });
});
