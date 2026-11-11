import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import MockAdapter from 'axios-mock-adapter';
import { useAuthStore } from '@/store/authStore';
import {
  api,
  publicApi,
  apiErrorMessage,
  authAPI,
  userAPI,
  plansAPI,
  templatesAPI,
  eventsAPI,
  invitationsAPI,
  adminAPI,
} from './api';

type Method = 'get' | 'post' | 'patch';

let mock: MockAdapter;
let publicMock: MockAdapter;

beforeEach(() => {
  mock = new MockAdapter(api);
  publicMock = new MockAdapter(publicApi);
  mock.onAny().reply(200, { success: true, data: {} });
  publicMock.onAny().reply(200, { success: true, data: {} });
  localStorage.clear();
});

afterEach(() => {
  mock.restore();
  publicMock.restore();
});

function lastRequest(m: MockAdapter, method: Method) {
  const list = m.history[method];
  expect(list.length, `expected one ${method.toUpperCase()} request`).toBe(1);
  return list[0];
}

const bodyOf = (req: { data?: unknown }) =>
  req.data === undefined || req.data === null || req.data === '' ? undefined : JSON.parse(req.data as string);

describe('authenticated endpoints (base /api/v1)', () => {
  const cases: Array<[string, () => Promise<unknown>, Method, string, unknown, Record<string, unknown>?]> = [
    ['authAPI.register',
      () => authAPI.register({ phone: '+919876543210', username: 'ravi', password: 'p', password_confirm: 'p' }),
      'post', '/auth/register/', { phone: '+919876543210', username: 'ravi', password: 'p', password_confirm: 'p' }],
    ['authAPI.login', () => authAPI.login({ identifier: 'ravi', password: 'x' }),
      'post', '/auth/login/', { identifier: 'ravi', password: 'x' }],
    ['authAPI.logout', () => authAPI.logout('r1'), 'post', '/auth/logout/', { refresh: 'r1' }],
    ['userAPI.getProfile', () => userAPI.getProfile(), 'get', '/auth/profile/', undefined],
    ['userAPI.updateProfile', () => userAPI.updateProfile({ full_name: 'Ravi K' }),
      'patch', '/auth/profile/', { full_name: 'Ravi K' }],
    ['plansAPI.getAll', () => plansAPI.getAll(), 'get', '/plans/', undefined],
    ['templatesAPI.getByPlan(code)', () => templatesAPI.getByPlan('PREMIUM'),
      'get', '/plans/templates/by-plan/PREMIUM/', undefined],
    ['templatesAPI.getByPlan()', () => templatesAPI.getByPlan(), 'get', '/plans/templates/all', undefined],
    ['eventsAPI.getOrders', () => eventsAPI.getOrders(), 'get', '/invitations/orders/', undefined],
    ['eventsAPI.createOrder', () => eventsAPI.createOrder({ plan_code: 'BASIC', event_type: 'WEDDING', event_type_name: 'Wedding' }),
      'post', '/invitations/orders/create/', { plan_code: 'BASIC', event_type: 'WEDDING', event_type_name: 'Wedding' }],
    ['eventsAPI.update', () => eventsAPI.update('my-wedding', { event_venue: 'New Hall' }),
      'patch', '/invitations/my-wedding/update/', { event_venue: 'New Hall' }],
    ['eventsAPI.getAll', () => eventsAPI.getAll(), 'get', '/invitations/', undefined],
    ['eventsAPI.getOne', () => eventsAPI.getOne('my-wedding'), 'get', '/invitations/my-wedding/', undefined],
    ['eventsAPI.getStats', () => eventsAPI.getStats('my-wedding'), 'get', '/invitations/my-wedding/stats/', undefined],
    ['eventsAPI.getGuests', () => eventsAPI.getGuests('my-wedding', 2),
      'get', '/invitations/my-wedding/guests/', undefined, { page: 2 }],
    ['eventsAPI.exportGuestsCSV', () => eventsAPI.exportGuestsCSV('my-wedding'),
      'get', '/invitations/my-wedding/guests/export/', undefined],
    ['eventsAPI.createRazorpayOrder', () => eventsAPI.createRazorpayOrder('o1'),
      'post', '/invitations/orders/o1/payment/razorpay/create/', undefined],
    ['eventsAPI.verifyPayment',
      () => eventsAPI.verifyPayment({ razorpay_order_id: 'a', razorpay_payment_id: 'b', razorpay_signature: 'c' }),
      'post', '/invitations/payment/razorpay/verify/', { razorpay_order_id: 'a', razorpay_payment_id: 'b', razorpay_signature: 'c' }],
    ['adminAPI.getStats', () => adminAPI.getStats(), 'get', '/admin-dashboard/dashboard/', undefined],
    ['adminAPI.getUsers', () => adminAPI.getUsers({ search: 'ravi', status: 'pending' }),
      'get', '/admin-dashboard/users/', undefined, { search: 'ravi', status: 'pending' }],
    ['adminAPI.getPendingApprovals', () => adminAPI.getPendingApprovals(),
      'get', '/admin-dashboard/approvals/pending/', undefined],
    ['adminAPI.approveUser', () => adminAPI.approveUser('u1', { notes: 'paid via UPI' }),
      'post', '/admin-dashboard/users/u1/approve/', { notes: 'paid via UPI' }],
    ['adminAPI.rejectUser', () => adminAPI.rejectUser('u1', { reason: 'no payment', block_user: false }),
      'post', '/admin-dashboard/users/u1/reject/', { reason: 'no payment', block_user: false }],
  ];

  it.each(cases)('%s hits the right endpoint', async (_name, call, method, url, body, params) => {
    await call();
    const req = lastRequest(mock, method);
    expect(req.url).toBe(url);
    expect(bodyOf(req)).toEqual(body);
    if (params) expect(req.params).toEqual(params);
    expect(publicMock.history[method]).toHaveLength(0);
  });

  it('exportGuestsCSV asks for a blob', async () => {
    await eventsAPI.exportGuestsCSV('my-wedding');
    expect(lastRequest(mock, 'get').responseType).toBe('blob');
  });

  it('sends the stored access token', async () => {
    localStorage.setItem('accessToken', 'tok123');
    await userAPI.getProfile();
    expect(lastRequest(mock, 'get').headers?.Authorization).toBe('Bearer tok123');
  });
});

describe('public invite endpoints (base /api, not /api/v1)', () => {
  const cases: Array<[string, () => Promise<unknown>, Method, string, unknown]> = [
    ['invitationsAPI.get', () => invitationsAPI.get('abc'), 'get', '/invite/abc/', undefined],
    ['invitationsAPI.check', () => invitationsAPI.check('abc', { fingerprint: 'fp' }),
      'post', '/invite/abc/check/', { fingerprint: 'fp' }],
    ['invitationsAPI.register', () => invitationsAPI.register('abc', { name: 'Asha', fingerprint: 'fp', is_test: false }),
      'post', '/invite/abc/register/', { name: 'Asha', fingerprint: 'fp', is_test: false }],
    ['invitationsAPI.rsvp', () => invitationsAPI.rsvp('abc', { fingerprint: 'fp', attending: true }),
      'post', '/invite/abc/rsvp/', { fingerprint: 'fp', attending: true }],
  ];

  it.each(cases)('%s hits the right endpoint', async (_name, call, method, url, body) => {
    await call();
    const req = lastRequest(publicMock, method);
    expect(req.url).toBe(url);
    expect(bodyOf(req)).toEqual(body);
    expect(mock.history[method]).toHaveLength(0);
  });

  it('public base URL drops the /v1 suffix', async () => {
    await invitationsAPI.register('abc', { name: 'Asha', fingerprint: 'fp', is_test: false });
    const req = lastRequest(publicMock, 'post');
    expect(`${req.baseURL}${req.url}`).toBe('http://localhost:8000/api/invite/abc/register/');
  });

  it('never sends the auth token to guests endpoints', async () => {
    localStorage.setItem('accessToken', 'tok123');
    await invitationsAPI.get('abc');
    expect(lastRequest(publicMock, 'get').headers?.Authorization).toBeUndefined();
  });
});

describe('apiErrorMessage', () => {
  it('prefers the server message', () => {
    expect(apiErrorMessage({ response: { data: { message: 'Please wait for admin approval' } } }, 'x'))
      .toBe('Please wait for admin approval');
  });

  it('falls back to the first error in an envelope errors object', () => {
    expect(apiErrorMessage({ response: { data: { success: false, errors: { phone: ['Invalid phone'] } } } }, 'x'))
      .toBe('Invalid phone');
  });

  it('reads a plain DRF field-error body', () => {
    expect(apiErrorMessage({ response: { data: { phone: ['Phone already registered'] } } }, 'x'))
      .toBe('Phone already registered');
  });

  it('reads DRF detail', () => {
    expect(apiErrorMessage({ response: { data: { detail: 'Not found.' } } }, 'x')).toBe('Not found.');
  });

  it('uses the fallback for network errors', () => {
    expect(apiErrorMessage(new Error('Network Error'), 'Something went wrong')).toBe('Something went wrong');
  });
});

describe('token refresh', () => {
  it.each([
    ['enveloped', { success: true, data: { access: 'new-tok' } }],
    ['bare', { access: 'new-tok' }],
  ])('retries once with the refreshed token (%s response)', async (_kind, refreshBody) => {
    localStorage.setItem('accessToken', 'old-tok');
    localStorage.setItem('refreshToken', 'ref-tok');
    mock.reset();
    let calls = 0;
    mock.onGet('/auth/profile/').reply((config) => {
      calls += 1;
      return config.headers?.Authorization === 'Bearer new-tok' ? [200, { success: true }] : [401, {}];
    });
    mock.onPost('/auth/token/refresh/').reply(200, refreshBody);

    const res = await userAPI.getProfile();

    expect(res.status).toBe(200);
    expect(calls).toBe(2);
    expect(localStorage.getItem('accessToken')).toBe('new-tok');
    expect(bodyOf(mock.history.post[0])).toEqual({ refresh: 'ref-tok' });
  });
});

describe('auth endpoints never trigger a token refresh', () => {
  it('a wrong password on /auth/login/ rejects with the server message, without refreshing', async () => {
    localStorage.setItem('accessToken', 'dead');
    localStorage.setItem('refreshToken', 'dead-refresh');
    mock.reset();
    mock.onPost('/auth/login/').reply(401, { success: false, code: 'INVALID_CREDENTIALS', message: 'Invalid credentials' });
    mock.onPost('/auth/token/refresh/').reply(401, {});

    const err = await authAPI.login({ identifier: 'ravi', password: 'wrong' }).catch((e) => e);

    expect(apiErrorMessage(err, 'x')).toBe('Invalid credentials');
    expect(mock.history.post.map((r) => r.url)).toEqual(['/auth/login/']);
  });
});

describe('auth store stays in sync with token refresh', () => {
  const user = { id: 'u1', username: 'ravi', phone: '+919876543210', email: '', full_name: '', is_approved: true, is_phone_verified: false };

  it('logs the store out when the refresh token is rejected', async () => {
    useAuthStore.getState().setAuth(user, 'old-tok', 'ref-tok');
    mock.reset();
    mock.onGet('/auth/profile/').reply(401, {});
    mock.onPost('/auth/token/refresh/').reply(401, { success: false });

    await userAPI.getProfile().catch(() => undefined);

    expect(useAuthStore.getState().isAuthenticated).toBe(false);
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  it('stores the refreshed access token in the auth store too', async () => {
    useAuthStore.getState().setAuth(user, 'old-tok', 'ref-tok');
    mock.reset();
    mock.onGet('/auth/profile/').reply((config) =>
      config.headers?.Authorization === 'Bearer new-tok' ? [200, { success: true }] : [401, {}]);
    mock.onPost('/auth/token/refresh/').reply(200, { success: true, data: { access: 'new-tok' } });

    await userAPI.getProfile();

    expect(useAuthStore.getState().accessToken).toBe('new-tok');
  });
});

describe('invitation create uploads the banner as multipart', () => {
  it('sends FormData untouched (not converted to JSON by the client default header)', async () => {
    const fd = new FormData();
    fd.append('event_title', 'Asha & Ravi');
    fd.append('banner_image', new File(['x'], 'banner.jpg', { type: 'image/jpeg' }));

    await eventsAPI.create(fd);

    const req = lastRequest(mock, 'post');
    expect(req.url).toBe('/invitations/create/');
    expect(req.data).toBeInstanceOf(FormData);
    expect((req.data as FormData).get('banner_image')).toBeInstanceOf(File);
  });
});
