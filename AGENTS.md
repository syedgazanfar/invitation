# AGENTS.md - Wedding Invitations Platform

This document provides essential information for AI coding agents working on this project.

## Project Overview

This is an **AI-Enhanced Digital Wedding Invitations Platform** - a full-stack web application for creating and managing personalized digital wedding invitations.

### Core Features
- User registration and authentication with JWT
- Multi-tier pricing plans (Basic, Premium, Luxury)
- Country-aware pricing with tax and service fee calculations
- Wedding event creation and management
- Template selection (60 templates total, 20 per plan)
- Unique invitation URL generation with 5-day validity
- Guest access control with per-plan limits
- Personalized guest experience with animations
- Organizer dashboard with analytics and CSV export
- Admin dashboard for user management and approvals

## Technology Stack

This project has **two separate implementations**:

### 1. Node.js Stack (Primary Development)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript |
| Styling | Tailwind CSS, PostCSS |
| State Management | Zustand |
| Animation | GSAP |
| Backend | NestJS 10, TypeScript |
| Database | PostgreSQL 15 |
| ORM | Prisma 5 |
| Authentication | JWT (Access + Refresh tokens), Passport |
| Password Hashing | bcrypt |
| Validation | class-validator, class-transformer |

### 2. Python/Django Stack (Docker Production)

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Material-UI v5 |
| Routing | React Router v6 |
| State Management | Zustand |
| Animation | Framer Motion, GSAP |
| Backend | Django 4.2, Django REST Framework |
| Database | PostgreSQL 15 |
| Cache/Queue | Redis 7, Celery 5 |
| Authentication | JWT (SimpleJWT) |
| File Storage | AWS S3 (boto3), WhiteNoise |
| Payment | Razorpay |
| Testing | pytest, locust |

## Project Structure

```
Invitation/
├── apps/
│   ├── backend/              # NestJS API server (Node.js stack)
│   │   ├── prisma/
│   │   │   ├── schema.prisma    # Database schema
│   │   │   ├── seed.ts          # Database seed script
│   │   │   └── migrations/
│   │   ├── src/
│   │   │   ├── main.ts          # Application entry
│   │   │   ├── app.module.ts    # Root module
│   │   │   ├── auth/            # Authentication module
│   │   │   ├── users/           # User management
│   │   │   ├── events/          # Event CRUD
│   │   │   ├── plans/           # Pricing plans
│   │   │   ├── templates/       # Invitation templates
│   │   │   ├── invitations/     # Public invitation handlers
│   │   │   └── prisma/          # Prisma service
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   └── Dockerfile
│   │
│   ├── backend-python/       # Django API server (Python stack)
│   │   ├── src/
│   │   │   ├── apps/
│   │   │   │   ├── accounts/        # User authentication
│   │   │   │   ├── admin_dashboard/ # Admin management
│   │   │   │   ├── invitations/     # Events & invitations
│   │   │   │   └── plans/           # Pricing plans
│   │   │   ├── config/              # Django settings
│   │   │   └── manage.py
│   │   ├── media/               # User-uploaded files
│   │   ├── static/              # Static files
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── frontend/             # Next.js web application
│   │   ├── src/
│   │   │   ├── app/             # App Router pages
│   │   │   ├── lib/
│   │   │   │   └── api.ts       # API client with interceptors
│   │   │   ├── store/
│   │   │   │   └── authStore.ts # Zustand auth state
│   │   │   └── types/
│   │   │       └── index.ts     # TypeScript types
│   │   ├── public/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── next.config.js
│   │   ├── tailwind.config.js
│   │   └── Dockerfile
│   │
│   ├── frontend-mui/         # React + Material-UI frontend
│   │   ├── src/
│   │   ├── public/
│   │   ├── package.json
│   │   └── Dockerfile
│   │
│   └── frontend-static/      # Static HTML frontend (Nginx)
│       ├── index.html
│       ├── login.html
│       ├── register.html
│       └── ...
│
├── nginx/
│   └── nginx.conf            # Nginx configuration
│
├── package.json              # Root workspace configuration
├── docker-compose.yml        # Docker services (Python stack)
├── start.sh / start.bat      # Production start scripts
├── quick-start.sh / .bat     # Quick start scripts
└── *.md                      # Documentation files
```

## Ports and URLs

### Node.js Stack (Development)

| Service | Port | URL |
|---------|------|-----|
| Frontend | 9300 | http://localhost:9300 |
| Backend API | 9301 | http://localhost:9301/api |
| PostgreSQL | 5432 | localhost:5432 |

### Python/Django Stack (Docker)

| Service | Port | URL |
|---------|------|-----|
| Frontend (Nginx) | 80 | http://localhost |
| Backend API | 8000 | http://localhost:8000 |
| Admin Panel | 8000 | http://localhost:8000/admin |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |

## Build and Development Commands

### Node.js Stack

#### Root-level Commands (from project root)

```bash
# Install all dependencies (root + all workspaces)
npm install

# Development - run both frontend and backend
npm run dev

# Individual development
npm run dev:backend      # Backend only (port 9301)
npm run dev:frontend     # Frontend only (port 9300)

# Build for production
npm run build            # Build both
npm run build:backend    # Build backend only
npm run build:frontend   # Build frontend only

# Database operations
npm run prisma:generate  # Generate Prisma client
npm run prisma:migrate   # Run migrations
npm run prisma:studio    # Open Prisma Studio
npm run seed             # Seed database
```

#### Backend-specific Commands (from apps/backend/)

```bash
npm run build           # Build NestJS app
npm run dev             # Start with watch mode
npm run start:prod      # Start production build
npm run format          # Format with Prettier
```

#### Frontend-specific Commands (from apps/frontend/)

```bash
npm run dev             # Start Next.js dev server
npm run build           # Build Next.js app
npm run start           # Start production build
npm run lint            # Run ESLint
```

### Python/Django Stack

```bash
# Start all services (recommended)
./start.sh              # Linux/Mac
start.bat               # Windows

# Or use Docker Compose directly
docker-compose up -d    # Start all services
docker-compose down     # Stop all services
docker-compose down -v  # Stop and remove volumes

# Run migrations
docker-compose exec backend python src/manage.py migrate

# Seed database
docker-compose exec backend python src/manage.py seed_data

# Create admin user
docker-compose exec backend python src/manage.py createsuperuser

# View logs
docker-compose logs -f [service]
```

## Environment Configuration

### Node.js Backend (.env in apps/backend/)

```env
# Database
DATABASE_URL="postgresql://postgres:password@localhost:5432/wedding_invitations?schema=public"

# JWT Authentication
JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"
JWT_REFRESH_SECRET="your-super-secret-refresh-key-change-this-in-production"
JWT_EXPIRATION="15m"
JWT_REFRESH_EXPIRATION="7d"

# Application
NODE_ENV="development"
PORT=9301
FRONTEND_URL="http://localhost:9300"
CORS_ORIGINS="http://localhost:9300"
```

### Node.js Frontend (.env.local in apps/frontend/)

```env
NEXT_PUBLIC_API_URL=http://localhost:9301/api
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### Python Backend (.env in apps/backend-python/)

```env
SECRET_KEY=your-secret-key-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.01,*
DB_NAME=invitation_platform
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.01,http://localhost:3000
FRONTEND_URL=http://localhost
FINGERPRINT_SALT=your-secret-salt
```

## Database Schema

Key entities (see `apps/backend/prisma/schema.prisma` for complete Node.js schema):

- **User**: Organizers who create wedding events
- **Plan**: Pricing plans (BASIC, PREMIUM, LUXURY)
- **CountryPricing**: Country-specific pricing configuration
- **Template**: Wedding invitation templates (60 total)
- **Event**: Wedding events created by users (DRAFT → ACTIVE → EXPIRED)
- **Payment**: Payment records for events
- **Guest**: People who view invitations
- **RefreshToken**: JWT refresh token storage

### Seeded Data

The database seed creates:
- 3 Plans (Basic, Premium, Luxury)
- 10 Country pricing configurations (US, IN, GB, CA, AU, DE, FR, JP, BR, MX)
- 60 Templates (20 per plan)

## API Architecture (Node.js Stack)

### Base URL
`http://localhost:9301/api`

### Response Format
All endpoints return responses in this format:
```json
{
  "success": true,
  "data": { ... }
}
```

### Authentication
Protected endpoints require JWT Bearer token:
```
Authorization: Bearer <access-token>
```

### Key Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /auth/signup | POST | No | User registration |
| /auth/login | POST | No | User login |
| /auth/refresh | POST | No | Refresh access token |
| /auth/logout | POST | Yes | User logout |
| /users/profile | GET/PUT | Yes | User profile |
| /plans | GET | No | List all plans |
| /plans/pricing | GET | No | Country-specific pricing |
| /templates | GET | No | List templates |
| /events | GET/POST | Yes | List/create events |
| /events/:id | GET/PUT | Yes | Get/update event |
| /events/:id/activate | POST | Yes | Activate event |
| /events/:id/guests | GET | Yes | List guests |
| /events/:id/guests/export | GET | Yes | Export CSV |
| /invite/:slug | GET | No | Get invitation metadata |
| /invite/:slug/register-guest | POST | No | Register guest |

See `API_DOCUMENTATION.md` for complete documentation.

## Code Style Guidelines

### Backend (NestJS)

- **Module Structure**: Each feature is a module with controller, service, and DTOs
- **DTOs**: Use class-validator decorators for validation
- **Naming**: PascalCase for classes, camelCase for variables/functions
- **Imports**: Use path alias `@/*` for src directory
- **Error Handling**: Use NestJS built-in exceptions (NotFoundException, BadRequestException, etc.)
- **Services**: Keep business logic in services, controllers handle HTTP layer

Example module structure:
```
src/feature/
├── feature.module.ts
├── feature.controller.ts
├── feature.service.ts
├── dto/
│   ├── create-feature.dto.ts
│   └── update-feature.dto.ts
└── guards/ (if needed)
```

### Backend (Django)

- **App Structure**: Each feature is a Django app with models, views, serializers, urls
- **Models**: Use Django ORM with type hints where possible
- **Views**: Use Django REST Framework viewsets and API views
- **Serializers**: Use DRF serializers for data validation
- **URLs**: Separate URL configs per app, included in main urls.py

Example app structure:
```
apps/feature/
├── models.py
├── views.py
├── serializers.py
├── urls.py
├── admin.py
├── tests.py
└── management/
    └── commands/
```

### Frontend (Next.js)

- **App Router**: Uses Next.js 14 App Router (not pages router)
- **Components**: Server components by default, `'use client'` for client components
- **Styling**: Tailwind CSS utility classes
- **State**: Zustand for global state, React hooks for local state
- **API Calls**: Use `lib/api.ts` with axios interceptors for auth
- **Types**: Define types in `types/index.ts`

### Frontend (React + MUI)

- **Components**: Functional components with hooks
- **Styling**: Material-UI components and theme
- **State**: Zustand for global state
- **Routing**: React Router v6
- **API**: Axios with interceptors

### TypeScript

- Strict mode enabled in frontend, relaxed in backend (NestJS defaults)
- Use explicit types for function parameters and return types
- Use enums for fixed values (PlanCode, EventStatus, PaymentStatus)

## Testing Instructions

### Manual Testing

1. **Authentication**: Sign up → Login → Access protected routes
2. **Event Creation**: Create event → Select plan → Choose template → Payment → Activate
3. **Guest Flow**: Access invitation URL → Enter name → View invitation
4. **Dashboard**: View events → Check guest stats → Export CSV

### Quick API Test (Node.js)

```bash
# Test plans endpoint
curl http://localhost:9301/api/plans

# Test pricing
curl "http://localhost:9301/api/plans/pricing?country=US"

# Test templates
curl "http://localhost:9301/api/templates?plan=BASIC"
```

### Plan Limits

| Plan | Regular Guests | Test Guests | Total |
|------|---------------|-------------|-------|
| Basic | 40 | 5 | 45 |
| Premium | 100 | 10 | 110 |
| Luxury | 150 | 20 | 170 |

See `TESTING_GUIDE.md` for comprehensive testing scenarios.

## Security Considerations

### Implemented
- Password hashing with bcrypt (Node.js) / Django PBKDF2 (Python)
- JWT-based authentication with access and refresh tokens
- Input validation via class-validator (Node.js) / DRF serializers (Python)
- Authorization guards for protected resources
- SQL injection prevention via Prisma ORM / Django ORM
- CORS configuration
- User isolation (users can only access their own events)
- Fingerprinting for guest tracking (Python stack)

### JWT Token Configuration
- Access token: 15 minutes expiration
- Refresh token: 7 days expiration
- Refresh tokens stored in database for revocation

### Required for Production
- Change default JWT secrets
- Use HTTPS
- Implement rate limiting
- Add request logging and monitoring
- Regular dependency updates
- Database connection pooling
- Set `DEBUG=False` in Python/Django

## Common Issues and Fixes

### TypeScript Build Errors

**Issue**: `Argument of type 'X' is not assignable to parameter of type 'never'`

**Fix**: Ensure arrays have proper type annotations:
```typescript
// Bad
const templates = [];

// Good
const templates: Array<{ planCode: PlanCode; name: string; }> = [];
```

### Docker Build Failures

```bash
# Clear all caches and rebuild
docker-compose down -v
docker system prune -a
npm install
docker-compose build --no-cache
docker-compose up -d
```

### Port Conflicts

```bash
# Kill processes on ports
npx kill-port 9300
npx kill-port 9301
```

### Database Connection Issues

```bash
# Node.js stack
npx prisma migrate reset
npm run seed

# Python stack
docker-compose exec backend python src/manage.py migrate
docker-compose exec backend python src/manage.py seed_data
```

See `TROUBLESHOOTING.md` for more details.

## Development Workflow

### Node.js Stack

1. **New Feature Development**:
   - Backend: Define Prisma schema → Create DTOs → Implement service → Add controller
   - Frontend: Create/update pages → Add API calls → Update state management

2. **Database Changes**:
   - Modify `schema.prisma`
   - Run `npm run prisma:migrate`
   - Update seed script if needed
   - Run `npm run seed`

3. **Adding a New API Endpoint**:
   - Create/update DTO in `apps/backend/src/feature/dto/`
   - Add method to service
   - Add route to controller
   - Update frontend API client in `apps/frontend/src/lib/api.ts`

### Python/Django Stack

1. **New Feature Development**:
   - Backend: Create/update models → Create serializers → Add views → Update URLs
   - Frontend: Create React components → Add API calls → Update state

2. **Database Changes**:
   - Modify `apps/*/models.py`
   - Run `docker-compose exec backend python src/manage.py makemigrations`
   - Run `docker-compose exec backend python src/manage.py migrate`

3. **Adding Admin Functionality**:
   - Register models in `apps/*/admin.py`
   - Or create custom admin dashboard views in `apps/admin_dashboard/`

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `SETUP.md` | Detailed setup instructions |
| `API_DOCUMENTATION.md` | Complete API reference |
| `TESTING_GUIDE.md` | Testing scenarios and checklist |
| `TROUBLESHOOTING.md` | Common issues and solutions |
| `BUILD_FIXES.md` | Build issue resolutions |
| `PORT_CHANGES.md` | Port configuration details |
| `DOCKER_BUILD_READY.md` | Docker build status |
| `ARCHITECTURE.md` | System architecture overview |
| `ADMIN_GUIDE.md` | Admin panel usage guide |

## Dependencies to Know

### Node.js Backend
- `@nestjs/*`: NestJS framework
- `@prisma/client`: Prisma ORM
- `passport`, `passport-jwt`: JWT authentication
- `bcrypt`: Password hashing
- `class-validator`, `class-transformer`: Validation
- `nanoid`: Unique ID generation

### Node.js Frontend
- `next`: Next.js framework
- `react`, `react-dom`: React
- `axios`: HTTP client
- `zustand`: State management
- `gsap`: Animations
- `tailwindcss`: Styling

### Python Backend
- `Django`, `djangorestframework`: Web framework
- `djangorestframework-simplejwt`: JWT authentication
- `psycopg2-binary`: PostgreSQL adapter
- `redis`, `celery`: Cache and task queue
- `Pillow`: Image processing
- `boto3`, `django-storages`: AWS S3 storage
- `razorpay`: Payment gateway
- `nanoid`: Unique ID generation

### Python Frontend (MUI)
- `@mui/material`, `@mui/icons-material`: Material-UI components
- `@emotion/react`, `@emotion/styled`: CSS-in-JS
- `react-router-dom`: Routing
- `framer-motion`: Animations
- `recharts`: Charts
- `zustand`: State management

## License

Proprietary - All rights reserved.
