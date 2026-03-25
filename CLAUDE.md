# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Digital Wedding Invitations Platform** for the Indian market — Django + React app for creating and managing personalized digital event invitations (weddings, birthdays, parties, religious festivals).

**Key Business Logic:**
- Multi-tier pricing (Basic/Premium/Luxury) with INR-based pricing
- Admin approval workflow: `PENDING_PAYMENT → PENDING_APPROVAL → APPROVED`
- Device fingerprinting anti-fraud system to prevent duplicate guest counts
- Separate regular and test link quotas per plan
- **15-day invitation validity from approval date** (not creation date — `link_expires_at` is set on approval)
- Razorpay payment integration; MSG91 for SMS/OTP

## Technology Stack

**Backend:** Django 4.2 + DRF + PostgreSQL 15 + Redis + Celery + Django Channels (WebSocket)
**Frontend:** React 18 + TypeScript + Material-UI v5 + Zustand + React Router
**AI:** OpenAI API + Google Cloud Vision + scikit-learn + OpenCV
**Payment/SMS:** Razorpay + MSG91
**Deployment:** Docker + Docker Compose + Nginx

> Note: `package.json` lists Next.js but the frontend is a React SPA with React Router — Next.js is not used.

## Project Structure

```
apps/
├── backend/src/
│   ├── apps/
│   │   ├── accounts/        # User auth, JWT, profiles, phone verification
│   │   ├── plans/           # Plans, pricing tiers, order management
│   │   ├── invitations/     # Invitations, guests, analytics, payments
│   │   ├── admin_dashboard/ # Admin workflow, WebSocket consumers
│   │   └── ai/              # Photo analysis, message gen, recommendations
│   ├── config/              # Django settings, URLs, Celery, ASGI/WSGI
│   └── utils/               # Shared fingerprinting, validators
│
└── frontend/src/
    ├── components/ui/       # Reusable component library
    ├── pages/               # Auth, Dashboard, InvitationBuilder, Admin, Invite
    ├── store/               # Zustand (authStore.ts)
    ├── services/            # api.ts, aiApi.ts (axios clients)
    ├── hooks/               # Custom React hooks
    └── types/               # TypeScript type definitions

tools/template-generator/    # Python + Jinja2 generator for 50 HTML templates
archive/                     # Legacy (NestJS, Next.js, static) — do not use
```

## Service Layer Pattern

All Django apps use a service layer. Views are thin HTTP controllers; business logic lives in `services/`:

```
apps/<app>/services/<service>.py   # Business logic (static methods)
apps/<app>/views.py                # Thin: validate → call service → Response
apps/<app>/tests/test_services.py  # Tests target service methods
```

Key service files:
- `accounts/services/` — auth_service, phone_verification_service, user_profile_service, activity_service
- `invitations/services/` — invitation_service, guest_service, order_service, payment_service, analytics_service
- `plans/services/` — plan_service, order_service
- `admin_dashboard/services.py` — approval workflow
- `ai/services/` — base_ai, photo_analysis, message_generator, recommendation

## Essential Commands

```bash
# Start all services
docker-compose up -d

# Run migrations / seed data
docker-compose exec backend python src/manage.py migrate
docker-compose exec backend python src/manage.py seed_data

# Create superuser
docker-compose exec backend python src/manage.py createsuperuser

# Run all backend tests
docker-compose exec backend python src/manage.py test

# Run specific app/service tests
docker-compose exec backend python src/manage.py test apps.accounts.tests.test_services
docker-compose exec backend python src/manage.py test apps.invitations.tests.test_services

# Comprehensive API tests (75+ endpoints)
python test_all_apis.py

# Make/apply new migrations
docker-compose exec backend python src/manage.py makemigrations
docker-compose exec backend python src/manage.py migrate

# Frontend
docker-compose exec frontend npm install <package>
docker-compose exec frontend npm run build
```

## Critical Business Logic

### Device Fingerprinting (Anti-Fraud)
**Location:** `apps/invitations/services/guest_service.py`

Uniqueness checked on `(invitation_id, device_fingerprint)`. If exists → return existing guest (no double-count). Backup: IP + User-Agent hash for incognito detection.

**⚠️ Never bypass or remove fingerprint checks in guest registration.**

### Test vs Regular Links
Two separate quotas per invitation: `regular_links_used` / `test_links_used`. The `is_test_link` flag on guest registration routes to the correct quota. Both must be tracked independently.

### Order Approval Workflow
Only admins approve orders. On approval: `invitation.link_expires_at = now() + 15 days`, `invitation.is_active = True`.

Always query active invitations with: `is_active=True` AND `link_expires_at > now()`.

## Frontend Component Library

Reusable components in `apps/frontend/src/components/ui/` — always use these instead of raw MUI components:

- `Button/LoadingButton` — button with loading spinner
- `Form/FormInput`, `PasswordInput`, `PhoneInput`, `EmailInput`
- `Feedback/Alert`, `LoadingSpinner`, `EmptyState`
- `Layout/AuthLayout`

```tsx
import { AuthLayout, PhoneInput, PasswordInput, LoadingButton } from '@/components/ui';
```

## API Structure

```
POST /api/v1/auth/register/
POST /api/v1/auth/login/
GET  /api/v1/auth/profile/

POST /api/v1/invitations/orders/create/
POST /api/v1/invitations/orders/{id}/payment/razorpay/create/
POST /api/v1/invitations/create/

# Public (no auth)
GET  /api/invite/{slug}/
POST /api/invite/{slug}/check/     # Fingerprint check
POST /api/invite/{slug}/register/  # Guest registration
POST /api/invite/{slug}/rsvp/
```

Full reference: `API_ENDPOINTS_DOCUMENTATION.md`

## Database

43 strategic indexes were added in Phase 2 (see `DATABASE_OPTIMIZATION_COMPLETE.md`). When adding queries:
- Use `select_related()` for ForeignKey fields
- Use `prefetch_related()` for ManyToMany / reverse ForeignKey

To add a new index:
```bash
docker-compose exec backend python src/manage.py makemigrations --empty <app_name>
# Edit migration to use migrations.AddIndex(...)
docker-compose exec backend python src/manage.py migrate
```

## Environment Variables

**Backend** (`apps/backend/.env`): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DB_*`, `REDIS_*`, `RAZORPAY_*`, `MSG91_*`, `FINGERPRINT_SALT`, optional `AWS_*` (S3)

**Frontend** (`apps/frontend/.env`): `REACT_APP_API_URL`, `REACT_APP_PUBLIC_URL`, `REACT_APP_ENV`

## Access Points

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin
- PostgreSQL: localhost:5432 | Redis: localhost:6379
