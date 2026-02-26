# API Testing Guide

**Project:** Wedding Invitations Platform
**Date:** February 26, 2026

---

## Overview

This guide explains how to test all APIs in the Wedding Invitations Platform. Three testing methods are provided:

1. **Quick Test** - Fast verification that server is running (5 minutes)
2. **Comprehensive Test** - Full API test suite (15-20 minutes)
3. **Manual Testing** - Using curl commands or Postman

---

## Prerequisites

### 1. Start the Backend Server

```bash
cd apps/backend/src
python manage.py runserver 0.0.0.0:8000
```

Verify server is running by visiting: http://localhost:8000/api/v1/

### 2. Install Testing Dependencies (for comprehensive tests)

```bash
pip install requests colorama
```

### 3. Optional: Install jq (for pretty JSON output)

**Windows:**
```bash
# Using Chocolatey
choco install jq

# Or download from: https://stedolan.github.io/jq/download/
```

**Linux:**
```bash
sudo apt-get install jq
```

**Mac:**
```bash
brew install jq
```

---

## Method 1: Quick Test (Recommended)

Tests the most important endpoints to verify the server is working correctly.

### Windows:
```bash
quick_api_test.bat
```

### Linux/Mac:
```bash
chmod +x quick_api_test.sh
./quick_api_test.sh
```

### What it tests:
1. ✓ Server connectivity
2. ✓ API Root endpoint
3. ✓ Plans list
4. ✓ Categories list
5. ✓ Templates list
6. ✓ User registration
7. ✓ User login
8. ✓ Protected endpoints (with authentication)

**Duration:** ~1-2 minutes

---

## Method 2: Comprehensive Test

Tests all 75+ endpoints systematically with detailed reporting.

### Run the test:
```bash
python test_all_apis.py
```

### What it tests:

#### 1. API Root
- GET /api/v1/ - API information

#### 2. Authentication (10 endpoints)
- POST /auth/register/ - User registration
- POST /auth/login/ - User login
- POST /auth/logout/ - User logout
- POST /auth/refresh/ - Token refresh
- GET /auth/profile/ - Get user profile
- POST /auth/change-password/ - Change password
- POST /auth/send-otp/ - Send OTP
- POST /auth/verify-otp/ - Verify OTP
- GET /auth/my-plan/ - Get current plan
- POST /auth/request-plan-change/ - Request plan change

#### 3. Plans & Templates (8 endpoints)
- GET /plans/ - List all plans
- GET /plans/{code}/ - Plan details
- GET /plans/categories/list - List categories
- GET /plans/templates/all - List all templates
- GET /plans/templates/featured - Featured templates
- GET /plans/templates/{id}/ - Template details
- GET /plans/templates/by-plan/{code}/ - Templates by plan

#### 4. Invitations & Orders (10 endpoints)
- GET /invitations/orders/ - List orders
- POST /invitations/orders/create/ - Create order
- GET /invitations/orders/{id}/ - Order details
- GET /invitations/ - List invitations
- POST /invitations/create/ - Create invitation
- GET /invitations/{slug}/ - Invitation details
- PUT /invitations/{slug}/update/ - Update invitation
- GET /invitations/{slug}/stats/ - Invitation statistics
- GET /invitations/{slug}/guests/ - List guests
- GET /invitations/{slug}/guests/export/ - Export guests

#### 5. AI Features (15+ endpoints)
- POST /ai/analyze-photo/ - Photo analysis
- POST /ai/extract-colors/ - Color extraction
- POST /ai/detect-mood/ - Mood detection
- POST /ai/generate-messages/ - Message generation
- GET /ai/message-styles/ - Available styles
- POST /ai/generate-hashtags/ - Hashtag generation
- GET /ai/recommend-templates/ - Template recommendations
- GET /ai/style-recommendations/ - Style recommendations
- GET /ai/usage/ - AI usage statistics
- GET /ai/limits/ - AI usage limits
- GET /ai/smart-suggestions/ - Smart suggestions

#### 6. Admin Dashboard (15+ endpoints)
- GET /admin-dashboard/dashboard/ - Dashboard stats
- GET /admin-dashboard/approvals/pending/ - Pending approvals
- GET /admin-dashboard/approvals/recent/ - Recent approvals
- GET /admin-dashboard/users/ - List all users
- GET /admin-dashboard/users/pending/ - Pending users
- GET /admin-dashboard/users/{id}/ - User details
- POST /admin-dashboard/users/{id}/approve/ - Approve user
- POST /admin-dashboard/users/{id}/reject/ - Reject user
- POST /admin-dashboard/users/{id}/notes/ - Update notes
- POST /admin-dashboard/users/{id}/grant-links/ - Grant links
- GET /admin-dashboard/notifications/ - List notifications
- POST /admin-dashboard/notifications/{id}/read/ - Mark as read

#### 7. Public Endpoints (4 endpoints)
- GET /api/invite/{slug}/ - View invitation
- GET /api/invite/{slug}/check/ - Check guest status
- POST /api/invite/{slug}/register/ - Register guest
- POST /api/invite/{slug}/rsvp/ - Update RSVP

#### 8. Error Handling
- 404 Not Found
- 401 Unauthorized
- 400 Bad Request

**Duration:** ~10-15 minutes

### Sample Output:

```
********************************************************************************
Wedding Invitations Platform - API Test Suite
********************************************************************************

================================================================================
                              1. API ROOT
================================================================================

✓ API Root accessible
  Status: operational
ℹ Version
  v1

Cyan Available Endpoints:
  - auth: /api/v1/auth/
  - plans: /api/v1/plans/
  - invitations: /api/v1/invitations/
  ...

================================================================================
                            2. AUTHENTICATION
================================================================================

✓ User registration
  User created: testuser
✓ User login
  Token received: eyJ0eXAiOiJKV1QiLCJ...
✓ Token refresh
✓ Profile access
  User: testuser
✓ User logout

...
```

---

## Method 3: Manual Testing

### Using curl

#### 1. Test API Root:
```bash
curl http://localhost:8000/api/v1/
```

#### 2. Register a user:
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "TestPassword123",
    "password_confirm": "TestPassword123"
  }'
```

#### 3. Login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+919876543210",
    "password": "TestPassword123"
  }'
```

**Save the access token from the response.**

#### 4. Get profile (protected endpoint):
```bash
curl http://localhost:8000/api/v1/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 5. List plans:
```bash
curl http://localhost:8000/api/v1/plans/
```

#### 6. List templates:
```bash
curl http://localhost:8000/api/v1/plans/templates/all
```

#### 7. Create invitation:
```bash
curl -X POST http://localhost:8000/api/v1/invitations/create/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Wedding",
    "event_type": "wedding",
    "bride_name": "Jane",
    "groom_name": "John",
    "event_date": "2026-12-31",
    "event_time": "18:00",
    "venue_name": "Test Venue",
    "venue_address": "123 Test St",
    "message": "Join us!"
  }'
```

#### 8. List invitations:
```bash
curl http://localhost:8000/api/v1/invitations/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Using Postman

1. **Import Collection:**
   - Create a new collection in Postman
   - Add environment variable `base_url` = `http://localhost:8000/api/v1`
   - Add environment variable `token` = (will be set after login)

2. **Add Requests:**
   - Copy endpoints from `API_ENDPOINTS_DOCUMENTATION.md`
   - Use `{{base_url}}` and `{{token}}` variables

3. **Test Flow:**
   - Register → Login → Save token → Test protected endpoints

### Using httpie (Alternative to curl)

```bash
# Install httpie
pip install httpie

# Test API
http GET http://localhost:8000/api/v1/

# Register
http POST http://localhost:8000/api/v1/auth/register/ \
  phone="+919876543210" \
  username="testuser" \
  password="TestPassword123" \
  password_confirm="TestPassword123"

# Login
http POST http://localhost:8000/api/v1/auth/login/ \
  phone="+919876543210" \
  password="TestPassword123"

# Get profile
http GET http://localhost:8000/api/v1/auth/profile/ \
  "Authorization:Bearer YOUR_TOKEN"
```

---

## Common Issues & Solutions

### Issue 1: Server not running
**Error:** `Connection refused` or `Failed to connect`

**Solution:**
```bash
cd apps/backend/src
python manage.py runserver 0.0.0.0:8000
```

### Issue 2: Database not initialized
**Error:** `Database table doesn't exist`

**Solution:**
```bash
cd apps/backend/src
python manage.py migrate
```

### Issue 3: Missing dependencies
**Error:** `ModuleNotFoundError`

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 4: Authentication failed
**Error:** `401 Unauthorized`

**Solution:**
- Verify token is included in Authorization header
- Check token hasn't expired (24 hour lifetime)
- Use refresh token to get new access token

### Issue 5: Permission denied
**Error:** `403 Forbidden`

**Solution:**
- Admin endpoints require staff/admin permissions
- Create admin user: `python manage.py createsuperuser`

---

## Test Data

### Test Users:
```
Regular User:
  Phone: +919876543210
  Username: testuser
  Password: TestPassword123

Admin User:
  Phone: +919876543211
  Username: adminuser
  Password: AdminPassword123
```

### Test Invitation:
```json
{
  "title": "John & Jane's Wedding",
  "event_type": "wedding",
  "bride_name": "Jane Doe",
  "groom_name": "John Smith",
  "event_date": "2026-12-31",
  "event_time": "18:00",
  "venue_name": "Grand Hotel",
  "venue_address": "123 Main St, City 12345",
  "message": "Join us for our special day!"
}
```

---

## API Documentation

For complete API documentation with all endpoints, request/response formats, and examples, see:

- **API_ENDPOINTS_DOCUMENTATION.md** - Complete endpoint reference
- **Backend API Docs** - http://localhost:8000/admin/doc/ (if enabled)
- **Django Admin** - http://localhost:8000/admin/

---

## Testing Checklist

### Basic Tests
- [ ] Server starts without errors
- [ ] API root returns correct response
- [ ] User registration works
- [ ] User login works
- [ ] Token refresh works
- [ ] Protected endpoints require authentication

### Plans & Templates
- [ ] Plans list returns data
- [ ] Plan details work for each plan
- [ ] Categories list returns data
- [ ] Templates list returns data
- [ ] Featured templates endpoint works

### Invitations
- [ ] Order creation works
- [ ] Invitation creation works
- [ ] Invitation list shows created invitations
- [ ] Invitation details endpoint works
- [ ] Invitation stats endpoint works
- [ ] Guest management works

### AI Features
- [ ] Message generation works
- [ ] Hashtag generation works
- [ ] AI usage tracking works
- [ ] AI limits are enforced

### Public Endpoints
- [ ] Public invitation view works (no auth)
- [ ] Guest registration works (no auth)
- [ ] RSVP updates work

### Admin Dashboard
- [ ] Dashboard stats accessible (admin only)
- [ ] User management works
- [ ] Approval workflow works

### Error Handling
- [ ] 404 returned for invalid endpoints
- [ ] 401 returned for missing auth
- [ ] 403 returned for insufficient permissions
- [ ] 400 returned for invalid data

---

## Performance Testing

### Load Testing with Apache Bench:
```bash
# Install Apache Bench
apt-get install apache2-utils  # Linux
brew install httpd  # Mac

# Test API root
ab -n 1000 -c 10 http://localhost:8000/api/v1/

# Test with authentication
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/auth/profile/
```

### Load Testing with locust:
```bash
# Install locust
pip install locust

# Create locustfile.py with test scenarios
# Run load test
locust -f locustfile.py --host=http://localhost:8000
```

---

## Continuous Testing

### GitHub Actions (CI/CD):
```yaml
# .github/workflows/api-tests.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run migrations
        run: python manage.py migrate
      - name: Start server
        run: python manage.py runserver &
      - name: Run API tests
        run: python test_all_apis.py
```

---

## Reporting Issues

If you find issues during testing:

1. **Check the logs:**
   ```bash
   # Backend logs
   tail -f apps/backend/src/logs/django.log
   ```

2. **Create an issue:**
   - Go to: https://github.com/syedgazanfar/invitation/issues
   - Include: API endpoint, request data, response, error message

3. **Contact support:**
   - Email: support@example.com

---

## Summary

- ✅ **Quick Test** - Run `quick_api_test.bat` (Windows) or `./quick_api_test.sh` (Linux/Mac)
- ✅ **Comprehensive Test** - Run `python test_all_apis.py`
- ✅ **Manual Testing** - Use curl, Postman, or httpie
- ✅ **Documentation** - See `API_ENDPOINTS_DOCUMENTATION.md`

**All test scripts are ready to use!**

---

**Last Updated:** February 26, 2026
