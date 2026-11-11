import { describe, expect, it } from 'vitest';
import { normalizePhone, profileUpdatePayload } from './forms';

describe('normalizePhone', () => {
  it('strips spaces, dashes and brackets so Django phone_regex accepts the shown format', () => {
    expect(normalizePhone('+91 98765 43210')).toBe('+919876543210');
    expect(normalizePhone(' 98765-43210 ')).toBe('9876543210');
    expect(normalizePhone('(+91) 98765 43210')).toBe('+919876543210');
  });
});

describe('profileUpdatePayload', () => {
  it('omits a blank email (Django rejects an empty string for a unique email field)', () => {
    expect(profileUpdatePayload({ full_name: ' Ravi ', email: '  ' })).toEqual({ full_name: 'Ravi' });
  });

  it('keeps a filled email, trimmed', () => {
    expect(profileUpdatePayload({ full_name: 'Ravi', email: ' r@x.com ' })).toEqual({ full_name: 'Ravi', email: 'r@x.com' });
  });
});

describe('normalizePhone with Indian-language keyboards', () => {
  it('converts Devanagari digits (Hindi/Marathi keyboards) to ASCII', () => {
    expect(normalizePhone('+९१ ९८७६५ ४३२१०')).toBe('+919876543210');
    expect(normalizePhone('९८७६५-४३२१०')).toBe('9876543210');
  });

  it('keeps a leading 0 for the backend to interpret (098765 43210)', () => {
    expect(normalizePhone('098765 43210')).toBe('09876543210');
  });
});
