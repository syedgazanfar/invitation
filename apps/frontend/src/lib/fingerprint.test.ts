import { describe, expect, it } from 'vitest';
import { getFingerprint } from './fingerprint';

describe('getFingerprint', () => {
  it('returns a non-empty fingerprint plus the components the backend accepts', async () => {
    const fp = await getFingerprint();
    expect(fp.fingerprint).toMatch(/^[0-9a-f]{64}$/); // SHA-256 hex; Guest.device_fingerprint max_length=64
    expect(typeof fp.screen_resolution).toBe('string');
    expect(typeof fp.timezone_offset).toBe('string');
    expect(typeof fp.languages).toBe('string');
    expect(typeof fp.canvas_hash).toBe('string');
  });

  it('is stable for the same browser', async () => {
    const a = await getFingerprint();
    const b = await getFingerprint();
    expect(a.fingerprint).toBe(b.fingerprint);
  });

  it('changes when the browser environment changes', async () => {
    const before = await getFingerprint();
    const original = navigator.userAgent;
    Object.defineProperty(navigator, 'userAgent', { value: `${original} OtherBrowser/1.0`, configurable: true });
    try {
      const after = await getFingerprint();
      expect(after.fingerprint).not.toBe(before.fingerprint);
    } finally {
      Object.defineProperty(navigator, 'userAgent', { value: original, configurable: true });
    }
  });
});

describe('getFingerprint distinguishes identical devices', () => {
  it('gives two browsers with identical characteristics different fingerprints', async () => {
    localStorage.clear();
    const first = await getFingerprint();
    localStorage.clear(); // a second, identical phone has its own storage
    const second = await getFingerprint();
    expect(second.fingerprint).not.toBe(first.fingerprint);
  });
});
