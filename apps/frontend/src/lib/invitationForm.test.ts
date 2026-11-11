import { describe, expect, it } from 'vitest';
import { BANNER_MAX_BYTES, bannerError, invitationFormData } from './invitationForm';

const input = {
  order_id: 'o1',
  template_id: 't1',
  event_title: 'Asha & Ravi',
  event_date: '2027-02-14T12:30:00.000Z',
  event_venue: 'Taj Krishna',
  host_name: 'Sharma Family',
  event_address: '',
  custom_message: 'Join us',
};

describe('invitationFormData', () => {
  it('includes the banner file and every non-empty field', () => {
    const banner = new File(['x'], 'banner.jpg', { type: 'image/jpeg' });
    const fd = invitationFormData(input, banner);
    expect(fd.get('banner_image')).toBe(banner);
    expect(fd.get('order_id')).toBe('o1');
    expect(fd.get('template_id')).toBe('t1');
    expect(fd.get('event_date')).toBe('2027-02-14T12:30:00.000Z');
    expect(fd.get('custom_message')).toBe('Join us');
  });

  it('leaves out empty optional fields', () => {
    const fd = invitationFormData(input, new File(['x'], 'b.png', { type: 'image/png' }));
    expect(fd.has('event_address')).toBe(false);
  });
});

describe('bannerError', () => {
  it('requires a banner (Django Invitation.banner_image is mandatory)', () => {
    expect(bannerError(null)).toMatch(/banner/i);
  });

  it('accepts jpg, jpeg, png and webp only (model FileExtensionValidator)', () => {
    expect(bannerError(new File(['x'], 'a.JPG', { type: 'image/jpeg' }))).toBeNull();
    expect(bannerError(new File(['x'], 'a.webp', { type: 'image/webp' }))).toBeNull();
    expect(bannerError(new File(['x'], 'a.gif', { type: 'image/gif' }))).toMatch(/jpg|png|webp/i);
  });

  it('rejects files over the upload limit before sending', () => {
    const big = new File([new Uint8Array(BANNER_MAX_BYTES + 1)], 'big.jpg', { type: 'image/jpeg' });
    expect(bannerError(big)).toMatch(/MB/);
  });
});
