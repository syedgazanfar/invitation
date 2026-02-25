# Troubleshooting Guide

Common issues and their solutions for the Wedding Invitations Platform.

## Build Errors

### Error: TypeScript Error in seed.ts

**Error Message:**
```
prisma/seed.ts:194:22 - error TS2345: Argument of type '{ planCode: PlanCode; name: string; previewUrl: string; description: string; }' is not assignable to parameter of type 'never'.
```

**Cause:**
The `templates` array was not properly typed, causing TypeScript to infer it as `never[]`.

**Solution:**
This has been fixed in the current version. The templates array now has proper type annotation:

```typescript
const templates: Array<{
  planCode: PlanCode;
  name: string;
  previewUrl: string;
  description: string;
}> = [];
```

**If you still encounter this:**
1. Pull the latest changes
2. Ensure `apps/backend/prisma/seed.ts` has the proper type annotation
3. Rebuild: `docker-compose build --no-cache backend`

### Error: Docker Build Failed

**Error Message:**
```
failed to solve: process "/bin/sh -c npm run build" did not complete successfully: exit code: 1
```

**Solutions:**

1. **Clear Docker cache and rebuild:**
```bash
docker-compose down
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

2. **Check for TypeScript errors locally:**
```bash
cd apps/backend
npm install
npm run build
```

3. **Verify Prisma is generated:**
```bash
cd apps/backend
npx prisma generate
```

### Error: Module Not Found

**Error Message:**
```
Cannot find module '@prisma/client'
```

**Solution:**
```bash
cd apps/backend
npm install
npx prisma generate
```

For Docker:
```bash
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

### Error: Public Directory Not Found (Frontend)

**Error Message:**
```
COPY --from=builder /app/public ./public
"/app/public": not found
```

**Cause:**
The frontend public directory doesn't exist or wasn't copied properly.

**Solution:**

This has been fixed in the current version. The Dockerfile now ensures the public directory exists.

**If you still encounter this:**

1. **Ensure public directory exists:**
```bash
mkdir -p apps/frontend/public
touch apps/frontend/public/.gitkeep
```

2. **Rebuild frontend:**
```bash
docker-compose build --no-cache frontend
```

3. **Verify directory structure:**
```
apps/frontend/
├── public/
│   ├── .gitkeep
│   ├── robots.txt
│   └── favicon.ico
├── src/
└── ...
```

## Database Errors

### Error: Connection Refused

**Error Message:**
```
Error: P1001: Can't reach database server at `localhost:5432`
```

**Solutions:**

1. **If using Docker:**
```bash
# Check if PostgreSQL container is running
docker ps | grep wedding-invitations-db

# If not running, start it
docker-compose up -d postgres

# Check logs
docker logs wedding-invitations-db
```

2. **If using local PostgreSQL:**
```bash
# Check if PostgreSQL is running
# Windows:
sc query postgresql-x64-15

# Linux/Mac:
sudo systemctl status postgresql

# Start if not running
# Windows: Start from Services
# Linux/Mac:
sudo systemctl start postgresql
```

3. **Verify connection string:**
Check `apps/backend/.env`:
```env
# For Docker:
DATABASE_URL="postgresql://postgres:postgres@postgres:5432/wedding_invitations"

# For local:
DATABASE_URL="postgresql://postgres:password@localhost:5432/wedding_invitations"
```

### Error: Database Does Not Exist

**Error Message:**
```
Error: P1003: Database wedding_invitations does not exist
```

**Solution:**

**With Docker:**
```bash
docker-compose down
docker-compose up -d postgres
# Wait a few seconds for database to initialize
docker-compose up -d backend
```

**With local PostgreSQL:**
```bash
# Create database
createdb wedding_invitations

# Or using psql:
psql -U postgres
CREATE DATABASE wedding_invitations;
\q

# Run migrations
cd apps/backend
npx prisma migrate deploy
npx prisma db seed
```

### Error: Migration Failed

**Error Message:**
```
Error: Migration failed to apply
```

**Solution:**

**Reset database (WARNING: Deletes all data):**
```bash
cd apps/backend
npx prisma migrate reset
npx prisma db seed
```

**For Docker:**
```bash
docker-compose down -v  # Removes volumes (deletes data)
docker-compose up -d
```

## Port Conflicts

### Error: Port Already in Use

**Error Message:**
```
Error: listen EADDRINUSE: address already in use :::9300
Error: listen EADDRINUSE: address already in use :::9301
```

**Solutions:**

**Option 1: Kill the process using the port**

Windows:
```cmd
# Find process using port 9300
netstat -ano | findstr :9300

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Same for port 9301
netstat -ano | findstr :9301
taskkill /PID <PID> /F
```

Linux/Mac:
```bash
# Kill process on port 9300
lsof -ti:9300 | xargs kill -9

# Kill process on port 9301
lsof -ti:9301 | xargs kill -9
```

**Option 2: Use different ports**

Edit `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - '9401:9301'  # Change external port
  frontend:
    ports:
      - '9400:3000'  # Change external port
```

**Option 3: Stop Docker containers**
```bash
docker-compose down
docker ps -a | grep wedding
docker stop <container-id>
```

## Frontend Errors

### Error: Cannot Connect to API

**Error in browser console:**
```
Failed to fetch
Network Error
```

**Solutions:**

1. **Check backend is running:**
```bash
curl http://localhost:9301/api/plans
```

2. **Verify API URL in frontend:**
Check `apps/frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:9301/api
```

3. **Check CORS settings:**
Verify `apps/backend/.env`:
```env
CORS_ORIGINS=http://localhost:9300
```

4. **Clear browser cache:**
- Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Clear localStorage in DevTools Console:
```javascript
localStorage.clear()
```

### Error: Page Not Found (404)

**Cause:** Frontend not running or wrong URL

**Solutions:**

1. **Verify frontend is running:**
```bash
curl http://localhost:9300
```

2. **Check Docker logs:**
```bash
docker logs wedding-invitations-frontend
```

3. **Restart frontend:**
```bash
docker-compose restart frontend
```

## JWT/Authentication Errors

### Error: 401 Unauthorized

**Cause:** Token expired or invalid

**Solution:**

1. **Clear tokens and re-login:**
In browser DevTools Console:
```javascript
localStorage.removeItem('accessToken')
localStorage.removeItem('refreshToken')
// Then login again
```

2. **Check JWT secrets match:**
Verify `apps/backend/.env` has valid secrets:
```env
JWT_SECRET="your-secret-key"
JWT_REFRESH_SECRET="your-refresh-secret"
```

3. **Verify token expiration settings:**
```env
JWT_EXPIRATION="15m"
JWT_REFRESH_EXPIRATION="7d"
```

## Prisma Errors

### Error: Prisma Client Not Generated

**Error Message:**
```
Cannot find module '@prisma/client'
```

**Solution:**
```bash
cd apps/backend
npx prisma generate
```

For Docker:
```bash
docker-compose exec backend npx prisma generate
```

### Error: Schema Validation Failed

**Cause:** Invalid Prisma schema syntax

**Solution:**

1. **Validate schema:**
```bash
cd apps/backend
npx prisma validate
```

2. **Format schema:**
```bash
npx prisma format
```

3. **Check for syntax errors in:**
`apps/backend/prisma/schema.prisma`

## Seed Data Errors

### Error: Seed Failed

**Error Message:**
```
Error during seeding
```

**Solutions:**

1. **Check database connection:**
```bash
cd apps/backend
npx prisma db pull
```

2. **Reset and reseed:**
```bash
npx prisma migrate reset
# Confirm with 'y'
```

3. **Run seed manually:**
```bash
npm run seed
```

4. **For Docker:**
```bash
docker-compose exec backend npm run seed
```

## Docker-Specific Errors

### Error: Container Exits Immediately

**Check logs:**
```bash
docker logs wedding-invitations-backend
docker logs wedding-invitations-frontend
docker logs wedding-invitations-db
```

**Common causes and solutions:**

1. **Database not ready:**
```bash
# Add depends_on and health checks in docker-compose.yml
# Or wait 10 seconds between starting services
docker-compose up -d postgres
sleep 10
docker-compose up -d backend
sleep 5
docker-compose up -d frontend
```

2. **Missing environment variables:**
Check all required env vars are set in `docker-compose.yml`

3. **Build failed:**
```bash
docker-compose build --no-cache
```

### Error: Cannot Remove Container

**Error Message:**
```
Error: container is in use
```

**Solution:**
```bash
# Force remove
docker-compose down -v
docker rm -f wedding-invitations-backend
docker rm -f wedding-invitations-frontend
docker rm -f wedding-invitations-db

# Remove orphan containers
docker-compose down --remove-orphans
```

## Performance Issues

### Slow API Responses

**Solutions:**

1. **Check database indexes:**
Ensure proper indexes exist (already in schema.prisma)

2. **Enable query logging:**
In `apps/backend/src/prisma/prisma.service.ts`:
```typescript
log: ['query', 'error', 'warn']
```

3. **Increase database connection pool:**
In `apps/backend/prisma/schema.prisma`:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
  // Add connection pooling
}
```

### High Memory Usage

**For Docker:**
```bash
# Limit container memory
docker-compose.yml:
services:
  backend:
    mem_limit: 512m
  frontend:
    mem_limit: 512m
```

## Common Setup Mistakes

### Mistake 1: Not Creating .env Files

**Solution:**
```bash
cd apps/backend
cp .env.example .env

cd ../frontend
cp .env.local.example .env.local
```

### Mistake 2: Wrong Node Version

**Check version:**
```bash
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 9.0.0
```

**Solution:**
Install Node.js 18+ from nodejs.org or use nvm:
```bash
nvm install 18
nvm use 18
```

### Mistake 3: Not Running Migrations

**Solution:**
```bash
cd apps/backend
npx prisma migrate deploy
npx prisma db seed
```

## Getting Help

If you're still experiencing issues:

1. **Check all logs:**
```bash
# Backend logs
docker logs wedding-invitations-backend

# Frontend logs
docker logs wedding-invitations-frontend

# Database logs
docker logs wedding-invitations-db
```

2. **Verify all services are running:**
```bash
docker-compose ps
```

3. **Check environment variables:**
```bash
docker-compose exec backend printenv | grep -E "DATABASE_URL|JWT|PORT|FRONTEND_URL"
docker-compose exec frontend printenv | grep NEXT_PUBLIC
```

4. **Test individual services:**
```bash
# Test database
docker-compose exec postgres psql -U postgres -d wedding_invitations -c "SELECT 1;"

# Test backend
curl http://localhost:9301/api/plans

# Test frontend
curl http://localhost:9300
```

5. **Full reset (last resort):**
```bash
docker-compose down -v
docker system prune -a
rm -rf apps/backend/node_modules
rm -rf apps/frontend/node_modules
npm install
docker-compose build --no-cache
docker-compose up -d
```

## Quick Diagnostic Script

Save as `diagnose.sh`:

```bash
#!/bin/bash
echo "=== Wedding Invitations Platform Diagnostics ==="
echo ""
echo "Node version:"
node --version
echo ""
echo "Docker containers:"
docker-compose ps
echo ""
echo "Backend logs (last 10 lines):"
docker logs --tail 10 wedding-invitations-backend
echo ""
echo "Frontend logs (last 10 lines):"
docker logs --tail 10 wedding-invitations-frontend
echo ""
echo "Database logs (last 10 lines):"
docker logs --tail 10 wedding-invitations-db
echo ""
echo "Testing endpoints:"
echo "Backend API:"
curl -s http://localhost:9301/api/plans | head -20
echo ""
echo "Frontend:"
curl -s http://localhost:9300 | head -20
echo ""
echo "=== End Diagnostics ==="
```

Run with:
```bash
chmod +x diagnose.sh
./diagnose.sh
```
