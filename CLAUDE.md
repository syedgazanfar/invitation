# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Digital Wedding Invitations Platform** for the Indian market, supporting multiple event types (weddings, birthdays, parties, religious festivals). The platform uses a hybrid architecture with both Django and NestJS backends, supporting multiple frontend implementations.

**Key Business Logic:**
- Multi-tier pricing plans (Basic/Premium/Luxury) with country-specific pricing
- Admin approval workflow for orders
- Device fingerprinting system to prevent duplicate guest counts
- Guest link tracking with separate regular and test link quotas
- 15-day invitation validity from approval date

## Tech Stack

### Backends (Dual Implementation)
1. **Django Backend** (Primary - `apps/backend-python/`)
   - Framework: Django 4.2 + Django REST Framework
   - Database: PostgreSQL 15
   - Cache/Queue: Redis + Celery
   - Auth: JWT (djangorestframework-simplejwt)

2. **NestJS Backend** (Alternative - `apps/backend/`)
   - Framework: NestJS + TypeScript
   - ORM: Prisma
   - Auth: JWT + Passport

### Frontends (Multiple Implementations)
1. **React + MUI** (`apps/frontend-mui/`) - Primary, feature-complete
2. **Next.js** (`apps/frontend/`) - Alternative implementation
3. **Static HTML** (`apps/frontend-static/`) - Production deployment

### DevOps
- Docker + Docker Compose
- Nginx (reverse proxy)
- Gunicorn (WSGI server for Django)

## Quick Start Commands

### Development (Docker - Recommended)

Start all services:
```bash
# Windows
start.bat

# Mac/Linux
chmod +x start.sh
./start.sh
```

Or manually:
```bash
docker-compose up -d --build
docker-compose exec backend python src/manage.py migrate
docker-compose exec backend python src/manage.py seed_data
```

### Access Points
- Frontend: http://localhost:3000 (or port 80)
- Backend API: http://localhost:8000
- Django Admin: http://localhost:8000/admin
- Prisma Studio (NestJS): `npm run prisma:studio` in `apps/backend/`

### Common Development Commands

**Django Backend:**
```bash
# Run migrations
docker-compose exec backend python src/manage.py migrate

# Create migrations
docker-compose exec backend python src/manage.py makemigrations

# Seed database
docker-compose exec backend python src/manage.py seed_data

# Create admin user
docker-compose exec backend python src/manage.py createsuperuser

# Run tests
docker-compose exec backend python src/manage.py test

# Access Django shell
docker-compose exec backend python src/manage.py shell
```

**NestJS Backend:**
```bash
cd apps/backend

# Development
npm run dev

# Prisma
npm run prisma:generate
npm run prisma:migrate
npm run prisma:studio

# Seed
npm run seed
```

**Frontend (React + MUI):**
```bash
cd apps/frontend-mui
npm start  # Development server
npm run build  # Production build
```

### Logs and Debugging
```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart backend
docker-compose restart frontend

# Stop all
docker-compose down

# Clean restart (removes volumes)
docker-compose down -v
docker-compose up -d --build
```

## Architecture Details

### Hybrid Backend Strategy
This project maintains **two separate backend implementations** for flexibility:

1. **Django (`apps/backend-python/src/`)** - Production-ready
   - Apps: `accounts`, `plans`, `invitations`, `admin_dashboard`, `ai`
   - Entry point: `src/manage.py`
   - Settings: `src/config/settings.py`
   - URLs: `src/config/urls.py`

2. **NestJS (`apps/backend/`)** - Alternative implementation
   - Modules in `src/` directory
   - Prisma schema: `prisma/schema.prisma`
   - Entry point: `src/main.ts`

**When making changes:** Determine which backend is being used and modify accordingly. The Django backend is more feature-complete with admin dashboard and AI features.

### Core Business Models (Django)

**User Model** (`apps/backend-python/src/apps/accounts/models.py`):
- Custom user with phone number field
- `is_verified`, `is_blocked` flags

**Plan Model** (`apps/backend-python/src/apps/plans/models.py`):
- `code`: BASIC, PREMIUM, LUXURY
- `regular_links`, `test_links`: Per-plan quotas
- `price_inr`: Base price in INR

**Order Model** (Payment/Approval Workflow):
- Status: PENDING_PAYMENT → PENDING_APPROVAL → APPROVED/REJECTED/EXPIRED
- Admin approval required before activation
- Tracks `granted_regular_links`, `granted_test_links`

**Invitation Model**:
- `slug`: Unique sharing URL
- `template`: Selected from plan-specific templates
- `link_expires_at`: Set to +15 days from approval
- `is_active`: Only true after order approval
- Usage tracking: `regular_links_used`, `test_links_used`

**Guest Model** (Anti-Fraud Tracking):
- `device_fingerprint`: SHA-256 hash for duplicate prevention
- `ip_address`, `user_agent_hash`, `session_id`: Anti-fraud signals
- `is_test_link`: Separate quota tracking
- Unique constraint: `(invitation, device_fingerprint)`

### Device Fingerprinting System

**Critical anti-fraud logic** - prevents same person from counting multiple times:

1. Frontend generates fingerprint from:
   - Browser + version, OS, screen resolution
   - Installed fonts subset
   - Canvas/WebGL fingerprint
   - Timezone, language

2. Backend checks `(invitation_id, device_fingerprint)` uniqueness
3. If fingerprint exists → Show existing registration
4. If new → Allow registration, increment counter
5. Backup: IP + User-Agent hash for incognito detection

**Implementation locations:**
- Frontend: `apps/frontend-mui/src/utils/fingerprint.ts` (or equivalent)
- Backend: `apps/backend-python/src/apps/invitations/views.py` in guest registration endpoint

### Animation System

Templates have animation configurations stored in JSON:
- `animation_type`: elegant, fun, traditional, modern
- `entrance`: Hero, title, details reveal animations
- `effects`: Particles, confetti, music options
- Libraries: Framer Motion (React), GSAP (complex timelines)

**Location:** Template models in database, React components in `apps/frontend-mui/src/components/templates/`

### AI Features (Optional - Not Required)

Located in `apps/backend-python/src/apps/ai/`:
- Photo-to-theme analysis (Google Vision API)
- Template recommendation engine
- Smart message generator (GPT-4/Claude)
- Color palette extraction
- Hashtag generator
- RSVP prediction

**Note:** AI features are optional enhancements, not core functionality.

## API Structure

### Django REST API Endpoints

**Authentication:**
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - JWT login
- `POST /api/auth/refresh/` - Refresh token
- `POST /api/auth/logout/` - Logout

**Plans & Templates (Public):**
- `GET /api/plans/` - List all plans
- `GET /api/templates/` - List templates (filter by `?plan=BASIC`)
- `GET /api/categories/` - Event categories

**Invitations (Authenticated):**
- `POST /api/invitations/` - Create invitation
- `GET /api/invitations/<slug>/` - Get details
- `GET /api/invitations/<slug>/stats/` - View statistics
- `GET /api/invitations/<slug>/guests/` - List guests
- `GET /api/invitations/<slug>/export/` - Export CSV

**Public Guest Registration (No Auth):**
- `GET /api/invite/<slug>/` - Get invitation public data
- `POST /api/invite/<slug>/register/` - Register guest name
- `GET /api/invite/<slug>/check/` - Check if already registered

**Admin APIs:**
- `GET /api/admin/dashboard/` - Dashboard stats
- `GET /api/admin/orders/` - List orders
- `POST /api/admin/orders/<id>/approve/` - Approve order
- `POST /api/admin/orders/<id>/reject/` - Reject order

### NestJS API (Similar structure, different framework)
- Check `apps/backend/src/` for module structure
- Controllers define routes
- Services contain business logic
- Guards handle authentication

## Key Configuration Files

**Django:**
- `apps/backend-python/.env.example` - Environment variables template
- `apps/backend-python/src/config/settings.py` - Django settings
- `apps/backend-python/requirements.txt` - Python dependencies

**NestJS:**
- `apps/backend/.env` - Environment variables
- `apps/backend/prisma/schema.prisma` - Database schema

**Docker:**
- `docker-compose.yml` - Service orchestration (db, redis, backend, frontend, celery)
- `apps/backend-python/Dockerfile` - Django container
- `nginx/nginx.conf` - Reverse proxy config

**Frontend:**
- `apps/frontend-mui/src/theme.ts` - MUI theme configuration
- `apps/frontend-mui/src/services/api.ts` - Axios instance
- `apps/frontend-mui/src/store/` - Zustand state management

## Testing

Run test suite:
```bash
# Django tests
docker-compose exec backend python src/manage.py test

# Load testing (Locust)
cd apps/backend-python
locust -f locustfile.py --host=http://localhost:8000
```

Comprehensive test scenarios in `TESTING_GUIDE.md` including:
- Authentication flows
- Guest limit enforcement (critical)
- Device fingerprinting
- Country-specific pricing
- Admin approval workflow

## Database Access

**PostgreSQL:**
```bash
docker-compose exec db psql -U postgres -d invitation_platform
```

**Common Queries:**
```sql
-- Check orders pending approval
SELECT id, user_id, plan_id, status FROM plans_order WHERE status = 'PENDING_APPROVAL';

-- Check invitation guest counts
SELECT slug, regular_links_used, test_links_used FROM invitations_invitation;

-- View guests with fingerprints
SELECT name, device_fingerprint, is_test_link FROM invitations_guest WHERE invitation_id = <id>;
```

## Common Development Tasks

### Adding a New Event Category
1. Django: Add to `apps/backend-python/src/apps/invitations/models.py` choices
2. Run migration: `docker-compose exec backend python src/manage.py makemigrations`
3. Apply: `docker-compose exec backend python src/manage.py migrate`
4. Update seed data if needed

### Adding a New Template
1. Create template entry in database (via admin or seed script)
2. Implement React component in `apps/frontend-mui/src/components/templates/`
3. Register in template registry/router
4. Add thumbnail image to static files

### Modifying Guest Limits
1. Update plan in database or seed script
2. Guest limit logic in: `apps/backend-python/src/apps/invitations/views.py`
3. Check `can_register_guest()` method logic

### Admin Approval Workflow Changes
1. Order model: `apps/backend-python/src/apps/plans/models.py`
2. Admin views: `apps/backend-python/src/apps/admin_dashboard/`
3. Status transitions enforced in serializers/views

## Production Deployment

The project is designed for Docker deployment:

1. **Environment variables:** Set production secrets in `.env`
2. **Database:** Use managed PostgreSQL (AWS RDS, etc.)
3. **Redis:** Use managed Redis (ElastiCache, etc.)
4. **Static files:** Serve via Nginx or CDN
5. **Media uploads:** Store in S3/Cloud Storage
6. **SSL:** Configure in Nginx or load balancer

Quick production setup scripts provided:
- `quick-start.sh` / `quick-start.bat`
- `create-admin.sh` / `create-admin.bat`

## Troubleshooting

Common issues documented in `TROUBLESHOOTING.md`:

**Port conflicts:**
- Change ports in `docker-compose.yml`

**Database issues:**
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d
docker-compose exec backend python src/manage.py migrate
```

**Frontend not loading:**
```bash
docker-compose logs frontend
```

**Backend errors:**
```bash
docker-compose logs backend
```

## Important Notes for Development

1. **Dual Backend:** This project has TWO backend implementations (Django and NestJS). Check which one is active in `docker-compose.yml` before making changes.

2. **Guest Counting:** The device fingerprinting system is CRITICAL for business logic. Any changes to guest registration must preserve fingerprint uniqueness checking.

3. **Link Expiry:** Invitations expire 15 days after approval, not creation. Check `expires_at` field, not `created_at`.

4. **Test vs Regular Guests:** These have SEPARATE quotas. Always respect `is_test_link` flag.

5. **Country Pricing:** Prices vary by country with different currencies, taxes, and service fees. Use `/api/plans/pricing?country=XX` endpoint.

6. **Admin Approval Required:** Orders cannot be activated without admin approval. Status workflow must be followed.

## Documentation References

- `ARCHITECTURE.md` - Detailed system design and data models
- `API_DOCUMENTATION.md` - Complete API reference
- `TESTING_GUIDE.md` - Comprehensive test scenarios
- `QUICK_START.md` - Startup instructions
- `IMPLEMENTATION_GUIDE.md` - Detailed setup guide
- `TROUBLESHOOTING.md` - Common issues and solutions
- `AI_FEATURES_SPECIFICATION.md` - AI features (optional)
- `ADMIN_GUIDE.md` - Admin dashboard usage
