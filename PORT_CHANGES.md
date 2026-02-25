# Port Configuration Changes

All ports have been updated from default to custom ports.

## Port Mapping

| Service | Old Port | New Port |
|---------|----------|----------|
| Frontend (Next.js) | 3000 | 9300 |
| Backend (NestJS) | 3001 | 9301 |
| PostgreSQL | 5432 | 5432 (unchanged) |

## Updated Files

### Configuration Files
- `docker-compose.yml` - Updated all port mappings and environment variables
- `apps/backend/.env.example` - Updated PORT, FRONTEND_URL, CORS_ORIGINS
- `apps/frontend/.env.local.example` - Updated NEXT_PUBLIC_API_URL

### Source Code
- `apps/backend/src/main.ts` - Updated default port and CORS origin
- `apps/frontend/src/lib/api.ts` - Updated default API URL

### Documentation
- `README.md` - All URLs and port references updated
- `SETUP.md` - All URLs and port references updated
- `TESTING_GUIDE.md` - All URLs and port references updated
- `API_DOCUMENTATION.md` - Base URL and all examples updated

## Access URLs

After starting the application:

- **Frontend**: http://localhost:9300
- **Backend API**: http://localhost:9301/api
- **PostgreSQL**: localhost:5432

## Quick Start Commands

### Using Docker
```bash
docker-compose up -d
```

Access:
- Frontend: http://localhost:9300
- API: http://localhost:9301/api

### Manual Development
```bash
npm run dev
```

Backend will run on port 9301
Frontend will run on port 9300

## Environment Variables Required

### Backend (.env)
```env
PORT=9301
FRONTEND_URL="http://localhost:9300"
CORS_ORIGINS="http://localhost:9300"
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:9301/api
```

## Testing the Changes

1. Start the application:
```bash
docker-compose up -d
```

2. Verify frontend is accessible:
```bash
curl http://localhost:9300
```

3. Verify backend API is accessible:
```bash
curl http://localhost:9301/api/plans
```

4. Check Docker containers:
```bash
docker ps
```

Should show:
- wedding-invitations-frontend running on 0.0.0.0:9300->3000/tcp
- wedding-invitations-backend running on 0.0.0.0:9301->9301/tcp
- wedding-invitations-db running on 0.0.0.0:5432->5432/tcp

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Kill process on port 9300
npx kill-port 9300

# Kill process on port 9301
npx kill-port 9301
```

Or find and kill manually:

**Windows:**
```cmd
netstat -ano | findstr :9300
taskkill /PID <PID> /F

netstat -ano | findstr :9301
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:9300 | xargs kill -9
lsof -ti:9301 | xargs kill -9
```

### Updating Existing Installation

If you already have the application running on old ports:

1. Stop all services:
```bash
docker-compose down
```

2. Update environment files:
```bash
cd apps/backend
cp .env.example .env
# Edit .env with new ports

cd ../frontend
cp .env.local.example .env.local
# Edit .env.local with new API URL
```

3. Restart:
```bash
docker-compose up -d
```

## Important Notes

- The PostgreSQL port (5432) remains unchanged as it's the standard port and typically not exposed publicly
- All documentation has been updated to reflect the new ports
- No code changes were required, only configuration
- The application is fully functional on the new ports
