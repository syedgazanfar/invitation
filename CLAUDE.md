# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Digital Wedding Invitations Platform** for the Indian market - A production-ready Django + React application for creating and managing personalized digital event invitations (weddings, birthdays, parties, religious festivals).

**Key Business Logic:**
- Multi-tier pricing (Basic/Premium/Luxury) with INR-based pricing
- Admin approval workflow for orders (PENDING_PAYMENT → PENDING_APPROVAL → APPROVED)
- Device fingerprinting anti-fraud system to prevent duplicate guest counts
- Separate regular and test link quotas per plan
- 15-day invitation validity from approval date (not creation date)
- Razorpay payment integration

## Technology Stack

**Backend:** Django 4.2 + Django REST Framework + PostgreSQL 15 + Redis + Celery
**Frontend:** React 18 + TypeScript + Material-UI v5 + Zustand
**Real-time:** Django Channels (WebSocket)
**Deployment:** Docker + Docker Compose

## Project Structure

```
apps/
├── backend/src/
│   ├── apps/
│   │   ├── accounts/       # User management & JWT auth (service layer ✅)
│   │   ├── plans/          # Plans, orders, pricing (service layer ✅)
│   │   ├── invitations/    # Invitations & guests (service layer ✅)
│   │   ├── admin_dashboard/# Admin approval workflow (refactored ✅)
│   │   └── ai/             # AI features (refactored ✅)
│   ├── config/             # Django settings & URLs
│   └── utils/              # Shared utilities (fingerprinting, validators)
│
└── frontend/src/
    ├── components/ui/      # Reusable component library (NEW - Phase 2)
    ├── pages/Auth/         # Login, Register (refactored to use UI components)
    ├── store/              # Zustand state management
    └── theme/              # MUI theme configuration

archive/                    # Legacy implementations (NestJS, Next.js, static)
```

## Recent Architecture Changes (Phase 2 - February 2026)

### 1. Service Layer Pattern (Complete ✅)
All Django apps now use a service layer to separate business logic from views:

**Pattern:**
```python
# apps/<app>/services/<service>.py
class UserService:
    @staticmethod
    def register_user(validated_data):
        # Business logic here
        return user, tokens

    @staticmethod
    def login_user(phone, password):
        # Authentication logic
        return user, tokens

# apps/<app>/views.py (thin controllers)
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, tokens = UserService.register_user(serializer.validated_data)
        return Response(...)
```

**Service Layer Files:**
- `apps/accounts/services/auth_service.py` - Registration, login, OTP
- `apps/accounts/services/profile_service.py` - Profile management
- `apps/plans/services/plan_service.py` - Plan operations
- `apps/plans/services/order_service.py` - Order creation, payment
- `apps/invitations/services/invitation_service.py` - Invitation CRUD
- `apps/invitations/services/guest_service.py` - Guest registration (fingerprinting)

### 2. Refactored View Structure
Large view files split into modules:

**AI App:**
```
apps/ai/views/
├── __init__.py              # Exports all views
├── photo_analysis.py        # Photo upload & analysis endpoints
├── message_generation.py    # Message & hashtag generation
├── recommendations.py       # Template & style recommendations
└── usage.py                 # AI usage stats & limits
```

**Admin Dashboard:**
```
apps/admin_dashboard/views/
├── __init__.py
├── dashboard.py             # Dashboard statistics
├── approvals.py             # Order approval workflow
├── users.py                 # User management
└── notifications.py         # Notification management
```

### 3. Database Optimizations (Complete ✅)
**43 strategic indexes added** across 3 apps:
- Query performance improved 90-97%
- API response times reduced 80%
- N+1 queries eliminated with `select_related()` and `prefetch_related()`

See `DATABASE_OPTIMIZATION_COMPLETE.md` and `N+1_QUERY_FIXES_IMPLEMENTED.md` for details.

### 4. Frontend Component Library (NEW)
**11 reusable UI components** created in `apps/frontend/src/components/ui/`:

**Components:**
- `Button/LoadingButton.tsx` - Button with built-in loading spinner
- `Form/FormInput.tsx` - Text input with icon support
- `Form/PasswordInput.tsx` - Password field with show/hide toggle (internal state)
- `Form/PhoneInput.tsx` - Phone input with phone icon
- `Form/EmailInput.tsx` - Email input with email icon
- `Feedback/Alert.tsx` - Alert with auto-dismiss
- `Feedback/LoadingSpinner.tsx` - Centered loading indicator
- `Feedback/EmptyState.tsx` - No data display
- `Layout/AuthLayout.tsx` - Standard auth page layout with animation

**Usage Example:**
```tsx
import { AuthLayout, PhoneInput, PasswordInput, LoadingButton } from '@/components/ui';

<AuthLayout title="Welcome Back" subtitle="Sign in to your account">
  <PhoneInput label="Phone" name="phone" value={phone} onChange={handleChange} required />
  <PasswordInput label="Password" name="password" value={password} onChange={handleChange} required />
  <LoadingButton loading={isLoading} type="submit" fullWidth>Sign In</LoadingButton>
</AuthLayout>
```

**Benefits:** 60% code reduction in auth pages, consistent UI, faster development

## Essential Commands

### Docker Development (Recommended)

```bash
# Start all services (db, redis, backend, frontend, celery)
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down

# Clean restart (removes volumes, fresh database)
docker-compose down -v
docker-compose up -d --build
```

### Backend (Django)

```bash
# Run migrations
docker-compose exec backend python src/manage.py migrate

# Create migrations
docker-compose exec backend python src/manage.py makemigrations

# Create admin user
docker-compose exec backend python src/manage.py createsuperuser

# Seed database with test data
docker-compose exec backend python src/manage.py seed_data

# Django shell
docker-compose exec backend python src/manage.py shell

# Run tests
docker-compose exec backend python src/manage.py test

# Run specific app tests
docker-compose exec backend python src/manage.py test apps.accounts
docker-compose exec backend python src/manage.py test apps.invitations.tests.test_services

# Access backend container
docker-compose exec backend bash
```

### Frontend (React + TypeScript)

```bash
# Access frontend container
docker-compose exec frontend sh

# Install new package
docker-compose exec frontend npm install <package-name>

# Run build
docker-compose exec frontend npm run build

# Run tests
docker-compose exec frontend npm test
```

### Database

```bash
# Access PostgreSQL
docker-compose exec db psql -U postgres -d invitation_platform

# Common queries
SELECT id, user_id, status FROM plans_order WHERE status = 'PENDING_APPROVAL';
SELECT slug, regular_links_used, test_links_used FROM invitations_invitation;
SELECT name, device_fingerprint FROM invitations_guest WHERE invitation_id = 1;

# Backup database
docker-compose exec db pg_dump -U postgres invitation_platform > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres invitation_platform < backup.sql
```

## Critical Business Logic

### 1. Device Fingerprinting (Anti-Fraud)
**Location:** `apps/invitations/services/guest_service.py`

**How it works:**
1. Frontend generates fingerprint from browser characteristics (OS, fonts, canvas, WebGL)
2. Backend checks uniqueness: `(invitation_id, device_fingerprint)`
3. If exists → return existing guest data (prevent duplicate count)
4. If new → allow registration, increment counter
5. Backup check: IP + User-Agent hash for incognito mode detection

**⚠️ WARNING:** Any changes to guest registration MUST preserve fingerprint uniqueness checking. This is CRITICAL for business logic.

**Test command:**
```bash
# Test fingerprinting logic
docker-compose exec backend python src/manage.py test apps.invitations.tests.test_guest_service
```

### 2. Link Expiry (15-Day Rule)
**Invitations expire 15 days after APPROVAL, not creation.**

```python
# apps/invitations/models.py
class Invitation:
    link_expires_at = models.DateTimeField()  # Set on order approval

    def is_expired(self):
        return timezone.now() > self.link_expires_at
```

**Check in queries:** Always filter `is_active=True` AND `link_expires_at > now()`

### 3. Test vs Regular Links
**Separate quotas tracked per invitation:**
- `regular_links_used` - Counts for plan limit
- `test_links_used` - Separate test quota (usually 5)

```python
# apps/invitations/services/guest_service.py
def register_guest(invitation, guest_data, is_test_link=False):
    if is_test_link:
        if invitation.test_links_used >= invitation.granted_test_links:
            raise ValidationError("Test link limit reached")
        invitation.test_links_used += 1
    else:
        if invitation.regular_links_used >= invitation.granted_regular_links:
            raise ValidationError("Regular link limit reached")
        invitation.regular_links_used += 1
```

### 4. Order Approval Workflow
**Status flow:** PENDING_PAYMENT → PENDING_APPROVAL → APPROVED/REJECTED

```python
# Only admins can approve
# apps/admin_dashboard/services.py
def approve_order(order_id, admin_user):
    order = Order.objects.get(id=order_id)
    order.status = 'APPROVED'
    order.approved_at = timezone.now()
    order.approved_by = admin_user

    # Set invitation expiry: +15 days from approval
    invitation = order.invitations.first()
    invitation.link_expires_at = timezone.now() + timedelta(days=15)
    invitation.is_active = True
    invitation.save()

    order.save()
    return order
```

## API Structure

### Authentication Flow
```
POST /api/v1/auth/register/    # Create account
POST /api/v1/auth/login/       # Get JWT tokens
POST /api/v1/auth/refresh/     # Refresh access token
POST /api/v1/auth/logout/      # Blacklist refresh token
GET  /api/v1/auth/profile/     # Get user profile (requires JWT)
```

### Order & Invitation Flow
```
1. User registers → JWT tokens
2. POST /api/v1/invitations/orders/create/  # Create order (PENDING_PAYMENT)
3. POST /api/v1/invitations/orders/{id}/payment/razorpay/create/  # Payment
4. Razorpay webhook → Order status: PENDING_APPROVAL
5. Admin approves → Order status: APPROVED, invitation.is_active=True
6. POST /api/v1/invitations/create/  # Create invitation content
7. Share: https://app.com/invite/{slug}  # Public URL
```

### Guest Registration (Public, No Auth)
```
GET  /api/invite/{slug}/                    # View invitation
POST /api/invite/{slug}/check/              # Check if fingerprint exists
POST /api/invite/{slug}/register/           # Register guest (with fingerprint)
POST /api/invite/{slug}/rsvp/               # Update RSVP
```

## Testing

### Run All Tests
```bash
docker-compose exec backend python src/manage.py test
```

### Run Specific Tests
```bash
# Service layer tests (NEW - Phase 2)
docker-compose exec backend python src/manage.py test apps.accounts.tests.test_services
docker-compose exec backend python src/manage.py test apps.invitations.tests.test_services
docker-compose exec backend python src/manage.py test apps.plans.tests.test_services

# Integration tests
docker-compose exec backend python src/manage.py test apps.tests.test_api_integration

# API endpoint tests
python test_all_apis.py  # Comprehensive API test suite (75+ endpoints)
```

### Load Testing
```bash
cd apps/backend
locust -f locustfile.py --host=http://localhost:8000
```

## Common Development Tasks

### Adding New Service Method
```python
# 1. Add to service class
# apps/<app>/services/<service>.py
class InvitationService:
    @staticmethod
    def new_method(param):
        # Business logic
        return result

# 2. Add test
# apps/<app>/tests/test_services.py
def test_new_method(self):
    result = InvitationService.new_method(param)
    self.assertEqual(result, expected)

# 3. Use in view
# apps/<app>/views.py
from apps.<app>.services import <Service>

class SomeView(APIView):
    def post(self, request):
        result = <Service>.new_method(param)
        return Response(...)
```

### Adding Database Index
```bash
# 1. Generate migration
docker-compose exec backend python src/manage.py makemigrations --empty <app_name>

# 2. Edit migration file
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='modelname',
            index=models.Index(fields=['field1', 'field2'], name='idx_model_field1_field2'),
        ),
    ]

# 3. Apply migration
docker-compose exec backend python src/manage.py migrate
```

### Adding Frontend Component
```tsx
// 1. Create component
// apps/frontend/src/components/ui/<Category>/<ComponentName>.tsx
import React from 'react';

export interface ComponentNameProps {
  // Props with JSDoc
}

export const ComponentName: React.FC<ComponentNameProps> = (props) => {
  return <div>Component</div>;
};

// 2. Export from index
// apps/frontend/src/components/ui/<Category>/index.ts
export * from './<ComponentName>';

// 3. Export from main index
// apps/frontend/src/components/ui/index.ts
export * from './<Category>';
```

## Environment Variables

**Backend (.env in apps/backend/):**
```bash
SECRET_KEY=...                          # Django secret (50+ chars)
DEBUG=False                             # True only in development
ALLOWED_HOSTS=localhost,127.0.0.1       # Comma-separated

DB_NAME=invitation_platform
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db                              # 'db' for Docker, 'localhost' for local
DB_PORT=5432

REDIS_HOST=redis                        # 'redis' for Docker
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

FRONTEND_URL=http://localhost:3000
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080

RAZORPAY_KEY_ID=rzp_test_...           # Payment gateway
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

FINGERPRINT_SALT=your-secret-salt       # For device fingerprinting
```

## Access Points (Default Ports)

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000/api/v1/
- **Django Admin:** http://localhost:8000/admin
- **API Docs (DRF):** http://localhost:8000/api/v1/ (browsable)
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

## Important Development Notes

1. **Production Stack Only:** Use Django + React (MUI). Alternative implementations (NestJS, Next.js) are archived in `archive/` for reference.

2. **Service Layer Pattern:** All new business logic goes in service layer, not views. Views should only handle HTTP request/response.

3. **Device Fingerprinting:** NEVER bypass or remove fingerprint checks in guest registration. This prevents fraud.

4. **Link Expiry:** Always use `link_expires_at` field (set on approval), not `created_at`.

5. **Test vs Regular:** Respect `is_test_link` flag. Quotas are separate and must be tracked independently.

6. **Admin Approval:** Orders cannot be activated without admin approval. Don't modify this workflow.

7. **Database Indexes:** Use `select_related()` for ForeignKey, `prefetch_related()` for ManyToMany/reverse ForeignKey. Indexes are optimized in Phase 2.

8. **Frontend Components:** Always use components from `@/components/ui` instead of raw MUI components for consistency.

9. **API Testing:** Run `python test_all_apis.py` to test all 75+ endpoints after changes.

## Documentation

**High-Level:**
- `README.md` - Project overview & quick start
- `ARCHITECTURE.md` - Detailed system design
- `PHASE2_PLAN.md` - Recent refactoring work

**Code Quality (Phase 2):**
- `DATABASE_OPTIMIZATION_COMPLETE.md` - 43 indexes added
- `N+1_QUERY_FIXES_IMPLEMENTED.md` - Query optimization
- `FRONTEND_COMPONENT_LIBRARY_COMPLETE.md` - UI component library
- `SERVICE_TESTS_COMPLETE.md` - Service layer tests

**API:**
- `API_ENDPOINTS_DOCUMENTATION.md` - Complete API reference (75+ endpoints)
- `API_TESTING_GUIDE.md` - How to test APIs
- `API_TESTING_STATUS.md` - Current test status

**Other:**
- `TESTING_GUIDE.md` - Comprehensive test scenarios
- `TROUBLESHOOTING.md` - Common issues
- `ADMIN_GUIDE.md` - Admin dashboard usage
- `AI_FEATURES_SPECIFICATION.md` - AI features (optional)

## Quick Troubleshooting

**Port already in use:**
```bash
# Change in docker-compose.yml
ports: ["3001:3000"]  # or ["8001:8000"]
```

**Database connection failed:**
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python src/manage.py migrate
```

**Frontend not loading:**
```bash
docker-compose logs frontend
docker-compose restart frontend
```

**Backend errors:**
```bash
docker-compose logs backend
docker-compose exec backend python src/manage.py check
```

**Service layer import errors:**
```bash
# After adding new service, restart backend
docker-compose restart backend
```

## Git Workflow

This is a proprietary project. For internal development:

1. Create feature branch from `master`
2. Make changes with clear commit messages
3. Test locally with `docker-compose`
4. Run tests: `docker-compose exec backend python src/manage.py test`
5. Create pull request for review
6. Merge after approval

**Recent Major Commits (Phase 2):**
- Complete Phase 2 code quality improvements (database optimization, N+1 fixes, frontend library)
- Refactor auth pages to use component library
- All APIs checked (test infrastructure added)
