# Testing Guide - Wedding Invitations Platform

This guide provides comprehensive testing scenarios for all features of the platform.

## Testing Prerequisites

1. Application running (backend on :9301, frontend on :9300)
2. Database seeded with plans, templates, and country pricing
3. Clean browser or incognito mode for testing guest flows

## Phase 1: Authentication Testing

### Test 1.1: User Signup

**Objective**: Verify user registration works correctly

**Steps**:
1. Navigate to http://localhost:9300
2. Click "Sign Up"
3. Fill form:
   - Email: testuser1@example.com
   - Country: United States
   - Password: password123
   - Confirm Password: password123
4. Click "Sign Up"

**Expected Result**:
- User is created
- Redirected to dashboard
- JWT tokens stored in localStorage

**Test variations**:
- Try different countries to test country pricing
- Test password validation (< 8 characters should fail)
- Test duplicate email (should show error)
- Test password mismatch (should show error)

### Test 1.2: User Login

**Objective**: Verify login works correctly

**Steps**:
1. Navigate to http://localhost:9300/login
2. Enter credentials from signup
3. Click "Login"

**Expected Result**:
- User is authenticated
- Redirected to dashboard
- Previous events shown (if any)

**Test variations**:
- Wrong password (should fail)
- Non-existent email (should fail)

### Test 1.3: Session Persistence

**Objective**: Verify JWT refresh works

**Steps**:
1. Login successfully
2. Wait for access token to expire (15 minutes)
3. Make an API request

**Expected Result**:
- Token automatically refreshed
- Request succeeds without re-login

## Phase 2: Pricing Engine Testing

### Test 2.1: Country-Specific Pricing

**Objective**: Verify pricing calculations for different countries

**Steps**:
1. Open browser console
2. Navigate to http://localhost:9301/api/plans/pricing?country=US
3. Note the prices
4. Navigate to http://localhost:9301/api/plans/pricing?country=IN
5. Compare prices

**Expected Result**:
- US prices in USD
- India prices in INR
- Correct exchange rate applied
- Tax and service fees calculated
- Final price = (base * exchange * multiplier) + tax + service_fee

**Test variations**:
- Test each available country (US, IN, GB, CA, AU, DE, FR, JP, BR, MX)
- Verify currency codes match country
- Verify multipliers are applied correctly

### Test 2.2: Plan Limits Verification

**Objective**: Verify each plan has correct limits

**API Call**: GET /api/plans

**Expected Results**:
- BASIC: 40 regular + 5 test = 45 total
- PREMIUM: 100 regular + 10 test = 110 total
- LUXURY: 150 regular + 20 test = 170 total

## Phase 3: Event Creation Testing

### Test 3.1: Complete Event Creation Flow

**Objective**: Create a complete wedding event end-to-end

**Steps**:

**Step 1: Login**
- Login as testuser1@example.com

**Step 2: Start Event Creation**
- Click "Create New Event"
- Fill wedding details:
  - Bride: Alice Johnson
  - Groom: Bob Smith
  - Date: 2024-12-31
  - Time: 18:00
  - Venue: Grand Palace Hotel
  - Address: 456 Wedding Ave
  - City: Los Angeles
  - Country: USA
  - Message: "Join us for our special day!"
- Click "Next: Select Plan"

**Step 3: Select Plan**
- Choose "Premium" plan
- Verify pricing shows for user's country
- Click on Premium card

**Step 4: Select Template**
- Browse templates (should show 20 Premium templates)
- Select "Royal Affair" or any template
- Verify template preview

**Step 5: Payment**
- Verify order summary shows:
  - Base price
  - Tax
  - Service fee
  - Total
- Click "Complete Payment"

**Expected Result**:
- Event created in DRAFT status
- Payment processed successfully
- Event activated with slug generated
- Redirected to event details page
- Invitation URL displayed
- Expiry date set to +5 days

**Test variations**:
- Try each plan (BASIC, PREMIUM, LUXURY)
- Try different templates
- Test with coordinates (lat/lng) for map
- Simulate payment failure (backend has simulateFailure option)

### Test 3.2: Event Status Verification

**Objective**: Verify event lifecycle states

**Steps**:
1. Create event (should be DRAFT initially)
2. Process payment (should remain DRAFT)
3. Activate event (should become ACTIVE)
4. Wait 5 days or manually update DB (should become EXPIRED)

**Database Check**:
```sql
SELECT id, status, slug, activated_at, expires_at FROM events;
```

## Phase 4: Guest Limit Testing

### Test 4.1: Regular Guest Limits

**Objective**: Verify regular guest limits are enforced

**Setup**:
- Create a BASIC plan event (40 regular guest limit)
- Get the invitation URL

**Steps**:
1. Open invitation URL 40 times in different browsers/incognito
2. Enter different names each time (uncheck "test guest")
3. Verify each guest is registered
4. On the 41st attempt, try to register another regular guest

**Expected Result**:
- First 40 guests: Successfully registered
- 41st guest: Error "Guest limit reached"

**Database Check**:
```sql
SELECT COUNT(*) FROM guests WHERE event_id = 'event-id' AND is_test = false;
-- Should return 40
```

### Test 4.2: Test Guest Limits

**Objective**: Verify test guest limits are separate from regular

**Setup**:
- Use same event from Test 4.1 (40 regular guests already)
- BASIC plan allows 5 test guests

**Steps**:
1. Open invitation URL 5 times
2. Enter different names with "test guest" checked
3. Try 6th test guest

**Expected Result**:
- First 5 test guests: Successfully registered
- 6th test guest: Error "Test guest limit reached"
- Regular guests unaffected (still at 40)

**Database Check**:
```sql
SELECT is_test, COUNT(*) FROM guests WHERE event_id = 'event-id' GROUP BY is_test;
-- Should show: false: 40, true: 5
```

### Test 4.3: Combined Limits

**Objective**: Verify total capacity

**Test Matrix**:

| Plan | Regular Max | Test Max | Total | Test Scenario |
|------|------------|----------|-------|---------------|
| BASIC | 40 | 5 | 45 | Fill both, verify 46th fails |
| PREMIUM | 100 | 10 | 110 | Fill both, verify 111th fails |
| LUXURY | 150 | 20 | 170 | Fill both, verify 171st fails |

## Phase 5: Invitation Experience Testing

### Test 5.1: Valid Invitation Access

**Objective**: Test complete guest invitation flow

**Steps**:
1. Get invitation URL from active event
2. Open in new incognito window
3. Verify "Enter your name" screen appears
4. Enter name: "John Doe"
5. Uncheck "test guest"
6. Click "View Invitation"

**Expected Result**:
- Animation sequence plays:
  1. Welcome with guest name
  2. Couple names appear
  3. Date and time revealed
  4. Venue details with map
- All information correct
- Map displays venue location
- Message (if provided) shows

**Test variations**:
- Test with test guest checked
- Test with special characters in name
- Test with very long names
- Test on mobile devices

### Test 5.2: Expired Invitation

**Objective**: Verify expired invitations are blocked

**Steps**:
1. Create an event
2. Manually update expires_at in database to past date:
```sql
UPDATE events SET expires_at = NOW() - INTERVAL '1 day' WHERE id = 'event-id';
```
3. Try to access invitation URL

**Expected Result**:
- "Invitation Expired" message shown
- Cannot enter name or view invitation

### Test 5.3: Invalid/Non-existent Invitation

**Objective**: Verify error handling for bad URLs

**Steps**:
1. Navigate to http://localhost:9300/invite/invalidslug123

**Expected Result**:
- Error message displayed
- "Invitation not found"

## Phase 6: Dashboard and Analytics Testing

### Test 6.1: Event Listing

**Objective**: Verify dashboard shows all user events

**Setup**:
- Create 3 events with different statuses:
  1. DRAFT (not paid)
  2. ACTIVE (paid and activated)
  3. EXPIRED (manually set)

**Steps**:
1. Login and view dashboard

**Expected Result**:
- All 3 events displayed
- Correct status badges
- Event details visible
- ACTIVE event shows invitation URL
- Guest counts displayed

### Test 6.2: Guest Statistics

**Objective**: Verify guest analytics are accurate

**Setup**:
- Create event with BASIC plan
- Register 10 regular guests
- Register 2 test guests

**Steps**:
1. Navigate to event details
2. View guest statistics

**Expected Result**:
- Regular guests: 10/40 (30 remaining)
- Test guests: 2/5 (3 remaining)
- Total: 12/45 (33 remaining)
- Guest list shows all 12 with correct type badges

### Test 6.3: Guest List Pagination

**Objective**: Test pagination with many guests

**Setup**:
- Register 100+ guests for an event

**Steps**:
1. View event details
2. Scroll to guest list

**Expected Result**:
- Shows 50 guests per page (default)
- Pagination controls appear
- Can navigate between pages
- Total count accurate

### Test 6.4: CSV Export

**Objective**: Verify guest data export

**Steps**:
1. Navigate to event with guests
2. Click "Export CSV"

**Expected Result**:
- CSV file downloaded
- Headers: Guest Name, Is Test, IP Address, User Agent, Created At
- All guests included
- Data correctly formatted

## Phase 7: Template and Plan Testing

### Test 7.1: Template Filtering

**Objective**: Verify templates filter by plan

**API Tests**:
```
GET /api/templates?plan=BASIC
- Should return 20 BASIC templates

GET /api/templates?plan=PREMIUM
- Should return 20 PREMIUM templates

GET /api/templates?plan=LUXURY
- Should return 20 LUXURY templates

GET /api/templates
- Should return all 60 templates
```

### Test 7.2: Template Validation

**Objective**: Verify template-plan matching

**Steps**:
1. Create event with BASIC plan
2. Try to manually assign PREMIUM template via API

**Expected Result**:
- Error: "Template does not belong to the selected plan"

## Phase 8: Security Testing

### Test 8.1: Authentication Protection

**Objective**: Verify protected routes require authentication

**Steps**:
1. Logout or clear localStorage
2. Try to access:
   - /api/events
   - /api/users/profile
   - /api/events/:id

**Expected Result**:
- 401 Unauthorized responses
- Redirected to login on frontend

### Test 8.2: Authorization Testing

**Objective**: Verify users can only access their own events

**Setup**:
- Create 2 user accounts
- User A creates event
- User B tries to access User A's event

**Steps**:
1. Login as User B
2. GET /api/events/:user-a-event-id

**Expected Result**:
- 403 Forbidden or 404 Not Found
- Cannot view or modify other users' events

### Test 8.3: Input Validation

**Test Invalid Inputs**:

**Email validation**:
- Invalid format: "notanemail" → Should fail
- Missing @ symbol → Should fail

**Password validation**:
- < 8 characters → Should fail
- Empty → Should fail

**Event dates**:
- Invalid date format → Should fail
- Past dates → Should allow (for testing)

**Coordinates**:
- Lat > 90 or < -90 → Should fail
- Lng > 180 or < -180 → Should fail

## Phase 9: Edge Cases and Error Handling

### Test 9.1: Concurrent Guest Registration

**Objective**: Test race conditions at guest limit

**Setup**:
- Event with 39/40 regular guests
- 2 users try to register simultaneously

**Expected Result**:
- First request succeeds (40/40)
- Second request fails with limit reached

### Test 9.2: Expired Token Refresh

**Objective**: Verify refresh token flow

**Steps**:
1. Login
2. Wait 15+ minutes (access token expires)
3. Make authenticated request

**Expected Result**:
- Access token automatically refreshed
- Request succeeds
- New tokens stored

### Test 9.3: Database Constraints

**Test Unique Constraints**:
```sql
-- Try to create duplicate email
INSERT INTO users (email, password_hash) VALUES ('test@example.com', 'hash');
-- Should fail with unique constraint violation

-- Try to create duplicate slug
UPDATE events SET slug = 'existing-slug' WHERE id = 'different-event';
-- Should fail
```

## Phase 10: Performance Testing

### Test 10.1: Page Load Times

**Measure**:
- Home page: < 2s
- Dashboard: < 3s
- Event creation: < 2s
- Invitation view: < 2s

### Test 10.2: API Response Times

**Measure**:
- GET /api/plans: < 100ms
- GET /api/events: < 200ms
- POST /api/invite/:slug/register-guest: < 500ms

### Test 10.3: Large Dataset Handling

**Setup**:
- Create event with 150 guests (LUXURY plan max)

**Test**:
- Guest list loads and paginates correctly
- CSV export completes successfully
- Dashboard statistics calculated quickly

## Test Automation Script Example

```bash
#!/bin/bash
# Quick smoke test script

echo "Testing authentication..."
curl -X POST http://localhost:9301/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123"}'

echo "Testing plans API..."
curl http://localhost:9301/api/plans

echo "Testing pricing API..."
curl "http://localhost:9301/api/plans/pricing?country=US"

echo "Testing templates API..."
curl "http://localhost:9301/api/templates?plan=BASIC"

echo "All basic tests passed!"
```

## Test Checklist

Use this checklist to verify all features:

### Authentication
- [ ] Signup with valid data
- [ ] Signup with invalid email
- [ ] Signup with weak password
- [ ] Login with valid credentials
- [ ] Login with wrong password
- [ ] Logout
- [ ] Token refresh

### Pricing
- [ ] USD pricing (US)
- [ ] INR pricing (India)
- [ ] EUR pricing (Germany)
- [ ] All 10 countries tested

### Plans & Templates
- [ ] All 3 plans listed
- [ ] 20 templates per plan
- [ ] Template filtering works

### Event Creation
- [ ] BASIC plan event
- [ ] PREMIUM plan event
- [ ] LUXURY plan event
- [ ] With all optional fields
- [ ] Payment flow
- [ ] Activation

### Guest Limits
- [ ] Regular guest limit (BASIC)
- [ ] Test guest limit (BASIC)
- [ ] Regular guest limit (PREMIUM)
- [ ] Test guest limit (PREMIUM)
- [ ] Regular guest limit (LUXURY)
- [ ] Test guest limit (LUXURY)

### Invitation Experience
- [ ] Name entry screen
- [ ] Animation sequence
- [ ] Map display
- [ ] Message display
- [ ] Expired handling
- [ ] Invalid slug handling

### Dashboard
- [ ] Event listing
- [ ] Event details
- [ ] Guest statistics
- [ ] Guest list
- [ ] Pagination
- [ ] CSV export

### Security
- [ ] Protected routes
- [ ] User isolation
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS prevention

## Reporting Issues

When reporting issues, include:
1. Test phase and number
2. Steps to reproduce
3. Expected vs actual result
4. Browser/environment
5. Console errors (if any)
6. Database state (if relevant)
