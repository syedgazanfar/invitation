# Setup and API Testing Guide

**Project:** Wedding Invitations Platform
**Date:** February 26, 2026
**Status:** Dependencies need to be set up

---

## Current Situation

The API testing infrastructure is complete and ready to use:
- ✅ `test_all_apis.py` - Comprehensive test script (75+ endpoints)
- ✅ `quick_api_test.bat` / `.sh` - Quick verification scripts
- ✅ `API_ENDPOINTS_DOCUMENTATION.md` - Complete API reference
- ✅ `API_TESTING_GUIDE.md` - Testing instructions

However, the backend server needs proper setup before testing can begin.

---

## Issue Encountered

When trying to run the Django server directly, we encountered:
1. **Missing Django** - Now installed ✅
2. **PostgreSQL dependency** - psycopg2-binary installation failed on Windows
3. **Missing Celery** - Required but not installed
4. **Missing Redis** - Required for channels and caching
5. **Project designed for Docker** - The docker-compose.yml shows the proper architecture

---

## Recommended Setup Method: Docker Compose

The project is designed to run with Docker Compose, which handles all dependencies automatically.

### Prerequisites:
1. **Install Docker Desktop for Windows**
   - Download: https://www.docker.com/products/docker-desktop/
   - Install and start Docker Desktop
   - Ensure WSL 2 is enabled

### Steps to Run with Docker:

```bash
# 1. Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# 2. Wait for services to be healthy (~30-60 seconds)
docker-compose ps

# 3. Verify backend is running
curl http://localhost:8000/api/v1/

# 4. Run API tests
python test_all_apis.py
```

### What Docker Compose Sets Up:

1. **PostgreSQL Database** (port 5432)
   - Database: invitation_platform
   - User: postgres
   - Password: password

2. **Redis Cache** (port 6379)
   - For caching and Celery tasks
   - For Django Channels (WebSocket)

3. **Django Backend** (port 8000)
   - Runs migrations automatically
   - Seeds initial data
   - API available at http://localhost:8000

4. **Celery Worker**
   - Background task processing
   - Email sending, notifications, etc.

5. **React Frontend** (port 3000)
   - Development server
   - Connected to backend API

---

## Alternative Method: Manual Setup (Advanced)

If you cannot use Docker, here's how to set up manually:

### 1. Install PostgreSQL

**Windows:**
```bash
# Download PostgreSQL installer
https://www.postgresql.org/download/windows/

# Or use Chocolatey
choco install postgresql

# Create database
createdb invitation_platform
```

**Mac:**
```bash
brew install postgresql@15
brew services start postgresql@15
createdb invitation_platform
```

**Linux:**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb invitation_platform
```

### 2. Install Redis

**Windows:**
```bash
# Use Windows Subsystem for Linux (WSL)
wsl sudo apt-get install redis-server
wsl redis-server

# Or use Docker for just Redis
docker run -d -p 6379:6379 redis:7-alpine
```

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

### 3. Install Python Dependencies

```bash
cd apps/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

Create `.env` file in `apps/backend/`:

```env
SECRET_KEY=your-secret-key-change-this
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=invitation_platform
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=5432

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
FRONTEND_URL=http://localhost:3000

FINGERPRINT_SALT=your-secret-salt
```

### 5. Run Migrations

```bash
cd apps/backend/src
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: create admin user
```

### 6. Start Services

**Terminal 1 - Django Server:**
```bash
cd apps/backend/src
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Celery Worker:**
```bash
cd apps/backend/src
celery -A config worker -l info
```

---

## Quick Start (Simplest Method)

If you just want to test quickly without full setup:

### Option 1: Use Docker Compose (Recommended)
```bash
# Start everything
docker-compose up

# In another terminal, run tests
python test_all_apis.py
```

### Option 2: SQLite for Testing (Limited)
```bash
# Install minimal dependencies
pip install Django djangorestframework djangorestframework-simplejwt

# Use SQLite settings (limited functionality)
cd apps/backend/src
python manage.py migrate --settings=config.settings_test
python manage.py runserver --settings=config.settings_test

# Run tests
python test_all_apis.py
```

**Note:** SQLite option will have limited functionality:
- ❌ No WebSocket support (requires Redis)
- ❌ No background tasks (requires Celery + Redis)
- ❌ No AI features (requires external APIs)
- ✅ Basic API endpoints work
- ✅ Authentication works
- ✅ CRUD operations work

---

## Current Status of Dependencies

### Installed:
- ✅ Python 3.14
- ✅ pip 26.0
- ✅ Django 6.0.2
- ✅ djangorestframework
- ✅ djangorestframework-simplejwt
- ✅ django-cors-headers
- ✅ django-filter
- ✅ Pillow
- ✅ python-dotenv
- ✅ nanoid
- ✅ phonenumbers
- ✅ requests
- ✅ pytest
- ✅ pytest-django

### Missing (needed for full functionality):
- ❌ PostgreSQL (psycopg2-binary)
- ❌ Redis
- ❌ Celery
- ❌ Channels
- ❌ Various AI/ML packages (openai, google-cloud-vision, etc.)

---

## Verification Steps

Once the server is running, verify with:

```bash
# 1. Check API root
curl http://localhost:8000/api/v1/

# Expected output:
# {
#   "name": "Wedding Invitations Platform API",
#   "version": "v1",
#   "status": "operational",
#   ...
# }

# 2. Run quick test
quick_api_test.bat  # Windows
./quick_api_test.sh  # Linux/Mac

# 3. Run comprehensive test
python test_all_apis.py
```

---

## Docker Compose Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop all services
docker-compose down

# Restart a service
docker-compose restart backend

# Run Django commands
docker-compose exec backend python src/manage.py createsuperuser
docker-compose exec backend python src/manage.py migrate

# Access PostgreSQL
docker-compose exec db psql -U postgres -d invitation_platform

# View running services
docker-compose ps

# Clean up (remove volumes)
docker-compose down -v
```

---

## Testing Workflow (Once Running)

### 1. Quick Smoke Test (1-2 minutes)
```bash
quick_api_test.bat  # or .sh
```

Verifies:
- Server is running
- API root accessible
- Plans and templates available
- User registration works
- Authentication works

### 2. Comprehensive Test (10-15 minutes)
```bash
python test_all_apis.py
```

Tests all 75+ endpoints:
- Authentication (10 endpoints)
- Plans & Templates (8 endpoints)
- Invitations & Orders (10 endpoints)
- AI Features (15+ endpoints)
- Admin Dashboard (15+ endpoints)
- Public Endpoints (4 endpoints)
- Error Handling

### 3. Manual Testing
```bash
# See API_TESTING_GUIDE.md for curl examples
# See API_ENDPOINTS_DOCUMENTATION.md for full API reference
```

---

## Troubleshooting

### Docker Issues

**Issue:** Docker not installed
```bash
# Download and install Docker Desktop
https://www.docker.com/products/docker-desktop/
```

**Issue:** Docker daemon not running
```bash
# Start Docker Desktop application
# Wait for it to fully start (whale icon in system tray)
```

**Issue:** Port already in use
```bash
# Check what's using the port
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Kill the process or change port in docker-compose.yml
```

### Database Issues

**Issue:** Database connection failed
```bash
# Check if PostgreSQL is running
docker-compose ps db

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**Issue:** Migrations not applied
```bash
# Run migrations manually
docker-compose exec backend python src/manage.py migrate

# Or rebuild
docker-compose down -v
docker-compose up --build
```

### Redis Issues

**Issue:** Redis connection failed
```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

---

## Next Steps

1. **Choose setup method:**
   - Docker Compose (recommended) ✅
   - Manual setup (advanced)
   - SQLite (limited testing)

2. **Start the server:**
   - Follow steps for chosen method

3. **Run tests:**
   - Quick test first
   - Then comprehensive test

4. **Review results:**
   - Check which endpoints pass/fail
   - Fix any issues found

5. **Document findings:**
   - Create test report
   - Note any bugs or issues

---

## Files Available

### Testing Scripts:
- `test_all_apis.py` - Comprehensive automated test
- `quick_api_test.bat` - Windows quick test
- `quick_api_test.sh` - Linux/Mac quick test

### Documentation:
- `API_ENDPOINTS_DOCUMENTATION.md` - Complete API reference
- `API_TESTING_GUIDE.md` - Testing instructions
- `API_TEST_SUMMARY.md` - Testing overview
- **`SETUP_AND_TEST_GUIDE.md`** - This file (setup guide)

### Configuration:
- `docker-compose.yml` - Docker setup
- `apps/backend/requirements.txt` - Python dependencies
- `apps/backend/.env.example` - Environment variables template

---

## Recommended Path Forward

**For fastest results:**

1. **Install Docker Desktop** (if not already installed)
2. **Start services:**
   ```bash
   docker-compose up -d
   ```
3. **Wait 60 seconds** for services to initialize
4. **Run quick test:**
   ```bash
   quick_api_test.bat
   ```
5. **If successful, run comprehensive test:**
   ```bash
   python test_all_apis.py
   ```

**Total time: ~5-10 minutes** (including Docker setup)

---

## Support

If you encounter issues:

1. Check Docker Desktop is running
2. Check logs: `docker-compose logs -f`
3. Check this guide's troubleshooting section
4. Check `API_TESTING_GUIDE.md` for more details

---

**Status:** Ready to test once environment is set up ✅
**Recommended:** Use Docker Compose for easiest setup
**Alternative:** Manual setup if Docker unavailable
**Quick option:** SQLite for basic testing (limited functionality)

