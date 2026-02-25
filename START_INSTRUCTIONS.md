# Wedding Invitations Platform - Quick Start Guide

## Prerequisites

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Start Docker Desktop application

## Start the Application

### Option 1: Using Docker Compose (Recommended)

Open PowerShell and run:

```powershell
# Navigate to project directory
cd "C:\Users\DELL\OneDrive\Desktop\Invitation"

# Start all services
docker-compose up -d

# View logs (optional)
docker-compose logs -f backend
```

### Option 2: Using the Start Script

```powershell
cd "C:\Users\DELL\OneDrive\Desktop\Invitation"
.\start.bat
```

## Services & URLs

Once started, access the application at:

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost | Main web application |
| **Backend API** | http://localhost:8000/api | Django REST API |
| **Admin Panel** | http://localhost:8000/admin | Django Admin |
| **API Docs** | http://localhost:8000/api/docs | Swagger/ReDoc API documentation |

## AI Features Test

Test the AI message generation:

```powershell
# Test AI endpoint
curl -X POST http://localhost:8000/api/v1/ai/generate-messages/ `
  -H "Content-Type: application/json" `
  -d '{
    "bride_name": "Priya",
    "groom_name": "Rahul",
    "event_type": "WEDDING",
    "tone": "warm",
    "details": "Childhood sweethearts"
  }'
```

## Default Login Credentials

After the database is seeded:

- **Admin User**: admin@example.com / admin123
- **Regular User**: Create via registration page

## Troubleshooting

### Port Already in Use

If ports 80 or 8000 are already in use:

```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Stop and change ports in docker-compose.yml
```

### Docker Not Running

1. Start Docker Desktop
2. Wait for the Docker engine to start (green icon)
3. Re-run the start commands

### Database Issues

```powershell
# Reset everything (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d --build
```

### View Logs

```powershell
# All services
docker-compose logs

# Specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## Stopping the Application

```powershell
docker-compose down
```

To also delete data volumes:
```powershell
docker-compose down -v
```

## Development Mode

For local development without Docker:

### Backend Only
```powershell
cd apps/backend-python
pip install -r requirements.txt
$env:PYTHONPATH="src"
$env:DJANGO_SETTINGS_MODULE="config.settings"
python src/manage.py migrate
python src/manage.py runserver
```

### Frontend Only
```powershell
cd apps/frontend-mui
npm install
npm start
```

---

**Status**: AI Features Configured ✅
- OpenAI API Key: Set
- AI Mock Mode: Disabled (Real GPT-4 responses)
- Photo Analysis: Fallback mode (colorthief - no API key needed)
