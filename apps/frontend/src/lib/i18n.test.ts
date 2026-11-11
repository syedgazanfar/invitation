import { describe, expect, it } from 'vitest';
import { LANDING_COPY, LOCALES, localePath, type Locale } from './i18n';

/** Every leaf string in a nested copy object, keyed by its path. */
function leaves(value: unknown, path = ''): Array<[string, string]> {
  if (typeof value === 'string') return [[path, value]];
  if (Array.isArray(value)) return value.flatMap((v, i) => leaves(v, `${path}[${i}]`));
  if (value && typeof value === 'object') {
    return Object.entries(value).flatMap(([k, v]) => leaves(v, path ? `${path}.${k}` : k));
  }
  return [];
}

const DEVANAGARI = /[ऀ-ॿ]/;
// Strings that are legitimately identical in every language.
const SAME_IN_ALL = new Set(['nav.whatsapp', 'mockup.rsvp', 'mockup.bride', 'mockup.groom', 'langName']);

describe('landing page translations', () => {
  it('offers English, Hindi and Marathi', () => {
    expect(LOCALES).toEqual(['en', 'hi', 'mr']);
  });

  it.each(['hi', 'mr'] as Locale[])('%s has exactly the same keys as English, none empty', (locale) => {
    const en = leaves(LANDING_COPY.en);
    const other = leaves(LANDING_COPY[locale]);
    expect(other.map(([p]) => p)).toEqual(en.map(([p]) => p));
    for (const [path, text] of other) expect(text.trim(), path).not.toBe('');
  });

  it.each(['hi', 'mr'] as Locale[])('%s is actually translated (Devanagari text, not copied English)', (locale) => {
    const en = new Map(leaves(LANDING_COPY.en));
    const untranslated = leaves(LANDING_COPY[locale])
      .filter(([path]) => !SAME_IN_ALL.has(path))
      .filter(([path, text]) => text === en.get(path) || !DEVANAGARI.test(text))
      .map(([path]) => path);
    expect(untranslated).toEqual([]);
  });

  it('Hindi and Marathi are different languages, not the same text twice', () => {
    expect(LANDING_COPY.hi.hero.body).not.toBe(LANDING_COPY.mr.hero.body);
    expect(LANDING_COPY.hi.enquiry.submit).not.toBe(LANDING_COPY.mr.enquiry.submit);
  });

  it('maps each language to its own URL', () => {
    expect(localePath('en')).toBe('/');
    expect(localePath('hi')).toBe('/hi');
    expect(localePath('mr')).toBe('/mr');
  });
});
