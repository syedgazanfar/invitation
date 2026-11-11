import type { Metadata } from 'next';
import { LANDING_COPY, LOCALES, localePath, type Locale } from '@/lib/i18n';

/** Per-language <title>, description and hreflang alternates for the landing page. */
export function landingMetadata(locale: Locale): Metadata {
  const t = LANDING_COPY[locale];
  return {
    title: t.meta.title,
    description: t.meta.description,
    alternates: {
      canonical: localePath(locale),
      languages: {
        ...Object.fromEntries(LOCALES.map((l) => [l === 'en' ? 'en-IN' : `${l}-IN`, localePath(l)])),
        'x-default': '/',
      },
    },
    openGraph: { title: t.meta.title, description: t.meta.description, locale: `${locale}_IN`, type: 'website' },
  };
}
