# Digital Invitation Platform - Production Ready

A complete **Digital Invitation Platform** built with Django + React-MUI that can handle **1000+ DAU**. Create beautiful animated invitations for weddings, birthdays, festivals, and special occasions.

## Features

- **Anti-Fraud Link Tracking** - Device fingerprinting prevents duplicate registrations
- **Admin Approval Workflow** - Manual payment verification and approval system
- **Animated Templates** - 8+ animation styles (Elegant, Bollywood, Royal, Traditional, etc.)
- **Plan System** - Basic (Rs. 150), Premium (Rs. 350), Luxury (Rs. 500)
- **Link Expiration** - 15 days validity from approval
- **Guest Analytics** - Track views, unique guests, RSVPs
- **CSV Export** - Download guest lists

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2, DRF, PostgreSQL, Redis, Celery |
| Frontend | React 18, TypeScript, Material-UI, Framer Motion |
| DevOps | Docker, Docker Compose, Nginx |

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone repository
cd Invitation

# 2. Create environment files
cp apps/backend-python/.env.example apps/backend-python/.env
cp apps/frontend-mui/.env.example apps/frontend-mui/.env.local

# 3. Start all services
docker-compose up -d

# 4. Run migrations
docker-compose exec backend python src/manage.py migrate

# 5. Create superuser
docker-compose exec backend python src/manage.py createsuperuser

# 6. Seed database
docker-compose exec backend python src/manage.py seed_data

# Access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Admin: http://localhost:8000/admin
```

### Manual Setup

**Backend:**
```bash
cd apps/backend-python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cd src
python manage.py migrate
python manage.py runserver
```

**Frontend:**
```bash
cd apps/frontend-mui
npm install
cp .env.example .env.local
npm start
```

## Project Structure

```
Invitation/
├── apps/
│   ├── backend-python/       # Django API
│   │   ├── src/apps/
│   │   │   ├── accounts/     # Auth & users
│   │   │   ├── plans/        # Plans & templates
│   │   │   ├── invitations/  # Orders & invitations
│   │   │   └── admin_dashboard/  # Admin APIs
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   └── frontend-mui/         # React Frontend
│       ├── src/
│       │   ├── components/   # UI components
│       │   ├── pages/        # Page components
│       │   ├── store/        # Zustand stores
│       │   └── services/     # API clients
│       ├── package.json
│       └── Dockerfile
├── docker-compose.yml
└── nginx/
```

## API Endpoints

### Public
```
GET  /api/v1/plans/              # List plans
GET  /api/v1/plans/templates/    # List templates
GET  /api/invite/<slug>/         # View invitation
POST /api/invite/<slug>/register/# Register guest
```

### Authenticated
```
POST /api/v1/auth/register/
POST /api/v1/auth/login/
GET  /api/v1/invitations/orders/
POST /api/v1/invitations/create/
GET  /api/v1/invitations/<slug>/
```

### Admin (Staff only)
```
GET  /api/v1/admin-dashboard/dashboard/
POST /api/v1/admin-dashboard/orders/<id>/approve/
POST /api/v1/admin-dashboard/orders/<id>/grant-links/
```

## Plan Details

| Plan | Regular Links | Test Links | Price | Templates |
|------|--------------|------------|-------|-----------|
| Basic | 100 | 5 | Rs. 150 | Basic only |
| Premium | 150 | 5 | Rs. 350 | Basic + Premium |
| Luxury | 200 | 5 | Rs. 500 | All templates |

## Invitation Categories

- **Wedding** - Hindu, Muslim, Christian, Sikh, Inter-faith
- **Birthday** - 1st, Kids, Sweet 16, Milestone
- **Party** - House Warming, Engagement, Anniversary
- **Festival** - Eid, Diwali, Christmas, Ramzan

## Anti-Fraud System

The platform uses **device fingerprinting** to prevent duplicate registrations:

```
Components:
- User Agent
- Screen Resolution
- Timezone Offset
- Canvas Fingerprint
- WebGL Fingerprint

Detection:
1. Check device fingerprint (primary)
2. Check IP + User Agent hash (backup)
3. Check session cookie (tertiary)
```

## Admin Workflow

```
1. User registers and selects plan
2. User creates order (PENDING_PAYMENT)
3. Admin receives order notification
4. User makes payment (manual/UPI/bank)
5. Admin verifies payment and approves
6. User can now share invitation link
7. Link expires after 15 days
```

## Animation Templates

### Available Styles
1. **Elegant** - Smooth, sophisticated
2. **Fun** - Playful, colorful
3. **Traditional** - Cultural themes
4. **Modern** - Minimal design
5. **Bollywood** - Dramatic effects
6. **Floral** - Nature-inspired
7. **Royal** - Luxurious feel
8. **Minimal** - Clean & simple

## Scaling for 1000+ DAU

- **Database**: Connection pooling + read replicas
- **Caching**: Redis for invitation pages (5min TTL)
- **CDN**: Static assets on CloudFront
- **Workers**: Celery for background tasks

## Production Checklist

- [ ] Change SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_HOSTS
- [ ] Set up HTTPS
- [ ] Configure AWS S3 for media files
- [ ] Set up monitoring/logging
- [ ] Configure backups
- [ ] Set up CI/CD pipeline

## Environment Variables

### Backend (.env)
```
SECRET_KEY=your-production-secret
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com
DB_HOST=your-db-host
DB_PASSWORD=secure-password
REDIS_URL=redis://redis:6379/0
FRONTEND_URL=https://yourdomain.com
```

### Frontend (.env.local)
```
REACT_APP_API_URL=https://api.yourdomain.com/api/v1
REACT_APP_PUBLIC_URL=https://yourdomain.com
```

## Documentation

- `ARCHITECTURE.md` - Detailed system design
- `IMPLEMENTATION_GUIDE.md` - Complete implementation guide
- `API_DOCUMENTATION.md` - API reference

## Support

For technical support, contact: support@inviteme.in

---

**Made with love in India** 

**Dream Project - Production Ready**
