# Digital Wedding Invitations Platform

A production-ready platform for creating and managing personalized digital wedding invitations with AI-enhanced features, targeting the Indian market.

## Technology Stack

### Backend
- **Framework:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL 15
- **Cache & Queue:** Redis + Celery
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Real-time:** Django Channels (WebSocket)
- **Payment:** Razorpay Integration
- **AI Services:** Google Vision API, Custom ML Models

### Frontend
- **Framework:** React 18 + TypeScript
- **UI Library:** Material-UI (MUI) v5
- **State Management:** Zustand
- **Routing:** React Router v6
- **Animations:** Framer Motion + GSAP
- **HTTP Client:** Axios

### DevOps
- **Containerization:** Docker + Docker Compose
- **Web Server:** Nginx (reverse proxy)
- **WSGI Server:** Gunicorn
- **Deployment:** Azure-ready

## Project Structure

```
digital-invitations-platform/
├── apps/
│   ├── backend/              # Django REST API
│   │   ├── src/
│   │   │   ├── apps/         # Django applications
│   │   │   │   ├── accounts/         # User management & auth
│   │   │   │   ├── plans/            # Plans, orders, pricing
│   │   │   │   ├── invitations/      # Invitation & guest management
│   │   │   │   ├── admin_dashboard/  # Admin approval workflow
│   │   │   │   └── ai/               # AI services (optional)
│   │   │   ├── config/       # Django settings & URLs
│   │   │   └── utils/        # Shared utilities
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend/             # React + MUI application
│       ├── src/
│       │   ├── features/     # Feature-based modules
│       │   ├── shared/       # Reusable components
│       │   ├── store/        # Zustand state management
│       │   └── theme/        # MUI theme configuration
│       ├── package.json
│       └── Dockerfile.dev
├── archive/                  # Archived implementations
│   ├── backend-nestjs/       # Alternative NestJS implementation
│   ├── frontend-nextjs/      # Alternative Next.js implementation
│   └── frontend-static/      # Static HTML mockups
├── docker-compose.yml
└── README.md
```

## Core Features

### Business Model
- **Multi-tier Plans:** Basic, Premium, Luxury
- **Country-aware Pricing:** INR-based pricing with tax calculations
- **Admin Approval Workflow:** Order review before activation
- **Guest Link Tracking:** Separate regular and test link quotas
- **Anti-fraud System:** Device fingerprinting to prevent duplicate counts
- **Link Validity:** 15-day expiration from approval date

### Technical Features
- User registration with phone verification (OTP)
- Multi-state order workflow (Draft → Payment → Approval → Active)
- Razorpay payment integration with webhooks
- Device fingerprinting (SHA-256 hash from browser characteristics)
- Guest limit enforcement with fraud prevention
- Real-time admin notifications (WebSocket)
- Template-based invitation system with animations
- AI-powered features (photo analysis, message generation)
- CSV export for guest data
- Admin dashboard with statistics

### Pricing Plans

| Plan | Regular Links | Test Links | Price (INR) | Templates |
|------|--------------|------------|-------------|-----------|
| Basic | 100 | 5 | 150 | Basic Templates |
| Premium | 150 | 5 | 350 | Basic + Premium |
| Luxury | 200 | 5 | 500 | All Templates |

Link validity: 15 days from approval date

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Git

### Start Application

**Windows:**
```cmd
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

Or manually:
```bash
# Start all services
docker-compose up -d --build

# Wait for database to be ready (10 seconds)

# Run migrations
docker-compose exec backend python src/manage.py migrate

# Seed database
docker-compose exec backend python src/manage.py seed_data

# Create admin user
docker-compose exec backend python src/manage.py createsuperuser
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React application |
| Backend API | http://localhost:8000 | Django REST API |
| Admin Panel | http://localhost:8000/admin | Django admin interface |
| API Docs | http://localhost:8000/api/ | DRF browsable API |

## Development

### Backend Development

```bash
# Access backend container
docker-compose exec backend bash

# Run migrations
python src/manage.py makemigrations
python src/manage.py migrate

# Create superuser
python src/manage.py createsuperuser

# Run tests
python src/manage.py test

# Django shell
python src/manage.py shell

# Collect static files
python src/manage.py collectstatic --no-input
```

### Frontend Development

```bash
# Access frontend container
docker-compose exec frontend sh

# Install new package
npm install <package-name>

# Build for production
npm run build

# Run tests
npm test
```

### Database Management

```bash
# Access PostgreSQL
docker-compose exec db psql -U postgres -d invitation_platform

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart services
docker-compose restart backend
docker-compose restart frontend

# Stop all services
docker-compose down

# Clean restart (removes volumes)
docker-compose down -v
docker-compose up -d --build
```

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register/` - User registration
- `POST /api/auth/login/` - Login (returns JWT)
- `POST /api/auth/refresh/` - Refresh access token
- `POST /api/auth/logout/` - Logout
- `POST /api/auth/verify-phone/` - Phone verification with OTP

### User Endpoints (Authenticated)
- `GET /api/user/profile/` - Get user profile
- `PUT /api/user/profile/` - Update profile
- `GET /api/user/orders/` - List user's orders
- `POST /api/user/orders/` - Create new order

### Plans & Templates (Public)
- `GET /api/plans/` - List all plans
- `GET /api/plans/<code>/` - Get plan details
- `GET /api/templates/` - List templates (filter by `?plan=BASIC`)
- `GET /api/categories/` - List invitation categories

### Invitation Management (Authenticated)
- `POST /api/invitations/` - Create invitation
- `GET /api/invitations/<slug>/` - Get invitation details
- `PUT /api/invitations/<slug>/` - Update invitation
- `GET /api/invitations/<slug>/stats/` - Get statistics
- `GET /api/invitations/<slug>/guests/` - List guests
- `GET /api/invitations/<slug>/export/` - Export guests as CSV

### Public Guest Registration (No Auth)
- `GET /api/invite/<slug>/` - Get public invitation data
- `POST /api/invite/<slug>/register/` - Register guest name
- `GET /api/invite/<slug>/check/` - Check if already registered

### Admin Endpoints (Admin Auth Required)
- `GET /api/admin/dashboard/` - Dashboard statistics
- `GET /api/admin/orders/` - List all orders
- `POST /api/admin/orders/<id>/approve/` - Approve order
- `POST /api/admin/orders/<id>/reject/` - Reject order
- `POST /api/admin/orders/<id>/grant-links/` - Grant additional links
- `GET /api/admin/users/` - List users
- `GET /api/admin/statistics/` - Platform statistics

## Testing

### Run Backend Tests
```bash
docker-compose exec backend python src/manage.py test
```

### Load Testing
```bash
cd apps/backend
locust -f locustfile.py --host=http://localhost:8000
```

Comprehensive test scenarios available in `TESTING_GUIDE.md`

## Security Features

1. **Authentication:** JWT with access/refresh tokens
2. **Phone Verification:** OTP-based verification
3. **Device Fingerprinting:** SHA-256 hash to prevent fraud
4. **Rate Limiting:** 100 requests/minute per IP
5. **CSRF Protection:** Enabled for state-changing requests
6. **Input Validation:** DRF serializers with comprehensive validation
7. **SQL Injection Prevention:** Django ORM parameterized queries
8. **XSS Protection:** React built-in sanitization + Django escaping
9. **Payment Security:** Razorpay webhook signature verification
10. **Admin Security:** Separate admin authentication

## Production Deployment

### 📋 Pre-Deployment

Before deploying to production, complete these essential steps:

1. **Review Production Checklist**
   - Read [`PRODUCTION_CHECKLIST.md`](./PRODUCTION_CHECKLIST.md)
   - Verify all security requirements
   - Configure production environment variables
   - Test critical user flows

2. **Configure Environment**
   - Backend: Create `apps/backend/.env.production`
   - Frontend: Create `apps/frontend/.env.production`
   - See [`ENVIRONMENT_CONFIG.md`](./apps/frontend/ENVIRONMENT_CONFIG.md) for details

3. **API Testing**
   - Complete [`API_TESTING_CHECKLIST.md`](./API_TESTING_CHECKLIST.md)
   - Verify all endpoints work correctly
   - Test payment integration with Razorpay Live keys

4. **Build & Deploy**
   - Follow [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md)
   - Use [`PRODUCTION_BUILD.md`](./apps/frontend/PRODUCTION_BUILD.md) for frontend
   - Monitor deployment with checklist

### 🚀 Quick Production Deployment

**Frontend (Netlify - Recommended):**
```bash
cd apps/frontend
npm run build
# Deploy build/ directory to Netlify/Vercel
```

**Backend (Server):**
```bash
cd apps/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

See [`DEPLOYMENT_GUIDE.md`](./DEPLOYMENT_GUIDE.md) for detailed instructions.

### 🔐 Production Environment Variables

#### Backend (.env.production)

Create `.env.production` file in `apps/backend/`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invitation_db

# Django
SECRET_KEY=your-secret-key-min-50-chars
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Razorpay (Payment)
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...

# Email Service
EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# SMS (Optional)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...

# Media & Static Files
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/invitation-app/media
STATIC_URL=/static/
STATIC_ROOT=/var/www/invitation-app/staticfiles
```

#### Frontend (.env.production)

Create `.env.production` file in `apps/frontend/`:

```env
# API Configuration
REACT_APP_API_URL=https://api.yourdomain.com/api/v1
REACT_APP_PUBLIC_URL=https://yourdomain.com
REACT_APP_ENV=production

# Payment Gateway
REACT_APP_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx

# Optional: Analytics & Monitoring
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_GA_TRACKING_ID=UA-XXXXXXXXX-X
REACT_APP_ENABLE_ERROR_REPORTING=true
REACT_APP_SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

**⚠️ Security Note:** Never commit `.env.production` to git. Keep production keys secure.

See [`ENVIRONMENT_CONFIG.md`](./apps/frontend/ENVIRONMENT_CONFIG.md) for complete configuration guide.

### Azure Deployment

1. Create Azure resources:
   - Azure Container Registry (ACR)
   - Azure Database for PostgreSQL
   - Azure Cache for Redis
   - Azure Blob Storage
   - Azure App Service or Container Instances

2. Build and push images:
```bash
# Login to ACR
az acr login --name yourregistry

# Build and push backend
docker build -t yourregistry.azurecr.io/backend:latest ./apps/backend
docker push yourregistry.azurecr.io/backend:latest

# Build and push frontend
docker build -t yourregistry.azurecr.io/frontend:latest ./apps/frontend
docker push yourregistry.azurecr.io/frontend:latest
```

3. Configure App Service with environment variables
4. Set up SSL certificate
5. Configure custom domain

## Performance Optimization

1. **Database:**
   - Indexed fields: slug, device_fingerprint, status
   - Connection pooling with PgBouncer
   - Read replicas for GET requests

2. **Caching:**
   - Redis cache for public invitation pages (5 min TTL)
   - Template data cached (1 hour TTL)
   - Plan data cached (24 hours TTL)

3. **Frontend:**
   - Code splitting
   - Lazy loading components
   - Image optimization
   - CDN for static assets

4. **Background Tasks:**
   - Celery for async operations
   - Expire links daily
   - Generate statistics
   - Send notifications

## Documentation

### Development & Architecture
- `ARCHITECTURE.md` - Detailed system architecture
- `API_DOCUMENTATION.md` - Complete API reference
- `QUICK_START.md` - Quick startup guide
- `TROUBLESHOOTING.md` - Common issues and solutions
- `ADMIN_GUIDE.md` - Admin dashboard usage
- `AI_FEATURES_SPECIFICATION.md` - AI features documentation
- `CLAUDE.md` - Developer guide for Claude Code

### Testing
- `TESTING_GUIDE.md` - Comprehensive test scenarios
- `API_TESTING_CHECKLIST.md` - End-to-end API testing checklist

### Production Deployment
- `DEPLOYMENT_GUIDE.md` - **Complete deployment instructions**
- `PRODUCTION_CHECKLIST.md` - **Pre-deployment checklist**
- `PRODUCTION_BUILD.md` - **Frontend build and optimization** (in `apps/frontend/`)
- `ENVIRONMENT_CONFIG.md` - **Environment variables guide** (in `apps/frontend/`)
- `CHANGELOG.md` - **Version history and release notes**

## Troubleshooting

### Port Already in Use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Frontend
  - "8001:8000"  # Backend
```

### Database Connection Issues
```bash
docker-compose down -v
docker-compose up -d
docker-compose exec backend python src/manage.py migrate
```

### Frontend Not Loading
```bash
docker-compose logs frontend
docker-compose restart frontend
```

### Backend Errors
```bash
docker-compose logs backend
docker-compose exec backend python src/manage.py check
```

## Contributing

This is a proprietary project. For internal development:

1. Create feature branch from `master`
2. Make changes with clear commit messages
3. Test locally with `docker-compose`
4. Create pull request for review
5. Merge after approval

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Check `TROUBLESHOOTING.md`
- Review `ARCHITECTURE.md` for system design
- Check `TESTING_GUIDE.md` for test scenarios
