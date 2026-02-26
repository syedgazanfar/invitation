# API Testing Checklist

## Overview

This document provides a comprehensive end-to-end testing checklist for all API integrations in the Digital Invitation Platform.

## Testing Environment

- **Backend API:** `http://localhost:8000/api/v1`
- **Frontend:** `http://localhost:3000`
- **Test Data:** Create test users, orders, and invitations for each scenario

## Pre-Testing Setup

### 1. Backend Setup
- [ ] Backend server is running
- [ ] Database migrations are applied
- [ ] Test data is seeded (if applicable)
- [ ] Admin user is created

### 2. Frontend Setup
- [ ] Frontend development server is running
- [ ] `.env.development` is configured correctly
- [ ] Browser DevTools console is open
- [ ] Network tab is open to monitor API calls

## 1. Authentication API Tests

### Registration Flow (`POST /auth/register/`)

- [ ] **Valid Registration**
  - Input: Valid phone, username, email, password
  - Expected: 201 Created, access/refresh tokens, user data
  - Verify: User can login with credentials

- [ ] **Invalid Phone Number**
  - Input: Invalid phone format
  - Expected: 400 Bad Request, error message

- [ ] **Duplicate Phone Number**
  - Input: Phone already registered
  - Expected: 400 Bad Request, "Phone already exists"

- [ ] **Password Mismatch**
  - Input: password ≠ password_confirm
  - Expected: 400 Bad Request, "Passwords don't match"

- [ ] **Missing Required Fields**
  - Input: Missing phone/username/password
  - Expected: 400 Bad Request, validation errors

### Login Flow (`POST /auth/login/`)

- [ ] **Valid Login**
  - Input: Correct phone + password
  - Expected: 200 OK, access/refresh tokens, user data
  - Verify: Token stored in Zustand store

- [ ] **Invalid Credentials**
  - Input: Wrong phone or password
  - Expected: 401 Unauthorized, error message

- [ ] **Missing Fields**
  - Input: Missing phone or password
  - Expected: 400 Bad Request

### OTP Verification (`POST /auth/send-otp/`, `POST /auth/verify-otp/`)

- [ ] **Send OTP**
  - Input: Valid phone number
  - Expected: 200 OK, "OTP sent successfully"
  - Verify: OTP received (check backend logs/SMS)

- [ ] **Verify Valid OTP**
  - Input: Correct phone + OTP
  - Expected: 200 OK, success message

- [ ] **Verify Invalid OTP**
  - Input: Wrong OTP code
  - Expected: 400 Bad Request, "Invalid OTP"

- [ ] **Expired OTP**
  - Input: OTP older than 5 minutes
  - Expected: 400 Bad Request, "OTP expired"

### Profile Management

- [ ] **Get Profile** (`GET /auth/profile/`)
  - Expected: 200 OK, user profile data
  - Verify: All fields match registration

- [ ] **Update Profile** (`PUT /auth/profile/`)
  - Input: Update email, full_name
  - Expected: 200 OK, updated profile
  - Verify: Changes persist on page reload

- [ ] **Change Password** (`POST /auth/change-password/`)
  - Input: Valid old_password, new_password
  - Expected: 200 OK, success message
  - Verify: Can login with new password
  - Verify: Cannot login with old password

### Token Refresh (`POST /auth/refresh/`)

- [ ] **Valid Refresh Token**
  - Input: Valid refresh token
  - Expected: 200 OK, new access token

- [ ] **Invalid Refresh Token**
  - Input: Invalid/expired refresh token
  - Expected: 401 Unauthorized
  - Verify: User redirected to login

### Logout (`POST /auth/logout/`)

- [ ] **Successful Logout**
  - Input: Refresh token
  - Expected: 200 OK
  - Verify: Tokens cleared from store
  - Verify: Redirected to home page
  - Verify: Cannot access protected routes

## 2. Plans & Templates API Tests

### Get Plans (`GET /plans/`)

- [ ] **Fetch All Plans**
  - Expected: 200 OK, array of plans
  - Verify: All plans have name, code, price, features

- [ ] **Plan Data Structure**
  - Verify: Each plan has correct pricing
  - Verify: Features array is populated
  - Verify: Icons/images load correctly

### Get Categories (`GET /plans/categories/list`)

- [ ] **Fetch Categories**
  - Expected: 200 OK, array of categories
  - Verify: Categories have name, slug, event types

### Get Templates (`GET /plans/templates/all`)

- [ ] **Fetch All Templates**
  - Expected: 200 OK, array of templates
  - Verify: Templates have name, thumbnail, plan_code

- [ ] **Filter by Plan**
  - Input: `?plan=premium`
  - Expected: Only premium templates returned

- [ ] **Filter by Category**
  - Input: `?category=wedding`
  - Expected: Only wedding templates returned

### Get Template by ID (`GET /plans/templates/{id}/`)

- [ ] **Valid Template ID**
  - Expected: 200 OK, template details
  - Verify: Full template data with preview images

- [ ] **Invalid Template ID**
  - Expected: 404 Not Found

### Get Featured Templates (`GET /plans/templates/featured`)

- [ ] **Fetch Featured**
  - Expected: 200 OK, featured templates only
  - Verify: is_featured flag is true

## 3. Orders & Invitations API Tests

### Create Order (`POST /invitations/orders/create/`)

**Prerequisites:** User must be logged in

- [ ] **Valid Order Creation**
  - Input: plan_code, event_type, event_type_name
  - Expected: 201 Created, order object with ID
  - Verify: Order appears in "My Orders"

- [ ] **Missing Required Fields**
  - Input: Missing plan_code or event_type
  - Expected: 400 Bad Request

- [ ] **Invalid Plan Code**
  - Input: Non-existent plan_code
  - Expected: 400 Bad Request

### Get Orders (`GET /invitations/orders/`)

- [ ] **Fetch User Orders**
  - Expected: 200 OK, array of user's orders
  - Verify: Orders sorted by creation date (newest first)

- [ ] **Empty Orders**
  - New user with no orders
  - Expected: 200 OK, empty array

### Get Order Details (`GET /invitations/orders/{id}/`)

- [ ] **Valid Order ID**
  - Expected: 200 OK, order details
  - Verify: Payment status, approval status, timestamps

- [ ] **Invalid Order ID**
  - Expected: 404 Not Found

- [ ] **Unauthorized Access**
  - Try accessing another user's order
  - Expected: 403 Forbidden or 404

### Create Invitation (`POST /invitations/create/`)

**Prerequisites:** Order must be approved

- [ ] **Valid Invitation Creation**
  - Input: Complete invitation data (event_title, date, venue, etc.)
  - Expected: 201 Created, invitation object with slug
  - Verify: Invitation appears in "My Invitations"

- [ ] **Missing Required Fields**
  - Input: Missing event_title or date
  - Expected: 400 Bad Request, validation errors

- [ ] **Invalid Date Format**
  - Input: Malformed date string
  - Expected: 400 Bad Request

- [ ] **Order Not Approved**
  - Try creating invitation for unapproved order
  - Expected: 400 Bad Request, "Order not approved"

### Get Invitations (`GET /invitations/`)

- [ ] **Fetch User Invitations**
  - Expected: 200 OK, array of invitations
  - Verify: Pagination works if many invitations

### Get Invitation (`GET /invitations/{slug}/`)

- [ ] **Valid Slug**
  - Expected: 200 OK, invitation details
  - Verify: All fields populated correctly

- [ ] **Invalid Slug**
  - Expected: 404 Not Found

### Update Invitation (`PUT /invitations/{slug}/update/`)

- [ ] **Valid Update**
  - Input: Update event_title, venue, etc.
  - Expected: 200 OK, updated invitation
  - Verify: Changes reflected immediately

- [ ] **Unauthorized Update**
  - Try updating another user's invitation
  - Expected: 403 Forbidden

### Get Invitation Stats (`GET /invitations/{slug}/stats/`)

- [ ] **Fetch Statistics**
  - Expected: 200 OK, stats object
  - Verify: total_guests, attending_count, not_attending_count

### Get Guests (`GET /invitations/{slug}/guests/`)

- [ ] **Fetch Guest List**
  - Expected: 200 OK, array of guests
  - Verify: Guest data includes name, phone, attending status

- [ ] **Empty Guest List**
  - New invitation with no guests
  - Expected: 200 OK, empty array

### Export Guests (`GET /invitations/{slug}/guests/export/`)

- [ ] **Export as CSV**
  - Expected: 200 OK, CSV file download
  - Verify: CSV contains all guest data
  - Verify: File name format: `guests_{event_title}.csv`

## 4. Payment Integration Tests

### Razorpay Order Creation (`POST /invitations/orders/{id}/payment/razorpay/create/`)

- [ ] **Create Payment Order**
  - Input: Valid order_id
  - Expected: 200 OK, Razorpay order_id and amount
  - Verify: Amount matches order total

- [ ] **Order Already Paid**
  - Try creating payment for paid order
  - Expected: 400 Bad Request, "Order already paid"

### Razorpay Payment Verification (`POST /invitations/payment/razorpay/verify/`)

- [ ] **Valid Payment**
  - Input: Valid payment_id, order_id, signature
  - Expected: 200 OK, payment verified
  - Verify: Order status updated to "paid"

- [ ] **Invalid Signature**
  - Input: Tampered signature
  - Expected: 400 Bad Request, "Invalid signature"

### Manual Payment Details (`GET /invitations/payment/manual-details/`)

- [ ] **Fetch Payment Info**
  - Expected: 200 OK, UPI ID, bank details
  - Verify: All fields are populated

## 5. Public Invitation API Tests (No Auth Required)

### Get Public Invitation (`GET /invite/{slug}/`)

- [ ] **Valid Slug**
  - Expected: 200 OK, invitation details
  - Verify: Public can access without login
  - Verify: Sensitive data (creator info) not exposed

- [ ] **Invalid Slug**
  - Expected: 404 Not Found

- [ ] **Expired Invitation**
  - Invitation with past event_date
  - Expected: 200 OK, but show "expired" message in UI

### Check Guest (`POST /invite/{slug}/check/`)

- [ ] **New Guest**
  - Input: New fingerprint
  - Expected: 200 OK, guest_exists: false

- [ ] **Existing Guest**
  - Input: Fingerprint of registered guest
  - Expected: 200 OK, guest_exists: true, guest data

### Register Guest (`POST /invite/{slug}/register/`)

- [ ] **Valid Registration**
  - Input: name, phone, fingerprint, attending
  - Expected: 201 Created, guest object
  - Verify: Guest appears in host's guest list

- [ ] **Duplicate Registration**
  - Same fingerprint registers again
  - Expected: 400 Bad Request or update existing

- [ ] **Missing Fields**
  - Input: Missing required fields
  - Expected: 400 Bad Request

### Update RSVP (`POST /invite/{slug}/rsvp/`)

- [ ] **Update Attendance**
  - Input: fingerprint, attending: true/false
  - Expected: 200 OK, updated guest
  - Verify: Status updated in guest list

- [ ] **Unregistered Guest**
  - Fingerprint not found
  - Expected: 404 Not Found

## 6. Admin Dashboard API Tests

**Prerequisites:** User must have admin role

### Dashboard Stats (`GET /admin-dashboard/dashboard/`)

- [ ] **Fetch Statistics**
  - Expected: 200 OK, stats object
  - Verify: users, orders, invitations, links counts
  - Verify: All numbers are accurate

- [ ] **Non-Admin Access**
  - Login as regular user
  - Expected: 403 Forbidden

### Get Users (`GET /admin-dashboard/users/`)

- [ ] **Fetch All Users**
  - Expected: 200 OK, array of users
  - Verify: Pagination works

- [ ] **Filter by Status**
  - Input: `?status=pending`
  - Expected: Only pending users

- [ ] **Search Users**
  - Input: `?search=john`
  - Expected: Users matching search query

### Get User Detail (`GET /admin-dashboard/users/{id}/`)

- [ ] **Valid User ID**
  - Expected: 200 OK, detailed user info
  - Verify: Orders, invitations, links data included

- [ ] **Invalid User ID**
  - Expected: 404 Not Found

### Approve User (`POST /admin-dashboard/users/{id}/approve/`)

- [ ] **Approve Pending User**
  - Input: Optional notes, payment details
  - Expected: 200 OK, user approved
  - Verify: User status changes to "approved"
  - Verify: User receives notification (if implemented)

- [ ] **Already Approved**
  - Try approving approved user
  - Expected: 400 Bad Request

### Reject User (`POST /admin-dashboard/users/{id}/reject/`)

- [ ] **Reject with Reason**
  - Input: reason, optional block_user flag
  - Expected: 200 OK, user rejected
  - Verify: User cannot create new orders

### Grant Links (`POST /admin-dashboard/users/{id}/grant-links/`)

- [ ] **Grant Regular Links**
  - Input: regular_links: 5
  - Expected: 200 OK, links granted
  - Verify: User's link balance updated

- [ ] **Grant Test Links**
  - Input: test_links: 3
  - Expected: 200 OK, test links granted

### Get Orders (`GET /admin-dashboard/orders/`)

- [ ] **Fetch All Orders**
  - Expected: 200 OK, array of all orders
  - Verify: Orders from all users

- [ ] **Filter by Status**
  - Input: `?status=pending`
  - Expected: Only pending orders

- [ ] **Filter by Payment Status**
  - Input: `?payment_status=paid`
  - Expected: Only paid orders

### Approve Order (`POST /admin-dashboard/orders/{id}/approve/`)

- [ ] **Approve Order**
  - Expected: 200 OK, order approved
  - Verify: User can now create invitation

### Update Payment Status (`POST /admin-dashboard/orders/{id}/payment/`)

- [ ] **Mark as Paid**
  - Input: payment_status: "paid", payment_method: "upi"
  - Expected: 200 OK, payment updated

### Get Notifications (`GET /admin-dashboard/notifications/`)

- [ ] **Fetch All Notifications**
  - Expected: 200 OK, array of notifications

- [ ] **Fetch Unread Only**
  - Input: `?unread=true`
  - Expected: Only unread notifications

### Mark Notification Read (`POST /admin-dashboard/notifications/{id}/read/`)

- [ ] **Mark as Read**
  - Expected: 200 OK
  - Verify: Unread count decreases

## 7. Error Handling Tests

### Authentication Errors

- [ ] **Expired Access Token**
  - Simulate token expiry
  - Expected: Auto-refresh with refresh token
  - Verify: Request retried with new token

- [ ] **Expired Refresh Token**
  - Simulate both tokens expired
  - Expected: Redirect to login page
  - Verify: Tokens cleared from storage

### Network Errors

- [ ] **Backend Down**
  - Stop backend server
  - Expected: Error boundary or error message
  - Verify: User-friendly error shown

- [ ] **Slow Network**
  - Throttle network to 3G
  - Expected: Loading states shown
  - Verify: Request completes or times out gracefully

- [ ] **Request Timeout**
  - API takes >30 seconds
  - Expected: Timeout error, user notified

### CORS Errors

- [ ] **Access from Different Origin**
  - Test from non-whitelisted domain
  - Expected: CORS error blocked by browser
  - Verify: Backend CORS configured correctly

## 8. Performance Tests

- [ ] **Large Data Sets**
  - Test with 100+ orders/invitations
  - Verify: Pagination works correctly
  - Verify: No performance degradation

- [ ] **Concurrent Requests**
  - Multiple API calls simultaneously
  - Verify: All requests complete successfully

- [ ] **Image Upload**
  - Upload various image sizes
  - Verify: Large images compressed
  - Verify: Invalid formats rejected

## 9. Security Tests

- [ ] **SQL Injection**
  - Try SQL injection in input fields
  - Expected: Input sanitized, no SQL errors

- [ ] **XSS Attacks**
  - Try script tags in text fields
  - Expected: Scripts escaped, not executed

- [ ] **Authorization**
  - Try accessing admin routes as regular user
  - Expected: 403 Forbidden

- [ ] **CSRF Protection**
  - Verify CSRF tokens (if implemented)

- [ ] **Rate Limiting**
  - Make 100+ requests rapidly
  - Expected: Rate limit enforced (if implemented)

## 10. Integration Tests

### Complete User Journey

- [ ] **New User Flow**
  1. Register new account
  2. Verify OTP (if enabled)
  3. Browse plans and templates
  4. Create order
  5. Wait for admin approval (or mock it)
  6. Make payment
  7. Create invitation
  8. View invitation as public user
  9. Register as guest
  10. Update RSVP
  11. View guest list as host
  12. Export guests

- [ ] **Admin Flow**
  1. Login as admin
  2. View dashboard stats
  3. Approve pending user
  4. Grant links to user
  5. Approve order
  6. View all invitations
  7. Check notifications

## Testing Tools

### Manual Testing
- Browser DevTools (Network, Console)
- Postman/Insomnia for API testing

### Automated Testing (Recommended)
```bash
# Install testing tools
npm install --save-dev jest @testing-library/react @testing-library/jest-dom

# Run tests
npm test
```

### API Testing with Postman
1. Import API collection
2. Set environment variables (baseURL, token)
3. Run collection tests

## Bug Report Template

When you find a bug, document it:

```markdown
**Bug:** [Brief description]

**Endpoint:** `POST /api/v1/auth/login/`

**Steps to Reproduce:**
1. Step 1
2. Step 2

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Request:**
{
  "phone": "+911234567890",
  "password": "test123"
}

**Response:**
{
  "error": "Something went wrong"
}

**Environment:**
- Browser: Chrome 120
- OS: Windows 11
- Backend: localhost:8000

**Priority:** High/Medium/Low
```

## Testing Sign-Off

Once all tests pass:

- [ ] All authentication flows work
- [ ] All CRUD operations succeed
- [ ] Payment integration tested
- [ ] Admin features verified
- [ ] Error handling works correctly
- [ ] Public invitation flow tested
- [ ] No console errors in browser
- [ ] API performance acceptable
- [ ] Security measures in place
- [ ] Documentation updated

**Tested by:** _______________
**Date:** _______________
**Signature:** _______________

## Next Steps

After testing:
1. Fix any bugs found
2. Update API documentation
3. Create automated test suite
4. Set up CI/CD with automated testing
5. Proceed to deployment
