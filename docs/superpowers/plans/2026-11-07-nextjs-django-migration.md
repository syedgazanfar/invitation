# Next.js Frontend → Django API Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every page of the live Next.js frontend (`apps/frontend/src/app/`) work against the Django REST API, so `next build` passes and the app can be deployed with `docker-compose.prod.yml`.

**Architecture:** The frontend was written for the retired NestJS backend and only partly ported. We rewrite the API client (`src/lib/api.ts`) and the types (`src/lib/types.ts`) to match Django exactly, pin both with unit tests, then port each page to those types. No backend changes: features that have no Django endpoint are removed from the UI rather than invented.

**Tech Stack:** Next.js 14 App Router, React 18, TypeScript (strict), Tailwind, axios, zustand. New dev deps: `vitest`, `jsdom`, `axios-mock-adapter`.

**Spec:** No separate design doc. The decisions below, agreed in the session of 2026-11-07, are the spec.

### Decisions (the spec)

1. **Full migration**, done properly: pages use real Django endpoints and response shapes. Switching off the type check (`ignoreBuildErrors`) is not allowed.
2. **Signup is phone-based, matching Django as it is:** `phone`, `username`, `password`, `password_confirm`, with `email` and `full_name` optional. No OTP step in this plan.
3. **No backend changes.** Where the frontend calls something Django doesn't have, the UI is removed:
   - *Delete invitation* (dashboard list + detail): remove the buttons. Invitations are tied to paid, approved orders; deletion stays in Django admin. *(my call)*
   - *Toggle admin* (admin users page): remove it. Granting staff stays in Django admin. *(my call, security-sensitive)*
   - *Countries dropdown* (signup): remove it, since Django has no country field.
   - *Admin "All Events"* page: replace it with an **Approvals** page on `/admin-dashboard/approvals/pending/`, which is the Django admin workflow (approve/reject a user's plan). *(my call)*
4. Dashboard routes are keyed by **slug** (Django looks invitations up by slug): rename `dashboard/events/[id]` → `dashboard/events/[slug]`.

## Global Constraints

- Node **18+** locally (the Docker image uses `node:18-alpine`). On this Windows machine: `winget install OpenJS.NodeJS.LTS`, then `cd apps/frontend && npm install --legacy-peer-deps`.
- Authenticated API base: `process.env.NEXT_PUBLIC_API_URL`, default `http://localhost:8000/api/v1`.
- Public invite API base: the same URL with a trailing `/v1` removed (`…/api`), because Django mounts the guest endpoints at `/api/invite/` (`config/urls.py`).
- Django envelope: most custom views return `{ success, message?, data, errors? }`. Generic DRF list views (`/invitations/`, `/invitations/<slug>/guests/`, `/invitations/orders/`) return the paginated shape `{ count, next, previous, results }` without an envelope. Detail/update views return the raw object.
- Only new code goes in `src/app/` and `src/lib/`. Never import from the legacy `src/pages`, `src/components`, `src/hooks`, `src/services`, `src/types`, `src/utils` (null-loaded by `next.config.js`).
- Keep using the existing Tailwind classes: `card`, `btn-primary`, `btn-secondary`, `input-field`, `error-message`.
- **Never bypass the device fingerprint** on guest registration (`CLAUDE.md`): `fingerprint` is required by `POST /api/invite/<slug>/register/`.
- Done means: `npx tsc --noEmit`, `npm test` and `npm run build` all pass in `apps/frontend`.

## Review Focus

1. **Expired invite link** (`GET /api/invite/<slug>/` → 410) shows an "invitation expired" state, not a crash or blank page. Test in Task 6 (`inviteViewStateForError`).
2. **Guest limit reached** (`POST …/register/` → 403) shows the limit-reached state. Test in Task 6.
3. **Returning guest** (`already_registered: true` from `check/` or `register/`) skips the form and greets by `guest_name`, with no second registration. Test in Task 6 (`inviteViewStateForCheck`).
4. **Unapproved user creates an invitation:** Django rejects it and the page shows the server's `message`/field errors instead of "Something went wrong". Test in Task 1 (`apiErrorMessage`).
5. **Token refresh:** Django's refresh returns `{ data: { access } }` or `{ access }`. The interceptor must handle both and retry once, then redirect to `/login`. Test in Task 1.

## File Structure

| File | Responsibility |
|---|---|
| `apps/frontend/package.json` | add `test` script and vitest, jsdom, axios-mock-adapter dev deps |
| `apps/frontend/vitest.config.ts` | vitest config (jsdom, `@/` alias → `src/`) |
| `src/lib/api.ts` | **rewrite**: every Django endpoint the app uses, plus `apiErrorMessage()` |
| `src/lib/api.test.ts` | method/URL/body for every API function, error helper, refresh |
| `src/lib/types.ts` | **rewrite**: Django response types |
| `src/lib/fingerprint.ts` (+ `.test.ts`) | `getFingerprint()` ported from legacy `src/hooks/useFingerprint.ts` |
| `src/lib/invite.ts` (+ `.test.ts`) | pure view-state helpers for the public invite page |
| `src/store/authStore.ts` | use `User` from `@/lib/types` |
| `src/app/login`, `src/app/signup` | identifier login, phone signup |
| `src/app/dashboard/**` | list, layout, `[slug]` detail, `[slug]/edit`, new |
| `src/app/invite/[slug]/page.tsx` | public invitation flow |
| `src/app/admin/**` | layout, dashboard stats, users, approvals (replaces events) |

---

### Task 1: Test harness + Django API client

**Files:**
- Modify: `apps/frontend/package.json`
- Create: `apps/frontend/vitest.config.ts`
- Rewrite: `apps/frontend/src/lib/api.ts`
- Create: `apps/frontend/src/lib/api.test.ts`

**Interfaces:**
- Produces (all return the axios promise; callers read `res.data`):
  - `authAPI.register(d: RegisterInput)` → `POST /auth/register/`
  - `authAPI.login(d: { identifier: string; password: string })` → `POST /auth/login/`
  - `authAPI.logout(refresh: string)` → `POST /auth/logout/ {refresh}`
  - `userAPI.getProfile()` → `GET /auth/profile/`; `userAPI.updateProfile(d: { full_name?: string; email?: string })` → `PATCH /auth/profile/`
  - `plansAPI.getAll()` → `GET /plans/`; `templatesAPI.getByPlan(code?: string)` → `GET /plans/templates/by-plan/<code>/`, or `GET /plans/templates/all` when no code is given
  - `eventsAPI.createOrder({plan_code, event_type?})` → `POST /invitations/orders/create/`; `eventsAPI.create(d: InvitationCreateInput)` → `POST /invitations/create/`; `eventsAPI.update(slug, d: InvitationUpdateInput)` → `PATCH /invitations/<slug>/update/`; `eventsAPI.getAll()` → `GET /invitations/`; `eventsAPI.getOne(slug)` → `GET /invitations/<slug>/`; `eventsAPI.getStats(slug)` → `GET /invitations/<slug>/stats/`; `eventsAPI.getGuests(slug, page=1)` → `GET /invitations/<slug>/guests/?page=`; `eventsAPI.exportGuestsCSV(slug)` → `GET /invitations/<slug>/guests/export/` (blob); `createRazorpayOrder` / `verifyPayment` unchanged
  - `invitationsAPI` (public base `…/api`): `get(slug)` → `GET /invite/<slug>/`; `check(slug, {fingerprint})` → `POST /invite/<slug>/check/`; `register(slug, d: GuestRegisterInput)` → `POST /invite/<slug>/register/`; `rsvp(slug, {fingerprint, attending: boolean})` → `POST /invite/<slug>/rsvp/`
  - `adminAPI.getStats()` → `GET /admin-dashboard/dashboard/`; `adminAPI.getUsers(params?: { search?: string; status?: 'pending'|'approved'|'blocked' })` → `GET /admin-dashboard/users/`; `adminAPI.getPendingApprovals()` → `GET /admin-dashboard/approvals/pending/`; `adminAPI.approveUser(id, d?: { notes?: string })` → `POST /admin-dashboard/users/<id>/approve/`; `adminAPI.rejectUser(id, d: { reason: string; block_user?: boolean })` → `POST /admin-dashboard/users/<id>/reject/`
  - `apiErrorMessage(err: unknown, fallback: string): string`: first of `response.data.message`, the first field error in `response.data.errors` or a DRF field-error body (`{field: [msg]}`), `response.data.detail`, else `fallback`
  - Input types (`RegisterInput`, `InvitationCreateInput`, `InvitationUpdateInput`, `GuestRegisterInput`) are defined in Task 2's `types.ts`; in this task, declare them inline in `api.ts` and move them in Task 2.

- [ ] **Step 1: Install test deps and config.** Add devDependencies `vitest@^1.6.0`, `jsdom@^24.0.0`, `axios-mock-adapter@^1.22.0` and the script `"test": "vitest run"`. Create `vitest.config.ts` with `test.environment = 'jsdom'` and `resolve.alias['@'] = path.resolve(__dirname, 'src')`. Run `npm install --legacy-peer-deps`.

- [ ] **Step 2: Write the failing tests** in `src/lib/api.test.ts`, using `new MockAdapter(api)` plus a second adapter on the public client:

```ts
it.each([
  ['login', () => authAPI.login({ identifier: 'ravi', password: 'x' }), 'post', '/auth/login/', { identifier: 'ravi', password: 'x' }],
  ['register', () => authAPI.register({ phone: '+919876543210', username: 'ravi', password: 'p', password_confirm: 'p' }), 'post', '/auth/register/', { phone: '+919876543210', username: 'ravi', password: 'p', password_confirm: 'p' }],
  ['getStats', () => adminAPI.getStats(), 'get', '/admin-dashboard/dashboard/', undefined],
  ['approveUser', () => adminAPI.approveUser('u1'), 'post', '/admin-dashboard/users/u1/approve/', undefined],
  ['rejectUser', () => adminAPI.rejectUser('u1', { reason: 'no payment' }), 'post', '/admin-dashboard/users/u1/reject/', { reason: 'no payment' }],
  ['getOne', () => eventsAPI.getOne('my-wedding'), 'get', '/invitations/my-wedding/', undefined],
  ['getStats(slug)', () => eventsAPI.getStats('my-wedding'), 'get', '/invitations/my-wedding/stats/', undefined],
  // …one row for every function in the Interfaces list
])('%s hits the right endpoint', async (_n, call, method, url, body) => { /* assert history[method][0].url === url and JSON body */ });

it('public invite calls use /api, not /api/v1', async () => {
  await invitationsAPI.register('abc', { name: 'Asha', fingerprint: 'fp', is_test: false });
  expect(publicMock.history.post[0].baseURL + publicMock.history.post[0].url)
    .toBe('http://localhost:8000/api/invite/abc/register/');
});

it('apiErrorMessage prefers server message, then field errors, then fallback', () => {
  expect(apiErrorMessage({ response: { data: { message: 'Please wait for admin approval' } } }, 'x')).toBe('Please wait for admin approval');
  expect(apiErrorMessage({ response: { data: { phone: ['Phone already registered'] } } }, 'x')).toBe('Phone already registered');
  expect(apiErrorMessage(new Error('net'), 'Something went wrong')).toBe('Something went wrong');
});

it('refreshes once on 401 using data.access or access, then retries', async () => { /* 401 → refresh 200 {data:{access:'new'}} → retry carries 'Bearer new' */ });
```

- [ ] **Step 3: Run:** `npm test`. Expected: FAIL (missing functions / wrong URLs).
- [ ] **Step 4: Rewrite `src/lib/api.ts`** to the Interfaces list. Export `api` (auth client) and `publicApi` (no auth interceptor, base `API_URL.replace(/\/v1\/?$/, '')`). Keep the existing 401-refresh interceptor and its `data.access || access` handling.
- [ ] **Step 5: Run:** `npm test`. Expected: PASS.
- [ ] **Step 6: Commit:** `git commit -m "feat(frontend): Django API client with endpoint tests"`

### Task 2: Django response types + auth store

**Files:**
- Rewrite: `src/lib/types.ts`
- Modify: `src/store/authStore.ts` (import `User` from `@/lib/types`, delete its local interface)
- Modify: `src/lib/api.ts` (import input types from `types.ts`)

**Interfaces (field names copied from the Django serializers named in brackets):**
- `User` [`authentication/services._build_user_payload`]: `id, username, phone, email, full_name, is_approved, is_phone_verified, is_staff, is_superuser, current_plan: {code,name,price_inr} | null`
- `Profile` [`UserProfileSerializer`]: `id, phone, username, email, full_name, is_phone_verified, created_at, updated_at, active_orders_count, total_invitations`
- `Plan` [`PlanSerializer`]: `id, code, name, description, regular_links, test_links, price_inr, display_price, features, is_active, sort_order`
- `Template` [`TemplateListSerializer`]: `id, name, description, thumbnail: string|null, plan_code, category_name, animation_type, supports_gallery, supports_music, supports_video, is_premium, use_count`
- `InvitationListItem` [`InvitationListSerializer`]: `id, slug, event_title, event_date, template_name, template_thumbnail, order_status, is_active, is_expired, link_expires_at, total_views, unique_guests`
- `InvitationDetail` [`InvitationDetailSerializer`]: every field in that serializer's `fields`
- `InvitationStats` [`InvitationStatsSerializer`], `Guest` [`GuestSerializer`], `Paginated<T> = { count; next; previous; results: T[] }`, `ApiEnvelope<T> = { success: boolean; message?: string; data: T; errors?: Record<string,string[]> }`
- `PublicInvitation` [`PublicInvitationSerializer`] and `PublicInviteResponse = { invitation: PublicInvitation; can_register: boolean; remaining_links: number }`
- `GuestCheckResult = { already_registered: true; guest_name: string; viewed_at: string; message: string } | { already_registered: false; can_register: boolean; remaining_links: number }`
- `GuestRegisterResult = { already_registered: boolean; guest_name: string; total_guests: number; remaining_links?: number }`
- `AdminStats` [`DashboardStatsView`]: `{ users:{total,new_today,pending_approval}, orders:{total,pending_payment,pending_approval,approved,rejected}, invitations:{total,active,expired}, links:{total_granted,total_used,total_remaining}, notifications:{unread,total} }`
- `AdminUser` [`AllUsersListView.list`], `PendingApproval` [`PendingApprovalsView.get`]: copy each dict's keys
- Inputs: `RegisterInput`, `InvitationCreateInput` (`InvitationCreateSerializer.fields`), `InvitationUpdateInput` (`InvitationUpdateSerializer.fields`), `GuestRegisterInput` (`name, fingerprint` required; `phone, message, attending, is_test, screen_resolution, timezone_offset, languages, canvas_hash, session_id` optional)
- Delete the NestJS-only types (`Event`, `Payment`, `GuestStats`, `GuestAnalytics`, `InvitationMeta`, `InvitationData`).

- [ ] **Step 1: Write `types.ts` and update the store/api imports.**
- [ ] **Step 2: Run** `npx tsc --noEmit -p . 2>&1 | grep -c "error TS"`. Expected: errors only in `src/app/**` pages (later tasks fix those), none in `src/lib` or `src/store`. Run `npm test`: PASS.
- [ ] **Step 3: Commit:** `git commit -m "feat(frontend): Django response types"`

### Task 3: Login + signup

**Files:** Modify `src/app/login/page.tsx`, rewrite `src/app/signup/page.tsx`.

**Interfaces:** Consumes `authAPI.login`, `authAPI.register`, `apiErrorMessage`, `useAuthStore().setAuth(user, access, refresh)`.

- [ ] **Step 1: Login.** Rename the field to `identifier`, with the label "Username or phone" and `type="text"`. On success read `res.data.data.{user, access, refresh}`. Redirect to `/admin/dashboard` if `user.is_staff`, otherwise `/dashboard`. Show errors with `apiErrorMessage(err, 'Login failed')`.
- [ ] **Step 2: Signup.** Fields: phone* (`type="tel"`, placeholder `+91 98765 43210`), username*, full name, email, password*, confirm password*. Send `password_confirm`. Keep the existing client checks (passwords match, length ≥ 8). Map a 400 field-error body onto each field (DRF returns `{phone: [...], username: [...]}`). On 201 read `res.data.data.{user, access, refresh}`, then `setAuth` and go to `/dashboard`. Show `res.data.message` (the "wait for admin approval" note) on the dashboard via `?welcome=1`. Remove the countries code.
- [ ] **Step 3: Verify:** `npx tsc --noEmit` shows no errors in `src/app/login` or `src/app/signup`.
- [ ] **Step 4: Commit:** `git commit -m "feat(frontend): phone-based signup and identifier login against Django"`

### Task 4: Dashboard layout + invitation list

**Files:** Modify `src/app/dashboard/layout.tsx`, `src/app/dashboard/page.tsx`.

**Interfaces:** Consumes `eventsAPI.getAll(): Paginated<InvitationListItem>`, `authAPI.logout(refresh)`, `User.is_staff`.

- [ ] **Step 1: Layout.** Show the Admin link on `user?.is_staff`. Logout calls `authAPI.logout(refreshToken)` (ignore failures) and then `clearAuth()`.
- [ ] **Step 2: List page.** Render `res.data.results`: `event_title`, `event_date`, `template_name`/`template_thumbnail`, a status badge (`is_expired` → Expired, `is_active` → Active, otherwise `order_status`), `unique_guests`, `total_views`. Each card links to `/dashboard/events/${slug}`. Empty `results` → existing empty state with "Create invitation". If `?welcome=1`, show the approval-pending notice. Remove `handleDelete` and its button.
- [ ] **Step 3: Verify:** no `tsc` errors in these two files.
- [ ] **Step 4: Commit:** `git commit -m "feat(frontend): dashboard list on Django invitations"`

### Task 5: Invitation detail, edit, new

**Files:**
- Rename: `src/app/dashboard/events/[id]/` → `src/app/dashboard/events/[slug]/` (`git mv`)
- Modify: `[slug]/page.tsx`, `[slug]/edit/page.tsx`, `src/app/dashboard/events/new/page.tsx`

**Interfaces:** Consumes `eventsAPI.getOne/getStats/getGuests/exportGuestsCSV/update(slug, InvitationUpdateInput)`, `InvitationDetail`, `InvitationStats`, `Paginated<Guest>`, `Plan.display_price`, `Template.thumbnail`.

- [ ] **Step 1: Detail page** (`useParams().slug`). Overview tab shows the `InvitationDetail` fields plus `share_url` with a copy button, `link_expires_at`, and `remaining_regular_links`/`remaining_test_links`. The stats tab uses `InvitationStats` (`expires_in_days`, `is_link_valid`, link counts). The guests tab is a paginated `Guest` table (`name, phone, attending, device_type, browser, os, viewed_at`) with a CSV export (`guests-${slug}.csv`). Delete the analytics charts that need NestJS-only `GuestAnalytics` fields. Remove delete.
- [ ] **Step 2: Edit page.** Form over the `InvitationUpdateInput` fields, prefilled from `getOne(slug)`. Save with `update(slug, …)`, then route to `/dashboard/events/${slug}`. Show errors with `apiErrorMessage`.
- [ ] **Step 3: New page.** Use `plan.display_price` and `template.thumbnail` (types now have them). On success route to `/dashboard/events/${res.data.slug ?? res.data.data?.slug}`. Read `InvitationCreateView` to confirm which shape it returns and use only that one.
- [ ] **Step 4: Verify:** no `tsc` errors under `src/app/dashboard`. `grep -rn "events/\[id\]\|eventsAPI.delete" src/app` returns nothing.
- [ ] **Step 5: Commit:** `git commit -m "feat(frontend): invitation detail/edit/new on Django, keyed by slug"`

### Task 6: Public invitation page (guest flow)

**Files:**
- Create: `src/lib/fingerprint.ts`, `src/lib/fingerprint.test.ts`, `src/lib/invite.ts`, `src/lib/invite.test.ts`
- Modify: `src/app/invite/[slug]/page.tsx`

**Interfaces:**
- `getFingerprint(): Promise<{ fingerprint: string; screen_resolution: string; timezone_offset: string; languages: string; canvas_hash: string }>`: port of legacy `src/hooks/useFingerprint.ts` (same components and hash) as a plain async function, with no React hook.
- `type InviteViewState = 'loading' | 'form' | 'animation' | 'welcome-back' | 'limit-reached' | 'expired' | 'not-found' | 'error'`
- `inviteViewStateForError(status: number | undefined): InviteViewState`: 410 → `expired`, 404 → `not-found`, 403 → `limit-reached`, else `error`
- `inviteViewStateForCheck(r: GuestCheckResult): InviteViewState`: `already_registered` → `welcome-back`; `can_register === false` → `limit-reached`; else `form`

- [ ] **Step 1: Write failing tests:**

```ts
expect(inviteViewStateForError(410)).toBe('expired');
expect(inviteViewStateForError(404)).toBe('not-found');
expect(inviteViewStateForError(403)).toBe('limit-reached');
expect(inviteViewStateForError(undefined)).toBe('error');
expect(inviteViewStateForCheck({ already_registered: true, guest_name: 'Asha', viewed_at: '', message: '' })).toBe('welcome-back');
expect(inviteViewStateForCheck({ already_registered: false, can_register: false, remaining_links: 0 })).toBe('limit-reached');
expect(inviteViewStateForCheck({ already_registered: false, can_register: true, remaining_links: 3 })).toBe('form');
// fingerprint: same environment → same value twice; value is a non-empty string
const a = await getFingerprint(); const b = await getFingerprint();
expect(a.fingerprint).toBeTruthy(); expect(a.fingerprint).toBe(b.fingerprint);
```

- [ ] **Step 2: Run** `npm test`. Expected: FAIL.
- [ ] **Step 3: Implement** `fingerprint.ts` and `invite.ts`.
- [ ] **Step 4: Run** `npm test`. Expected: PASS.
- [ ] **Step 5: Page.** On load: `invitationsAPI.get(slug)`, plus `getFingerprint()` → `invitationsAPI.check(slug, {fingerprint})`, and set the state with `inviteViewStateForCheck`. On HTTP error use `inviteViewStateForError(err.response?.status)`. Render the invitation from `PublicInvitation` (`event_title, event_date, event_venue, event_address, event_map_link, host_name, custom_message, banner_image, gallery_images, background_music`; theme from `template_theme`). Submit: `invitationsAPI.register(slug, { name, ...fingerprintParts, is_test })`, where `is_test` comes from a `?test=1` query param. Then `animation`, or `welcome-back` if `already_registered`. The RSVP buttons call `rsvp(slug, {fingerprint, attending})`. Keep the existing gsap animation.
- [ ] **Step 6: Verify:** no `tsc` errors in the page.
- [ ] **Step 7: Commit:** `git commit -m "feat(frontend): guest invitation flow on Django public API with fingerprint"`

### Task 7: Admin area

**Files:**
- Modify: `src/app/admin/layout.tsx`, `src/app/admin/dashboard/page.tsx`, `src/app/admin/users/page.tsx`
- Delete: `src/app/admin/events/page.tsx`; Create: `src/app/admin/approvals/page.tsx`

**Interfaces:** Consumes `adminAPI.getStats(): ApiEnvelope<AdminStats>`, `getUsers(): ApiEnvelope<AdminUser[]>`, `getPendingApprovals(): ApiEnvelope<PendingApproval[]>`, `approveUser`, `rejectUser`.

- [ ] **Step 1: Layout.** If not authenticated → `/login`. If authenticated but not `user.is_staff` → `/dashboard`. Logout as in Task 4. Nav: Dashboard, Users, Approvals.
- [ ] **Step 2: Dashboard.** Stat cards from `AdminStats`: users (total, new today, pending approval), orders by status, invitations (active/expired), links (granted/used/remaining). Link "pending approval" to `/admin/approvals`.
- [ ] **Step 3: Users.** Search box → `getUsers({search})`, a status filter (All/Pending/Approved/Blocked) → `getUsers({status})`, and a table of `username, full_name, phone, email, current_plan.name, is_approved, is_blocked, created_at, last_login`. No toggle-admin.
- [ ] **Step 4: Approvals.** List `PendingApproval` rows: user, plan (`name`, `price_inr`, links) and latest order (`order_number, status, payment_amount, payment_method`). Approve → `approveUser(id, {notes})`. Reject opens an inline form with a required reason and a "Block user" checkbox (default on, matching Django's default) → `rejectUser`. Remove the row on success, and show `apiErrorMessage` on failure.
- [ ] **Step 5: Verify:** `npx tsc --noEmit -p .` → **0 errors**. `npm test` → PASS.
- [ ] **Step 6: Commit:** `git commit -m "feat(frontend): admin dashboard, users and approvals on Django"`

### Task 8: Build gate, docs, deploy

**Files:** Modify `CLAUDE.md` (API Structure: note that `src/lib/api.ts` is the frontend's single source of endpoints, guarded by `api.test.ts`).

- [ ] **Step 1: Run** `cd apps/frontend && npx tsc --noEmit -p . && npm test && NEXT_PUBLIC_API_URL=https://app.invvite.heystartup.co.uk/api/v1 npm run build`. Expected: all three succeed, with `/enquiry`, `/signup`, `/admin/approvals` and `/invite/[slug]` in the route list.
- [ ] **Step 2: Commit** the docs, push the branch, and open the PR (merge needs the user's approval).
- [ ] **Step 3: Deploy** on `20.198.86.18`: `cd ~/invitation-app && git fetch && git checkout <branch> && docker compose -f docker-compose.prod.yml up -d --build frontend`.
- [ ] **Step 4: Smoke test** against `https://app.invvite.heystartup.co.uk`: sign up with a phone number → dashboard with the approval notice; in Django admin create a staff user → `/admin/approvals` shows the new user → approve; create an invitation → open its `share_url` in a private window → register a guest → reopening shows "welcome back"; submit `/enquiry` → enquiry visible in `/admin/`. Report each step's result.
