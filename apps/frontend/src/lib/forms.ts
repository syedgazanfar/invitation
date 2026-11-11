/** Form helpers shared by pages that post to Django. */

/**
 * Clean a phone number for Django: convert Devanagari digits (typed on Hindi /
 * Marathi keyboards) to ASCII, then remove spaces, dashes and brackets.
 * Django's phone_regex only accepts ASCII digits with an optional leading +.
 */
export function normalizePhone(value: string): string {
  return value
    .replace(/[०-९]/g, (d) => String(d.charCodeAt(0) - 0x0966))
    .replace(/[\s\-()]/g, '');
}

/** PATCH /auth/profile/ body: trimmed, with a blank email omitted (Django rejects "" for the unique email field). */
export function profileUpdatePayload(form: { full_name: string; email: string }): { full_name: string; email?: string } {
  const payload: { full_name: string; email?: string } = { full_name: form.full_name.trim() };
  const email = form.email.trim();
  if (email) payload.email = email;
  return payload;
}
