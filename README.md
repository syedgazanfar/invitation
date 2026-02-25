# AI-Enhanced Digital Wedding Invitations Platform

A full-stack web application for creating and managing personalized digital wedding invitations with AI-enhanced features.

## Architecture

- **Frontend**: Next.js 14 (App Router), React, TypeScript
- **Backend**: NestJS, TypeScript
- **Database**: PostgreSQL with Prisma ORM
- **Authentication**: JWT (Access + Refresh tokens)
- **API**: RESTful

## Project Structure

```
Invitation/
├── apps/
│   ├── backend/          # NestJS API server
│   └── frontend/         # Next.js web application
├── packages/
│   └── shared-types/     # Shared TypeScript types
└── docker-compose.yml    # Docker configuration
```

## Features

### Core Functionality
- User registration and authentication
- Multi-tier pricing plans (Basic, Premium, Luxury)
- Country-aware pricing with tax and service fee calculations
- Wedding event creation and management
- Template selection (20 templates per plan)
- Unique invitation URL generation with 5-day validity
- Guest access control with per-plan limits
- Personalized guest experience with animations
- Embedded Google Maps integration
- Organizer dashboard with analytics
- Guest data export (CSV)

### Pricing Plans

| Plan | Max Guests | Test Opens | Base Price (USD) |
|------|-----------|------------|------------------|
| Basic | 40 | 5 | $6 |
| Premium | 100 | 10 | $12 |
| Luxury | 150 | 20 | $20 |

Note: Base prices exclude taxes and service fees, which vary by country.

## Getting Started

### Quick Start with Docker (Recommended)

The fastest way to get started:

**Windows:**
```cmd
quick-start.bat
```

**Linux/Mac:**
```bash
chmod +x quick-start.sh
./quick-start.sh
```

Or manually:
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

Access:
- Frontend: http://localhost:9300
- Backend API: http://localhost:9301/api

### Manual Installation

Prerequisites:
- Node.js >= 18.0.0
- PostgreSQL >= 14
- npm >= 9.0.0

Steps:

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   # Backend (.env in apps/backend)
   DATABASE_URL="postgresql://user:password@localhost:5432/wedding_invitations"
   JWT_SECRET="your-secret-key"
   JWT_REFRESH_SECRET="your-refresh-secret"
   NODE_ENV="development"
   PORT=9301
   FRONTEND_URL="http://localhost:9300"

   # Frontend (.env.local in apps/frontend)
   NEXT_PUBLIC_API_URL="http://localhost:9301"
   ```

4. Run database migrations:
   ```bash
   npm run prisma:migrate
   ```

5. Seed the database:
   ```bash
   npm run seed
   ```

### Development

Run both frontend and backend:
```bash
npm run dev
```

Or run individually:
```bash
npm run dev:backend
npm run dev:frontend
```

### Database Management

```bash
# Generate Prisma client
npm run prisma:generate

# Create migration
npm run prisma:migrate

# Open Prisma Studio
npm run prisma:studio
```

## API Documentation

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login user
- `POST /auth/logout` - Logout user
- `POST /auth/refresh` - Refresh access token

### User Profile
- `GET /users/profile` - Get user profile
- `PUT /users/profile` - Update user profile

### Plans & Pricing
- `GET /plans` - List all plans
- `GET /plans/pricing?country=US` - Get country-specific pricing

### Templates
- `GET /templates?plan=BASIC` - List templates by plan

### Events (Organizer)
- `POST /events` - Create new event
- `PUT /events/:id` - Update event
- `GET /events` - List user's events
- `GET /events/:id` - Get event details
- `POST /events/:id/activate` - Activate event after payment
- `GET /events/:id/guests` - List event guests
- `GET /events/:id/guests/stats` - Get guest statistics
- `GET /events/:id/guests/export` - Export guests as CSV

### Invitations (Public)
- `GET /invite/:slug` - Get invitation metadata
- `POST /invite/:slug/register-guest` - Register guest name

## Deployment

### Using Docker

```bash
docker-compose up -d
```

### Manual Deployment

1. Build the applications:
   ```bash
   npm run build
   ```

2. Set production environment variables

3. Run database migrations on production database

4. Start the backend:
   ```bash
   cd apps/backend && npm run start:prod
   ```

5. Start the frontend:
   ```bash
   cd apps/frontend && npm run start
   ```

## Testing Strategy

Each feature is developed in sub-phases:
1. Data model and service layer
2. API endpoint implementation
3. Unit tests for business logic
4. Integration tests for APIs
5. Frontend implementation
6. End-to-end testing

## Security Considerations

- Password hashing with bcrypt
- JWT-based authentication
- Input validation on all endpoints
- Authorization guards for protected resources
- SQL injection prevention via Prisma
- XSS prevention via React's built-in sanitization
- Rate limiting on public endpoints
- CORS configuration

## License

Proprietary
