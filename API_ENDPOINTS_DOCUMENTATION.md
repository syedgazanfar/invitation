# API Endpoints Documentation

**Project:** Wedding Invitations Platform
**API Version:** v1
**Base URL:** `http://localhost:8000/api/v1`
**Date:** February 26, 2026

---

## Table of Contents

1. [API Root](#1-api-root)
2. [Authentication](#2-authentication)
3. [Plans & Templates](#3-plans--templates)
4. [Invitations & Orders](#4-invitations--orders)
5. [AI Features](#5-ai-features)
6. [Admin Dashboard](#6-admin-dashboard)
7. [Public Endpoints](#7-public-endpoints)
8. [Payment](#8-payment)

---

## 1. API Root

### Get API Information
```
GET /api/v1/
```

**Response:**
```json
{
  "name": "Wedding Invitations Platform API",
  "version": "v1",
  "status": "operational",
  "endpoints": {
    "auth": "/api/v1/auth/",
    "plans": "/api/v1/plans/",
    "invitations": "/api/v1/invitations/",
    "admin_dashboard": "/api/v1/admin-dashboard/",
    "ai": "/api/v1/ai/",
    "invite": "/api/invite/"
  }
}
```

---

## 2. Authentication

**Base Path:** `/api/v1/auth/`

### Register User
```
POST /auth/register/
```

**Request Body:**
```json
{
  "phone": "+919876543210",
  "username": "johndoe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "password": "SecurePassword123",
  "password_confirm": "SecurePassword123"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com",
    "phone": "+919876543210",
    "full_name": "John Doe"
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

### Login
```
POST /auth/login/
```

**Request Body:**
```json
{
  "phone": "+919876543210",
  "password": "SecurePassword123"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": "uuid",
    "username": "johndoe",
    "email": "john@example.com"
  },
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

### Logout
```
POST /auth/logout/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response:** `200 OK`

### Refresh Token
```
POST /auth/refresh/
```

**Request Body:**
```json
{
  "refresh": "jwt_refresh_token"
}
```

**Response:** `200 OK`
```json
{
  "access": "new_jwt_access_token"
}
```

### Get Profile
```
GET /auth/profile/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "full_name": "John Doe",
  "current_plan": {
    "code": "FREE",
    "name": "Free Plan",
    "status": "active"
  },
  "phone_verified": true,
  "created_at": "2026-01-15T10:30:00Z"
}
```

### Change Password
```
POST /auth/change-password/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "old_password": "OldPassword123",
  "new_password": "NewPassword123",
  "new_password_confirm": "NewPassword123"
}
```

**Response:** `200 OK`

### Send OTP
```
POST /auth/send-otp/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "phone": "+919876543210"
}
```

**Response:** `200 OK`
```json
{
  "message": "OTP sent successfully",
  "otp_id": "uuid"
}
```

### Verify OTP
```
POST /auth/verify-otp/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "otp_id": "uuid",
  "otp_code": "123456"
}
```

**Response:** `200 OK`

### Get My Plan
```
GET /auth/my-plan/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "plan": {
    "code": "PREMIUM",
    "name": "Premium Plan",
    "price": 999.00
  },
  "status": "active",
  "started_at": "2026-01-15",
  "expires_at": "2026-12-31",
  "invitations_used": 5,
  "invitations_limit": 50
}
```

### Request Plan Change
```
POST /auth/request-plan-change/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "new_plan": "PREMIUM",
  "reason": "Need more features"
}
```

**Response:** `200 OK`

---

## 3. Plans & Templates

**Base Path:** `/api/v1/plans/`

### List Plans
```
GET /plans/
```

**Response:** `200 OK`
```json
[
  {
    "code": "FREE",
    "name": "Free Plan",
    "price": 0.00,
    "invitations_limit": 1,
    "features": ["Basic templates", "1 invitation"]
  },
  {
    "code": "BASIC",
    "name": "Basic Plan",
    "price": 299.00,
    "invitations_limit": 5,
    "features": ["All templates", "5 invitations", "Basic customization"]
  }
]
```

### Get Plan Detail
```
GET /plans/{plan_code}/
```

**Example:** `GET /plans/PREMIUM/`

**Response:** `200 OK`
```json
{
  "code": "PREMIUM",
  "name": "Premium Plan",
  "price": 999.00,
  "invitations_limit": 50,
  "ai_requests_limit": 200,
  "features": [
    "Unlimited templates",
    "50 invitations",
    "Advanced customization",
    "AI features",
    "Priority support"
  ],
  "is_popular": true,
  "description": "Best for wedding planners"
}
```

### List Categories
```
GET /plans/categories/list
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Wedding",
    "slug": "wedding",
    "description": "Wedding invitation templates",
    "template_count": 25
  },
  {
    "id": "uuid",
    "name": "Birthday",
    "slug": "birthday",
    "template_count": 15
  }
]
```

### List Templates
```
GET /plans/templates/all
```

**Query Parameters:**
- `category` (optional): Filter by category slug
- `plan` (optional): Filter by plan code

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Elegant Wedding",
    "category": "Wedding",
    "thumbnail": "https://example.com/template1.jpg",
    "preview_url": "https://example.com/preview/template1",
    "is_premium": false,
    "required_plan": "FREE"
  }
]
```

### Get Featured Templates
```
GET /plans/templates/featured
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Royal Wedding",
    "thumbnail": "https://example.com/template1.jpg",
    "is_featured": true
  }
]
```

### Get Template Detail
```
GET /plans/templates/{template_id}/
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Elegant Wedding",
  "description": "Beautiful elegant template",
  "category": "Wedding",
  "thumbnail": "https://example.com/template1.jpg",
  "preview_url": "https://example.com/preview/template1",
  "is_premium": false,
  "required_plan": "FREE",
  "customization_options": {
    "colors": ["#000000", "#FFFFFF"],
    "fonts": ["Roboto", "Open Sans"]
  }
}
```

### Get Templates by Plan
```
GET /plans/templates/by-plan/{plan_code}/
```

**Example:** `GET /plans/templates/by-plan/PREMIUM/`

**Response:** `200 OK`

---

## 4. Invitations & Orders

**Base Path:** `/api/v1/invitations/`

### List Orders
```
GET /invitations/orders/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "plan": "PREMIUM",
    "status": "completed",
    "amount": 999.00,
    "created_at": "2026-02-15T10:00:00Z",
    "invitations_count": 2
  }
]
```

### Create Order
```
POST /invitations/orders/create/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "plan": "PREMIUM",
  "template_id": "uuid",
  "quantity": 1
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "plan": "PREMIUM",
  "amount": 999.00,
  "status": "pending",
  "payment_url": "https://payment.example.com/..."
}
```

### Get Order Detail
```
GET /invitations/orders/{order_id}/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`

### List Invitations
```
GET /invitations/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "slug": "john-jane-wedding",
    "title": "John & Jane's Wedding",
    "event_type": "wedding",
    "event_date": "2026-12-31",
    "status": "active",
    "views": 145,
    "rsvps": 32,
    "created_at": "2026-02-15T10:00:00Z"
  }
]
```

### Create Invitation
```
POST /invitations/create/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "title": "John & Jane's Wedding",
  "event_type": "wedding",
  "bride_name": "Jane Doe",
  "groom_name": "John Smith",
  "event_date": "2026-12-31",
  "event_time": "18:00",
  "venue_name": "Grand Hotel",
  "venue_address": "123 Main St, City, State 12345",
  "message": "Join us for our special day!",
  "template_id": "uuid",
  "custom_colors": {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4"
  }
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "slug": "john-jane-wedding",
  "title": "John & Jane's Wedding",
  "public_url": "https://example.com/invite/john-jane-wedding"
}
```

### Get Invitation Detail
```
GET /invitations/{slug}/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "slug": "john-jane-wedding",
  "title": "John & Jane's Wedding",
  "event_type": "wedding",
  "bride_name": "Jane Doe",
  "groom_name": "John Smith",
  "event_date": "2026-12-31",
  "event_time": "18:00",
  "venue_name": "Grand Hotel",
  "venue_address": "123 Main St",
  "message": "Join us for our special day!",
  "template": {
    "id": "uuid",
    "name": "Elegant Wedding"
  },
  "views": 145,
  "rsvps": 32,
  "guests_count": 50,
  "public_url": "https://example.com/invite/john-jane-wedding",
  "created_at": "2026-02-15T10:00:00Z"
}
```

### Update Invitation
```
PUT /invitations/{slug}/update/
Authorization: Bearer {access_token}
```

**Request Body:** (Same as create)

**Response:** `200 OK`

### Get Invitation Stats
```
GET /invitations/{slug}/stats/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "total_views": 145,
  "unique_views": 98,
  "total_rsvps": 32,
  "confirmed_guests": 28,
  "declined_guests": 4,
  "pending_guests": 18,
  "views_by_day": [
    {"date": "2026-02-20", "views": 25},
    {"date": "2026-02-21", "views": 30}
  ],
  "top_referrers": [
    {"source": "WhatsApp", "count": 45},
    {"source": "Facebook", "count": 30}
  ]
}
```

### List Guests
```
GET /invitations/{slug}/guests/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "name": "Alice Johnson",
    "phone": "+919876543210",
    "email": "alice@example.com",
    "rsvp_status": "confirmed",
    "guests_count": 2,
    "registered_at": "2026-02-20T15:30:00Z"
  }
]
```

### Export Guests
```
GET /invitations/{slug}/guests/export/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `format`: `csv` or `excel` (default: csv)

**Response:** `200 OK` (File download)

---

## 5. AI Features

**Base Path:** `/api/v1/ai/`

### Analyze Photo
```
POST /ai/analyze-photo/
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body:**
```
photo: [file]
```

**Response:** `200 OK`
```json
{
  "colors": [
    {"hex": "#FF6B6B", "name": "Coral Red", "percentage": 35},
    {"hex": "#4ECDC4", "name": "Turquoise", "percentage": 25}
  ],
  "mood": "romantic",
  "style": "modern",
  "recommended_templates": ["uuid1", "uuid2"]
}
```

### Extract Colors
```
POST /ai/extract-colors/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "image_url": "https://example.com/photo.jpg"
}
```
OR
```
Content-Type: multipart/form-data
photo: [file]
```

**Response:** `200 OK`
```json
{
  "colors": [
    {"hex": "#FF6B6B", "name": "Coral Red", "percentage": 35},
    {"hex": "#4ECDC4", "name": "Turquoise", "percentage": 25}
  ]
}
```

### Detect Mood
```
POST /ai/detect-mood/
Authorization: Bearer {access_token}
```

**Request Body:** (Same as extract colors)

**Response:** `200 OK`
```json
{
  "mood": "romantic",
  "confidence": 0.89,
  "emotions": {
    "joy": 0.75,
    "serenity": 0.60,
    "excitement": 0.45
  }
}
```

### Generate Messages
```
POST /ai/generate-messages/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "event_type": "wedding",
  "bride_name": "Jane",
  "groom_name": "John",
  "style": "formal",
  "language": "en",
  "additional_context": "Beach wedding"
}
```

**Response:** `200 OK`
```json
{
  "messages": [
    {
      "text": "Together with their families, Jane and John request the pleasure of your company...",
      "style": "formal",
      "length": "long"
    },
    {
      "text": "Join us as we celebrate the union of Jane and John...",
      "style": "formal",
      "length": "medium"
    }
  ],
  "usage": {
    "requests_used": 5,
    "requests_remaining": 195
  }
}
```

### Get Message Styles
```
GET /ai/message-styles/
```

**Response:** `200 OK`
```json
{
  "styles": [
    {
      "id": "formal",
      "name": "Formal",
      "description": "Traditional and elegant"
    },
    {
      "id": "casual",
      "name": "Casual",
      "description": "Relaxed and friendly"
    }
  ]
}
```

### Generate Hashtags
```
POST /ai/generate-hashtags/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "bride_name": "Jane",
  "groom_name": "John",
  "event_date": "2026-12-31",
  "theme": "beach"
}
```

**Response:** `200 OK`
```json
{
  "hashtags": [
    "#JohnAndJane2026",
    "#JaneMarriesJohn",
    "#BeachWeddingBliss",
    "#ForeverStartsToday"
  ]
}
```

### Get Template Recommendations
```
GET /ai/recommend-templates/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `colors` (optional): Comma-separated hex colors
- `mood` (optional): Mood keyword
- `style` (optional): Style preference

**Response:** `200 OK`
```json
{
  "recommendations": [
    {
      "template_id": "uuid",
      "name": "Elegant Wedding",
      "score": 0.95,
      "reason": "Matches your color palette"
    }
  ]
}
```

### Get Style Recommendations
```
GET /ai/style-recommendations/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `mood` (optional)
- `event_type` (optional)

**Response:** `200 OK`

### Get AI Usage Stats
```
GET /ai/usage/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "usage": {
    "total_requests": 45,
    "photo_analysis": 10,
    "message_generation": 25,
    "hashtag_generation": 10
  },
  "period": "current_month",
  "limit": 200,
  "remaining": 155
}
```

### Get AI Limits
```
GET /ai/limits/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "monthly_limit": 200,
  "daily_limit": 20,
  "per_request_cost": 1,
  "plan": "PREMIUM",
  "resets_at": "2026-03-01T00:00:00Z"
}
```

### Get Smart Suggestions
```
GET /ai/smart-suggestions/
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `event_type` (optional)
- `context` (optional)

**Response:** `200 OK`
```json
{
  "suggestions": {
    "venue_ideas": ["Beach", "Garden", "Ballroom"],
    "decoration_tips": ["Use fairy lights", "Floral centerpieces"],
    "timeline": {
      "6_months_before": ["Book venue", "Send save-the-dates"],
      "3_months_before": ["Order invitations", "Finalize menu"]
    }
  }
}
```

---

## 6. Admin Dashboard

**Base Path:** `/api/v1/admin-dashboard/`
**Required:** Admin/Staff permissions

### Get Dashboard Stats
```
GET /admin-dashboard/dashboard/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`
```json
{
  "total_users": 1250,
  "active_users": 890,
  "pending_approvals": 12,
  "total_orders": 456,
  "revenue": {
    "today": 5000.00,
    "this_month": 125000.00,
    "this_year": 850000.00
  },
  "recent_activity": [...]
}
```

### Get Pending Approvals
```
GET /admin-dashboard/approvals/pending/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`
```json
[
  {
    "user_id": "uuid",
    "username": "johndoe",
    "requested_plan": "PREMIUM",
    "current_plan": "FREE",
    "requested_at": "2026-02-20T10:00:00Z"
  }
]
```

### Get Recent Approvals
```
GET /admin-dashboard/approvals/recent/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`

### List All Users
```
GET /admin-dashboard/users/
Authorization: Bearer {admin_access_token}
```

**Query Parameters:**
- `status` (optional): active, inactive, pending
- `plan` (optional): Plan code
- `search` (optional): Search by name/email/phone

**Response:** `200 OK`

### List Pending Users
```
GET /admin-dashboard/users/pending/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`

### Get User Detail
```
GET /admin-dashboard/users/{user_id}/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "username": "johndoe",
  "email": "john@example.com",
  "phone": "+919876543210",
  "current_plan": "PREMIUM",
  "plan_status": "active",
  "invitations_count": 5,
  "total_orders": 2,
  "total_spent": 1998.00,
  "registered_at": "2026-01-15T10:00:00Z",
  "last_login": "2026-02-25T15:30:00Z",
  "admin_notes": "VIP customer"
}
```

### Approve User Plan
```
POST /admin-dashboard/users/{user_id}/approve/
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "plan": "PREMIUM",
  "notes": "Approved for promotional offer"
}
```

**Response:** `200 OK`

### Reject User Plan
```
POST /admin-dashboard/users/{user_id}/reject/
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "reason": "Insufficient documentation"
}
```

**Response:** `200 OK`

### Update User Notes
```
POST /admin-dashboard/users/{user_id}/notes/
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "notes": "Important customer - provide priority support"
}
```

**Response:** `200 OK`

### Grant Additional Links
```
POST /admin-dashboard/users/{user_id}/grant-links/
Authorization: Bearer {admin_access_token}
```

**Request Body:**
```json
{
  "additional_links": 10,
  "reason": "Promotional bonus"
}
```

**Response:** `200 OK`

### List Notifications
```
GET /admin-dashboard/notifications/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "type": "plan_request",
    "title": "New plan request",
    "message": "johndoe requested PREMIUM plan",
    "is_read": false,
    "created_at": "2026-02-25T10:00:00Z",
    "link": "/admin/users/uuid"
  }
]
```

### Mark Notification as Read
```
POST /admin-dashboard/notifications/{notification_id}/read/
Authorization: Bearer {admin_access_token}
```

**Response:** `200 OK`

---

## 7. Public Endpoints

**Base Path:** `/api/invite/`
**Authentication:** Not required

### View Public Invitation
```
GET /api/invite/{slug}/
```

**Example:** `GET /api/invite/john-jane-wedding/`

**Response:** `200 OK`
```json
{
  "slug": "john-jane-wedding",
  "title": "John & Jane's Wedding",
  "event_type": "wedding",
  "bride_name": "Jane Doe",
  "groom_name": "John Smith",
  "event_date": "2026-12-31",
  "event_time": "18:00",
  "venue_name": "Grand Hotel",
  "venue_address": "123 Main St",
  "message": "Join us for our special day!",
  "template_preview": "https://example.com/template-preview",
  "custom_colors": {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4"
  }
}
```

### Check Guest Status
```
GET /api/invite/{slug}/check/?phone={phone}
```

**Query Parameters:**
- `phone`: Guest phone number

**Response:** `200 OK`
```json
{
  "registered": true,
  "guest": {
    "name": "Alice Johnson",
    "rsvp_status": "confirmed",
    "guests_count": 2
  }
}
```

### Register Guest
```
POST /api/invite/{slug}/register/
```

**Request Body:**
```json
{
  "name": "Alice Johnson",
  "phone": "+919876543210",
  "email": "alice@example.com",
  "guests_count": 2,
  "message": "Looking forward to your special day!"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "name": "Alice Johnson",
  "rsvp_status": "pending",
  "message": "Registration successful"
}
```

### Update RSVP
```
POST /api/invite/{slug}/rsvp/
```

**Request Body:**
```json
{
  "phone": "+919876543210",
  "rsvp_status": "confirmed",
  "guests_count": 2,
  "dietary_preferences": "Vegetarian",
  "special_requests": "Wheelchair accessible seating"
}
```

**Response:** `200 OK`

---

## 8. Payment

**Base Path:** `/api/v1/invitations/`

### Create Razorpay Order
```
POST /invitations/orders/{order_id}/payment/razorpay/create/
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "razorpay_order_id": "order_xxx",
  "amount": 99900,
  "currency": "INR",
  "key": "rzp_test_xxx"
}
```

### Verify Razorpay Payment
```
POST /invitations/payment/razorpay/verify/
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "razorpay_order_id": "order_xxx",
  "razorpay_payment_id": "pay_xxx",
  "razorpay_signature": "signature_xxx",
  "order_id": "uuid"
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Payment verified successfully",
  "order": {
    "id": "uuid",
    "status": "completed"
  }
}
```

### Razorpay Webhook
```
POST /invitations/payment/razorpay/webhook/
```

**Headers:**
- `X-Razorpay-Signature`: Webhook signature

**Request Body:** (Razorpay webhook payload)

**Response:** `200 OK`

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "details": {
    "field": ["Error message"]
  }
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 429 Too Many Requests
```json
{
  "detail": "Request was throttled. Expected available in 60 seconds."
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

## Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer {access_token}
```

Tokens are obtained from:
- `/auth/register/` - Returns access and refresh tokens
- `/auth/login/` - Returns access and refresh tokens
- `/auth/refresh/` - Returns new access token

Access tokens expire after 24 hours.
Refresh tokens expire after 30 days.

---

## Rate Limiting

- **Authenticated users:** 1000 requests per hour
- **Anonymous users:** 100 requests per hour
- **AI endpoints:** Based on plan limits

---

## Pagination

List endpoints support pagination:

**Query Parameters:**
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 150,
  "next": "https://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

---

## Testing

Use the provided test script:

```bash
# Install dependencies
pip install requests colorama

# Run tests
python test_all_apis.py
```

Or use curl:

```bash
# Test API root
curl http://localhost:8000/api/v1/

# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "username": "test", "password": "Test123", "password_confirm": "Test123"}'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone": "+919876543210", "password": "Test123"}'
```

---

## WebSocket Endpoints

Real-time features are available via WebSocket connections:

### Admin Dashboard Notifications
```
ws://localhost:8000/ws/admin-dashboard/
```

**Authentication:** Include token as query parameter:
```
ws://localhost:8000/ws/admin-dashboard/?token={access_token}
```

**Messages:**
```json
{
  "type": "notification",
  "data": {
    "title": "New plan request",
    "message": "johndoe requested PREMIUM plan"
  }
}
```

---

## API Versioning

Current version: **v1**

Future versions will be available at:
- `/api/v2/...`
- `/api/v3/...`

v1 will be maintained for backward compatibility.

---

## Support

For API support:
- Email: support@example.com
- Documentation: https://docs.example.com
- GitHub Issues: https://github.com/syedgazanfar/invitation/issues

---

**Last Updated:** February 26, 2026
**Total Endpoints:** 75+
