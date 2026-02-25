# API Documentation - Wedding Invitations Platform

Base URL: `http://localhost:9301/api`

All endpoints return responses in the format:
```json
{
  "success": true,
  "data": { ... }
}
```

## Authentication Endpoints

### POST /auth/signup
Register a new user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "preferredCountry": "US",
  "preferredCurrency": "USD"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "preferredCountry": "US",
      "preferredCurrency": "USD",
      "createdAt": "2024-01-01T00:00:00Z"
    },
    "accessToken": "jwt-token",
    "refreshToken": "refresh-token"
  }
}
```

### POST /auth/login
Authenticate a user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**: Same as signup

### POST /auth/logout
Logout user (requires authentication).

**Headers**: `Authorization: Bearer <access-token>`

**Response**:
```json
{
  "success": true,
  "data": { "success": true }
}
```

### POST /auth/refresh
Refresh access token.

**Request Body**:
```json
{
  "refreshToken": "refresh-token"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "accessToken": "new-access-token",
    "refreshToken": "new-refresh-token"
  }
}
```

## User Profile Endpoints

### GET /users/profile
Get current user profile (requires authentication).

**Headers**: `Authorization: Bearer <access-token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "preferredCountry": "US",
    "preferredCurrency": "USD",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### PUT /users/profile
Update user profile (requires authentication).

**Headers**: `Authorization: Bearer <access-token>`

**Request Body**:
```json
{
  "preferredCountry": "IN",
  "preferredCurrency": "INR"
}
```

**Response**: Updated user object

## Plans Endpoints

### GET /plans
List all available plans.

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "code": "BASIC",
      "name": "Basic Plan",
      "basePriceUsd": 6,
      "maxRegularGuests": 40,
      "maxTestGuests": 5,
      "totalGuestLimit": 45
    },
    {
      "code": "PREMIUM",
      "name": "Premium Plan",
      "basePriceUsd": 12,
      "maxRegularGuests": 100,
      "maxTestGuests": 10,
      "totalGuestLimit": 110
    },
    {
      "code": "LUXURY",
      "name": "Luxury Plan",
      "basePriceUsd": 20,
      "maxRegularGuests": 150,
      "maxTestGuests": 20,
      "totalGuestLimit": 170
    }
  ]
}
```

### GET /plans/pricing?country={countryCode}
Get pricing for all plans in a specific country.

**Query Parameters**:
- `country` (optional, default: "US"): Country code (US, IN, GB, CA, AU, DE, FR, JP, BR, MX)

**Response**:
```json
{
  "success": true,
  "data": {
    "countryCode": "IN",
    "countryName": "India",
    "currency": "INR",
    "plans": [
      {
        "planCode": "BASIC",
        "planName": "Basic Plan",
        "countryCode": "IN",
        "currency": "INR",
        "basePriceUsd": 6,
        "basePriceLocal": 499.5,
        "adjustedPrice": 449.55,
        "tax": 80.92,
        "serviceFee": 25,
        "finalPrice": 555.47,
        "breakdown": {
          "baseUsd": 6,
          "exchangeRate": 83.25,
          "baseLocal": 499.5,
          "multiplier": 0.9,
          "adjusted": 449.55,
          "taxRate": 0.18,
          "taxAmount": 80.92,
          "serviceFee": 25,
          "total": 555.47
        }
      }
    ]
  }
}
```

### GET /plans/countries
List all available countries with pricing.

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "countryCode": "US",
      "countryName": "United States",
      "currency": "USD"
    },
    {
      "countryCode": "IN",
      "countryName": "India",
      "currency": "INR"
    }
  ]
}
```

## Templates Endpoints

### GET /templates?plan={planCode}
List templates, optionally filtered by plan.

**Query Parameters**:
- `plan` (optional): Plan code (BASIC, PREMIUM, LUXURY)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "planCode": "BASIC",
      "name": "Classic Elegance",
      "previewUrl": "https://placeholder.cdn/templates/basic/1.jpg",
      "description": "Beautiful Classic Elegance template for your special day"
    }
  ]
}
```

## Events Endpoints (Protected)

All event endpoints require authentication.

### POST /events
Create a new wedding event (DRAFT status).

**Headers**: `Authorization: Bearer <access-token>`

**Request Body**:
```json
{
  "planCode": "PREMIUM",
  "templateId": "template-uuid",
  "brideName": "Alice",
  "groomName": "Bob",
  "weddingDate": "2024-12-31",
  "startTime": "18:00",
  "timezone": "America/Los_Angeles",
  "venueName": "Grand Ballroom",
  "address": "123 Wedding St",
  "city": "Los Angeles",
  "country": "USA",
  "lat": 34.0522,
  "lng": -118.2437,
  "message": "Join us for our special day!"
}
```

**Response**: Created event object

### PUT /events/:id
Update event (only DRAFT events can be updated).

**Headers**: `Authorization: Bearer <access-token>`

**Request Body**: Same fields as create (all optional)

**Response**: Updated event object

### POST /events/:id/payment
Process payment for event (stubbed).

**Headers**: `Authorization: Bearer <access-token>`

**Request Body**:
```json
{
  "countryCode": "US",
  "paymentMethod": "card",
  "simulateFailure": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "payment": {
      "id": "payment-uuid",
      "amount": 12.96,
      "currency": "USD",
      "status": "COMPLETED",
      "transactionId": "TXN_ABC123"
    },
    "pricing": { ... },
    "success": true
  }
}
```

### POST /events/:id/activate
Activate event after successful payment.

**Headers**: `Authorization: Bearer <access-token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "event-uuid",
    "status": "ACTIVE",
    "slug": "abc123xyz789",
    "activatedAt": "2024-01-01T00:00:00Z",
    "expiresAt": "2024-01-06T00:00:00Z",
    "inviteUrl": "http://localhost:9300/invite/abc123xyz789"
  }
}
```

### GET /events
List all events for authenticated user.

**Headers**: `Authorization: Bearer <access-token>`

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "event-uuid",
      "brideName": "Alice",
      "groomName": "Bob",
      "weddingDate": "2024-12-31",
      "status": "ACTIVE",
      "slug": "abc123",
      "plan": { ... },
      "template": { ... },
      "guestStats": {
        "regularGuests": { "current": 10, "max": 100, "remaining": 90 },
        "testGuests": { "current": 2, "max": 10, "remaining": 8 },
        "total": { "current": 12, "max": 110, "remaining": 98 }
      },
      "inviteUrl": "http://localhost:9300/invite/abc123"
    }
  ]
}
```

### GET /events/:id
Get single event details.

**Headers**: `Authorization: Bearer <access-token>`

**Response**: Single event object

### GET /events/:id/guests?page=1&limit=50
List guests for an event with pagination.

**Headers**: `Authorization: Bearer <access-token>`

**Query Parameters**:
- `page` (optional, default: 1): Page number
- `limit` (optional, default: 50): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "guests": [
      {
        "id": "guest-uuid",
        "guestName": "John Doe",
        "isTest": false,
        "ip": "192.168.1.1",
        "userAgent": "Mozilla/5.0...",
        "createdAt": "2024-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 100,
      "totalPages": 2
    }
  }
}
```

### GET /events/:id/guests/stats
Get guest statistics for an event.

**Headers**: `Authorization: Bearer <access-token>`

**Response**:
```json
{
  "success": true,
  "data": {
    "regularGuests": {
      "current": 50,
      "max": 100,
      "remaining": 50
    },
    "testGuests": {
      "current": 5,
      "max": 10,
      "remaining": 5
    },
    "total": {
      "current": 55,
      "max": 110,
      "remaining": 55
    }
  }
}
```

### GET /events/:id/guests/export
Export guests as CSV.

**Headers**: `Authorization: Bearer <access-token>`

**Response**: CSV file download

**CSV Format**:
```
Guest Name,Is Test,IP Address,User Agent,Created At
"John Doe","false","192.168.1.1","Mozilla/5.0...","2024-01-01T00:00:00Z"
```

## Invitations Endpoints (Public)

### GET /invite/:slug
Get invitation metadata (checks if active and not expired).

**Response**:
```json
{
  "success": true,
  "data": {
    "slug": "abc123",
    "status": "ACTIVE",
    "expiresAt": "2024-01-06T00:00:00Z",
    "templateName": "Royal Affair",
    "templatePreviewUrl": "https://..."
  }
}
```

**Error Responses**:
- Not found: `{"success": false, "message": "Invitation not found"}`
- Expired: `{"success": false, "message": "This invitation has expired"}`
- Not active: `{"success": false, "message": "This invitation is not active"}`

### POST /invite/:slug/register-guest
Register a guest and get full invitation details.

**Request Body**:
```json
{
  "guestName": "John Doe",
  "isTest": false
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "guest": {
      "id": "guest-uuid",
      "name": "John Doe"
    },
    "event": {
      "brideName": "Alice",
      "groomName": "Bob",
      "weddingDate": "2024-12-31",
      "startTime": "18:00",
      "timezone": "America/Los_Angeles",
      "venueName": "Grand Ballroom",
      "address": "123 Wedding St",
      "city": "Los Angeles",
      "country": "USA",
      "lat": 34.0522,
      "lng": -118.2437,
      "message": "Join us for our special day!"
    }
  }
}
```

**Error Responses**:
- Limit reached: `{"success": false, "message": "Guest limit reached (100 maximum)"}`
- Test limit reached: `{"success": false, "message": "Test guest limit reached (10 maximum)"}`

### GET /invite/:slug/slots
Get remaining guest slots for an invitation.

**Response**:
```json
{
  "success": true,
  "data": {
    "regular": {
      "used": 50,
      "max": 100,
      "remaining": 50
    },
    "test": {
      "used": 5,
      "max": 10,
      "remaining": 5
    }
  }
}
```

## Error Responses

All endpoints may return error responses in this format:

```json
{
  "success": false,
  "message": "Error description",
  "statusCode": 400,
  "error": "Bad Request"
}
```

### Common HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Duplicate resource
- `500 Internal Server Error`: Server error

## Rate Limiting

Currently no rate limiting is implemented. For production, consider:
- Authentication endpoints: 5 requests/minute
- Public endpoints: 100 requests/minute
- Authenticated endpoints: 1000 requests/minute

## Authentication

Protected endpoints require a JWT access token in the Authorization header:

```
Authorization: Bearer <access-token>
```

Tokens expire after 15 minutes. Use the refresh endpoint to get new tokens.

## Webhooks (Future Enhancement)

Consider implementing webhooks for:
- Event activated
- Guest limit reached
- Invitation expired
- Payment completed

## Pagination

Endpoints that return lists support pagination:

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)

**Response includes**:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "totalPages": 3
  }
}
```

## Filtering and Sorting

**Templates**:
- Filter by plan: `?plan=BASIC`

**Events**:
- Currently returns all user events, sorted by creation date (desc)

**Guests**:
- Currently returns all event guests, sorted by creation date (desc)
- Filter options could be added: `?isTest=true`, `?search=John`

## Best Practices

1. **Always include Authorization header** for protected endpoints
2. **Handle token refresh** automatically on 401 responses
3. **Validate input** before sending requests
4. **Handle errors gracefully** with user-friendly messages
5. **Use pagination** for large datasets
6. **Cache static data** (plans, templates, countries)
7. **Retry failed requests** with exponential backoff
8. **Log API errors** for debugging

## Example API Client (JavaScript)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:9301/api',
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refreshToken');
      const { data } = await axios.post(
        'http://localhost:9301/api/auth/refresh',
        { refreshToken }
      );
      localStorage.setItem('accessToken', data.data.accessToken);
      error.config.headers.Authorization = `Bearer ${data.data.accessToken}`;
      return api(error.config);
    }
    return Promise.reject(error);
  }
);

export default api;
```
