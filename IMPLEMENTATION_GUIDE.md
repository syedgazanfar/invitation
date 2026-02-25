# Digital Invitation Platform - Implementation Guide

## Project Overview

This is a production-ready Digital Invitation Platform built with:
- **Backend**: Django 4.2 + Django REST Framework + PostgreSQL + Redis
- **Frontend**: React 18 + TypeScript + Material-UI + Framer Motion

## Architecture Highlights

### Anti-Fraud Link Tracking System

The platform uses a sophisticated device fingerprinting system to prevent duplicate guest registrations:

```
1. Device Fingerprint Generation:
   - User Agent
   - Screen Resolution
   - Timezone Offset
   - Browser Languages
   - Canvas/WebGL Fingerprint
   - Platform

2. Duplicate Detection:
   - Primary: Device fingerprint matching
   - Backup: IP + User Agent hash
   - Tertiary: Session cookie

3. Guest Registration Flow:
   - Check fingerprint in database
   - If exists: Return existing guest (no count increment)
   - If new: Create guest record, increment count
```

### Admin Approval Workflow

```
User Registration -> Select Plan -> Create Order
      |
      v
Payment Pending (Manual)
      |
      v
Admin Approval Required
      |
      v
Approved -> Invitation Active -> Can Share Link
      |
      v
15 Days Link Validity -> Expired
```

### Plan Structure

| Plan | Regular Links | Test Links | Price | Templates |
|------|--------------|------------|-------|-----------|
| Basic | 100 | 5 | Rs. 150 | Basic only |
| Premium | 150 | 5 | Rs. 350 | Basic + Premium |
| Luxury | 200 | 5 | Rs. 500 | All templates |

## Project Structure

```
Invitation/
├── apps/
│   ├── backend-python/        # Django Backend
│   │   ├── src/
│   │   │   ├── config/        # Django settings
│   │   │   ├── apps/
│   │   │   │   ├── accounts/  # User authentication
│   │   │   │   ├── plans/     # Plans & templates
│   │   │   │   ├── invitations/  # Orders & invitations
│   │   │   │   └── admin_dashboard/  # Admin APIs
│   │   │   ├── utils/         # Utilities
│   │   │   └── manage.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── .env.example
│   │
│   └── frontend-mui/          # React Frontend
│       ├── src/
│       │   ├── components/    # React components
│       │   ├── pages/         # Page components
│       │   ├── hooks/         # Custom hooks
│       │   ├── store/         # Zustand stores
│       │   ├── services/      # API services
│       │   ├── types/         # TypeScript types
│       │   ├── theme.ts       # MUI theme
│       │   ├── App.tsx
│       │   └── index.tsx
│       ├── public/
│       ├── package.json
│       └── tsconfig.json
│
├── docker-compose.yml         # Docker orchestration
├── ARCHITECTURE.md            # Detailed architecture
└── IMPLEMENTATION_GUIDE.md    # This file
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for local development)
- Git

### Quick Start with Docker

1. **Clone and navigate**:
```bash
cd Invitation
```

2. **Environment files**:
```bash
# Backend
cp apps/backend-python/.env.example apps/backend-python/.env

# Frontend
cp apps/frontend-mui/.env.example apps/frontend-mui/.env.local
```

3. **Start with Docker**:
```bash
docker-compose up -d
```

4. **Run migrations**:
```bash
docker-compose exec backend python src/manage.py migrate
```

5. **Create superuser**:
```bash
docker-compose exec backend python src/manage.py createsuperuser
```

6. **Seed database** (plans and templates):
```bash
docker-compose exec backend python src/manage.py seed_data
```

### Manual Setup (Development)

#### Backend Setup

```bash
cd apps/backend-python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
cd src
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

#### Frontend Setup

```bash
cd apps/frontend-mui

# Install dependencies
npm install

# Copy environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm start
```

## API Endpoints

### Authentication
```
POST /api/v1/auth/register/
POST /api/v1/auth/login/
POST /api/v1/auth/logout/
POST /api/v1/auth/refresh/
GET  /api/v1/auth/profile/
PUT  /api/v1/auth/profile/
```

### Plans & Templates
```
GET /api/v1/plans/
GET /api/v1/plans/<code>/
GET /api/v1/plans/categories/list
GET /api/v1/plans/templates/all
GET /api/v1/plans/templates/<id>/
GET /api/v1/plans/templates/featured
GET /api/v1/plans/templates/by-plan/<plan_code>/
```

### Orders & Invitations (Authenticated)
```
GET  /api/v1/invitations/orders/
POST /api/v1/invitations/orders/create/
GET  /api/v1/invitations/orders/<id>/

GET  /api/v1/invitations/
POST /api/v1/invitations/create/
GET  /api/v1/invitations/<slug>/
PUT  /api/v1/invitations/<slug>/update/
GET  /api/v1/invitations/<slug>/stats/
GET  /api/v1/invitations/<slug>/guests/
GET  /api/v1/invitations/<slug>/guests/export/
```

### Public Invitation (No Auth)
```
GET  /api/invite/<slug>/
POST /api/invite/<slug>/check/
POST /api/invite/<slug>/register/
POST /api/invite/<slug>/rsvp/
```

### Admin Dashboard (Staff Only)
```
GET  /api/v1/admin-dashboard/dashboard/
GET  /api/v1/admin-dashboard/orders/
GET  /api/v1/admin-dashboard/orders/<id>/
POST /api/v1/admin-dashboard/orders/<id>/approve/
POST /api/v1/admin-dashboard/orders/<id>/reject/
POST /api/v1/admin-dashboard/orders/<id>/grant-links/
POST /api/v1/admin-dashboard/orders/<id>/payment/
GET  /api/v1/admin-dashboard/users/
POST /api/v1/admin-dashboard/users/<id>/block/
POST /api/v1/admin-dashboard/users/<id>/unblock/
GET  /api/v1/admin-dashboard/statistics/
```

## Database Schema

### Core Models

1. **User** - Extended Django user with phone number
2. **Plan** - Pricing plans (Basic, Premium, Luxury)
3. **Template** - Invitation templates with animations
4. **Order** - User orders with approval workflow
5. **Invitation** - The actual invitation with unique slug
6. **Guest** - Guest registrations with device fingerprint
7. **InvitationViewLog** - Analytics for invitation views

## Key Features

### 1. Device Fingerprinting
Prevents duplicate guest registrations by creating a unique device fingerprint.

### 2. Admin Approval Workflow
All orders require admin approval before invitations become active.

### 3. Link Expiration
Invitations expire after 15 days from approval.

### 4. Template System
Multiple animation styles with theme customization.

### 5. Real-time Statistics
Track views, unique guests, and link usage.

### 6. CSV Export
Export guest lists for offline use.

## Animation Templates

### Available Animation Types

1. **Elegant** - Smooth, sophisticated animations
2. **Fun** - Playful, colorful effects
3. **Traditional** - Classic, cultural themes
4. **Modern** - Minimal, contemporary design
5. **Bollywood** - Dramatic, film-style effects
6. **Floral** - Nature-inspired animations
7. **Royal** - Luxurious, premium feel

### Animation Configuration

Each template supports:
- Entrance animations
- Scroll-triggered effects
- Particle systems (confetti, hearts)
- Background music
- Gallery image transitions

## Production Deployment

### Docker Production

```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Scale backend
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Environment Variables

#### Backend (.env)
```
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com
DB_HOST=your-db-host
DB_PASSWORD=secure-password
REDIS_URL=redis://your-redis-host:6379/0
FRONTEND_URL=https://yourdomain.com
```

#### Frontend (.env.local)
```
REACT_APP_API_URL=https://api.yourdomain.com/api/v1
REACT_APP_PUBLIC_URL=https://yourdomain.com
```

### AWS Deployment (Recommended for India)

1. **EC2 Instance**: t3.medium (2 vCPU, 4GB RAM)
2. **RDS**: PostgreSQL db.t3.micro
3. **ElastiCache**: Redis cache.t3.micro
4. **S3**: For media file storage
5. **CloudFront**: CDN for static files
6. **Route 53**: DNS management

### Scaling Considerations

- **Database**: Use RDS read replicas for GET requests
- **Caching**: Redis for invitation pages (5min TTL)
- **CDN**: CloudFront for static assets
- **Workers**: Celery for background tasks

## Security Checklist

- [x] JWT authentication with refresh tokens
- [x] Password hashing with bcrypt
- [x] Device fingerprinting for anti-fraud
- [x] Rate limiting (100 req/min)
- [x] CORS configuration
- [x] SQL injection protection (Django ORM)
- [x] XSS protection
- [ ] HTTPS in production
- [ ] 2FA for admin accounts
- [ ] Regular dependency updates

## Testing

### Backend Tests
```bash
cd apps/backend-python/src
python manage.py test
```

### Frontend Tests
```bash
cd apps/frontend-mui
npm test
```

## Support & Maintenance

### Backup Strategy
- Daily database backups
- Weekly full system backups
- 30-day retention

### Monitoring
- Application logs: `/app/logs/`
- Database performance
- Redis memory usage
- API response times

### Updates
```bash
# Backend dependencies
pip install -U -r requirements.txt

# Frontend dependencies
npm update
```

## Next Steps

### Phase 1: Complete Frontend Pages
1. Login/Register pages
2. Dashboard pages
3. Invitation builder
4. Public invitation viewer

### Phase 2: Animation Templates
1. Wedding templates (4 variations)
2. Birthday templates (4 variations)
3. Festival templates (Diwali, Eid, Christmas)
4. Party templates

### Phase 3: Advanced Features
1. Payment gateway integration (Razorpay)
2. SMS notifications
3. Email notifications
4. WhatsApp sharing
5. Advanced analytics

### Phase 4: Mobile App
1. React Native app
2. Offline support
3. Push notifications

## Contact & Support

For technical support:
- Email: support@inviteme.in
- Phone: +91 98765 43210

---

**Made with love in India** 
