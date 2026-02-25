# Wedding Invitations Platform - Setup Guide

Complete guide for setting up and running the AI-Enhanced Digital Wedding Invitations Platform.

## Prerequisites

- Node.js >= 18.0.0
- npm >= 9.0.0
- PostgreSQL >= 14 (or use Docker)
- Git

## Quick Start with Docker

The fastest way to get started is using Docker:

```bash
# Clone the repository (if not already done)
cd Invitation

# Start all services
docker-compose up -d

# The application will be available at:
# Frontend: http://localhost:9300
# Backend API: http://localhost:9301/api
# PostgreSQL: localhost:5432
```

The Docker setup automatically:
- Creates the database
- Runs migrations
- Seeds initial data (plans, templates, country pricing)
- Starts both frontend and backend

## Manual Setup

### 1. Install Dependencies

```bash
# Install root dependencies
npm install

# This will also install dependencies for all workspaces (apps/backend, apps/frontend)
```

### 2. Database Setup

#### Option A: Using Local PostgreSQL

```bash
# Create database
createdb wedding_invitations

# Or using psql
psql -U postgres
CREATE DATABASE wedding_invitations;
\q
```

#### Option B: Using Docker for PostgreSQL only

```bash
docker run --name wedding-invitations-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=wedding_invitations \
  -p 5432:5432 \
  -d postgres:15-alpine
```

### 3. Environment Configuration

#### Backend Environment

```bash
cd apps/backend
cp .env.example .env
```

Edit `apps/backend/.env`:

```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/wedding_invitations"
JWT_SECRET="your-super-secret-jwt-key-change-this-in-production"
JWT_REFRESH_SECRET="your-super-secret-refresh-key-change-this-in-production"
JWT_EXPIRATION="15m"
JWT_REFRESH_EXPIRATION="7d"
NODE_ENV="development"
PORT=9301
FRONTEND_URL="http://localhost:9300"
CORS_ORIGINS="http://localhost:9300"
```

#### Frontend Environment

```bash
cd apps/frontend
cp .env.local.example .env.local
```

Edit `apps/frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:9301/api
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=your-google-maps-api-key
```

### 4. Database Migration and Seeding

```bash
# Generate Prisma client
npm run prisma:generate

# Run migrations
npm run prisma:migrate

# Seed the database
npm run seed
```

The seed script will create:
- 3 Plans (BASIC, PREMIUM, LUXURY)
- 10 Country pricing configurations
- 60 Templates (20 per plan)

### 5. Start Development Servers

```bash
# Start both frontend and backend concurrently
npm run dev

# Or start individually:
npm run dev:backend   # Backend on http://localhost:9301
npm run dev:frontend  # Frontend on http://localhost:9300
```

## Testing the Application

### 1. Create an Account

1. Navigate to http://localhost:9300
2. Click "Sign Up"
3. Fill in:
   - Email: test@example.com
   - Country: United States (or any country)
   - Password: testpassword123
4. Click "Sign Up"

### 2. Create a Wedding Event

1. Click "Create New Event" or navigate to http://localhost:9300/dashboard/events/new
2. Fill in wedding details:
   - Bride Name: Sarah
   - Groom Name: John
   - Wedding Date: (select a future date)
   - Start Time: 15:00
   - Venue Name: Grand Ballroom
   - Address: 123 Main Street
   - City: New York
   - Country: USA
3. Click "Next: Select Plan"

### 3. Select Plan and Template

1. Choose a plan (Basic, Premium, or Luxury)
2. Select a template from the available options
3. Review pricing (will show localized pricing based on country)
4. Click "Complete Payment" (payment is simulated)

### 4. Share Invitation URL

1. After payment, the event is activated
2. Copy the invitation URL
3. Open it in a new browser/incognito window
4. Enter a guest name to view the invitation

### 5. View Guest Analytics

1. Go back to dashboard
2. Click on your event
3. View guest statistics and list
4. Export guest data as CSV

## API Endpoints

### Authentication
- POST `/api/auth/signup` - Register new user
- POST `/api/auth/login` - Login user
- POST `/api/auth/logout` - Logout user
- POST `/api/auth/refresh` - Refresh access token

### User Profile
- GET `/api/users/profile` - Get user profile
- PUT `/api/users/profile` - Update user profile

### Plans & Pricing
- GET `/api/plans` - List all plans
- GET `/api/plans/pricing?country=US` - Get country-specific pricing
- GET `/api/plans/countries` - List available countries

### Templates
- GET `/api/templates?plan=BASIC` - List templates (filter by plan)

### Events (Protected)
- POST `/api/events` - Create new event
- PUT `/api/events/:id` - Update event
- POST `/api/events/:id/payment` - Process payment
- POST `/api/events/:id/activate` - Activate event
- GET `/api/events` - List user's events
- GET `/api/events/:id` - Get event details
- GET `/api/events/:id/guests` - List event guests
- GET `/api/events/:id/guests/stats` - Get guest statistics
- GET `/api/events/:id/guests/export` - Export guests as CSV

### Invitations (Public)
- GET `/api/invite/:slug` - Get invitation metadata
- POST `/api/invite/:slug/register-guest` - Register guest name

## Database Schema

### Key Tables

**users**
- id, email, password_hash
- preferred_country, preferred_currency
- created_at, updated_at

**plans**
- code (BASIC, PREMIUM, LUXURY)
- base_price_usd
- max_regular_guests, max_test_guests

**country_pricing**
- country_code, currency
- exchange_rate, multiplier
- tax_rate, service_fee

**templates**
- plan_code, name, preview_url

**events**
- user_id, plan_code, template_id
- bride_name, groom_name, wedding_date
- venue details (name, address, lat, lng)
- status (DRAFT, ACTIVE, EXPIRED)
- slug, activated_at, expires_at

**guests**
- event_id, guest_name, is_test
- ip, user_agent, created_at

## Features Checklist

- [x] User authentication (signup/login with JWT)
- [x] Country-aware pricing with exchange rates
- [x] Three pricing plans (Basic, Premium, Luxury)
- [x] 60 templates (20 per plan)
- [x] Event creation with multi-step form
- [x] Stubbed payment processing
- [x] Unique invitation URL generation
- [x] 5-day invitation validity
- [x] Guest limit enforcement per plan
- [x] Test vs regular guest distinction
- [x] Guest name capture before viewing
- [x] Personalized animation sequence
- [x] Embedded Google Maps
- [x] Organizer dashboard with event listing
- [x] Guest analytics and statistics
- [x] CSV export of guest data
- [x] Mobile-first responsive design
- [x] Error handling and validation
- [x] Docker support

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker ps  # if using Docker
# or
pg_isready

# Reset database
npm run prisma:migrate reset
npm run seed
```

### Port Already in Use

```bash
# Kill process on port 9300 (frontend)
npx kill-port 9300

# Kill process on port 9301 (backend)
npx kill-port 9301
```

### Prisma Client Issues

```bash
# Regenerate Prisma client
npm run prisma:generate
```

## Production Deployment

### Build for Production

```bash
# Build both apps
npm run build

# Or individually
npm run build:backend
npm run build:frontend
```

### Environment Variables for Production

Ensure all sensitive values are changed:
- DATABASE_URL (use production database)
- JWT_SECRET (strong random value)
- JWT_REFRESH_SECRET (strong random value)
- FRONTEND_URL (production domain)
- CORS_ORIGINS (production domain)

### Deploy with Docker

```bash
# Build and start production containers
docker-compose up -d --build
```

## Security Considerations

1. Change all default secrets in production
2. Use HTTPS for production
3. Enable rate limiting
4. Implement proper CORS configuration
5. Use environment-specific database credentials
6. Enable database connection pooling
7. Implement request logging and monitoring
8. Regular security updates for dependencies

## Support

For issues or questions:
1. Check this setup guide
2. Review the main README.md
3. Check API endpoint documentation above
4. Review error logs in console

## License

Proprietary
