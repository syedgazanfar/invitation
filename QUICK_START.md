# Quick Start Guide

## Step 1: Start Docker Desktop

### Windows:
1. Open Docker Desktop application
2. Wait for it to show "Docker Desktop is running" in the system tray
3. Make sure you're using Linux containers (not Windows containers)

### Mac:
1. Open Docker Desktop from Applications
2. Wait for the whale icon to show "Docker Desktop is running"

### Linux:
Docker should already be running as a service:
```bash
sudo systemctl start docker
```

---

## Step 2: Start the Application

### Option A: Using the Start Script

**Windows:**
```cmd
start.bat
```

**Mac/Linux:**
```bash
chmod +x start.sh
./start.sh
```

### Option B: Manual Steps

1. **Create environment files:**
```bash
# Windows
copy apps\backend-python\.env.example apps\backend-python\.env
copy apps\frontend-mui\.env.example apps\frontend-mui\.env.local

# Mac/Linux
cp apps/backend-python/.env.example apps/backend-python/.env
cp apps/frontend-mui/.env.example apps/frontend-mui/.env.local
```

2. **Start all services:**
```bash
docker-compose up -d --build
```

3. **Run database migrations:**
```bash
docker-compose exec backend python src/manage.py migrate
```

4. **Seed the database:**
```bash
docker-compose exec backend python src/manage.py seed_data
```

5. **Create admin user (optional):**
```bash
docker-compose exec backend python src/manage.py createsuperuser
```

---

## Step 3: Access the Application

Once started, you can access:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Main website |
| Backend API | http://localhost:8000 | API endpoints |
| Admin Panel | http://localhost:8000/admin | Django admin |

### Default Test Data:

The seed_data command creates:
- **3 Plans**: Basic (Rs.150), Premium (Rs.350), Luxury (Rs.500)
- **10 Categories**: Wedding, Birthday, Eid, Diwali, etc.
- **10+ Templates**: Various animation styles

---

## Step 4: Test the Flow

### User Registration Flow:
1. Go to http://localhost:3000
2. Click "Get Started" to register
3. Login with your credentials
4. Browse plans and select one
5. Create an order
6. (Admin approves order)
7. Create invitation
8. Share the link!

### Admin Approval Flow:
1. Go to http://localhost:8000/admin
2. Login with superuser credentials
3. Go to "Orders" 
4. Click on pending order
5. Set payment status to "Received"
6. Set order status to "Approved"

---

## Common Commands

### View logs:
```bash
docker-compose logs -f
```

### Stop all services:
```bash
docker-compose down
```

### Restart a specific service:
```bash
docker-compose restart backend
docker-compose restart frontend
```

### Access database:
```bash
docker-compose exec db psql -U postgres -d invitation_platform
```

### Run tests:
```bash
# Backend tests
docker-compose exec backend python src/manage.py test

# Load testing (install locust first)
cd apps/backend-python
locust -f locustfile.py --host=http://localhost:8000
```

---

## Troubleshooting

### Port already in use:
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Instead of 3000:3000
  - "8001:8000"  # Instead of 8000:8000
```

### Database connection issues:
```bash
docker-compose down -v  # Remove volumes
docker-compose up -d    # Start fresh
docker-compose exec backend python src/manage.py migrate
```

### Frontend not loading:
```bash
docker-compose logs frontend
```

### Backend errors:
```bash
docker-compose logs backend
```

---

## Production Deployment

### Environment Variables for Production:

Create a `.env` file in project root:
```bash
# Database
DB_PASSWORD=your_secure_password

# Security
SECRET_KEY=your_super_secret_key_min_50_chars
DEBUG=False

# Razorpay (Payment)
RAZORPAY_KEY_ID=rzp_live_...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...

# MSG91 (SMS)
MSG91_AUTH_KEY=...
MSG91_TEMPLATE_ID=...

# Frontend
FRONTEND_URL=https://yourdomain.com
```

### Deploy to AWS/Azure/GCP:
1. Push to container registry
2. Use managed database (RDS/Cloud SQL)
3. Use managed Redis (ElastiCache/MemoryStore)
4. Configure load balancer
5. Set up SSL certificates

---

## Need Help?

- Check `ARCHITECTURE.md` for system design
- Check `IMPLEMENTATION_GUIDE.md` for detailed setup
- Check `PROJECT_COMPLETION_SUMMARY.md` for feature list

**Your Digital Invitation Platform is ready to launch!** 
