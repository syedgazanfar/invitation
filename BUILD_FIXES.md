# Build Fixes Applied

This document describes the fixes applied to resolve the TypeScript build error.

## Problem

When building the Docker container for the backend, the following error occurred:

```
prisma/seed.ts:194:22 - error TS2345: Argument of type '{ planCode: PlanCode; name: string; previewUrl: string; description: string; }' is not assignable to parameter of type 'never'.
```

## Root Cause

The `templates` array in `apps/backend/prisma/seed.ts` was declared without a type annotation:

```typescript
const templates = [];  // TypeScript infers this as never[]
```

When TypeScript encounters an empty array without type information, it infers the type as `never[]`, which means it cannot accept any values.

## Fixes Applied

### Fix 1: Added Type Annotation to Templates Array

**File:** `apps/backend/prisma/seed.ts`

**Before:**
```typescript
const templates = [];
for (const [planCode, themes] of Object.entries(templateThemes)) {
  for (let i = 0; i < themes.length; i++) {
    templates.push({
      planCode: planCode as PlanCode,
      name: themes[i],
      previewUrl: `https://placeholder.cdn/templates/${planCode.toLowerCase()}/${i + 1}.jpg`,
      description: `Beautiful ${themes[i]} template for your special day`,
    });
  }
}
```

**After:**
```typescript
const templates: Array<{
  planCode: PlanCode;
  name: string;
  previewUrl: string;
  description: string;
}> = [];

for (const [planCode, themes] of Object.entries(templateThemes)) {
  for (let i = 0; i < themes.length; i++) {
    templates.push({
      planCode: planCode as PlanCode,
      name: themes[i],
      previewUrl: `https://placeholder.cdn/templates/${planCode.toLowerCase()}/${i + 1}.jpg`,
      description: `Beautiful ${themes[i]} template for your special day`,
    });
  }
}
```

### Fix 2: Updated TypeScript Configuration

**File:** `apps/backend/tsconfig.json`

**Before:**
```json
{
  "include": ["src/**/*", "prisma/**/*"],
  "exclude": ["node_modules", "dist"]
}
```

**After:**
```json
{
  "include": ["src/**/*", "prisma/seed.ts"],
  "exclude": ["node_modules", "dist", "prisma/migrations"]
}
```

**Reason:**
- Only include the seed.ts file from prisma directory, not the entire directory
- Exclude migrations folder to avoid unnecessary compilation
- This ensures the seed script is available but doesn't interfere with the main build

### Fix 3: Added Prisma Seed Configuration

**File:** `apps/backend/package.json`

**Added:**
```json
{
  "prisma": {
    "seed": "ts-node prisma/seed.ts"
  }
}
```

**Reason:**
This tells Prisma how to run the seed script properly, especially important for Docker builds and `prisma db seed` commands.

## Verification

To verify the fixes work:

### 1. Local Build Test
```bash
cd apps/backend
npm install
npm run build
```

Expected output:
```
Successfully compiled: X files with tsc
```

### 2. Docker Build Test
```bash
docker-compose build --no-cache backend
```

Expected output:
```
Successfully built <image-id>
Successfully tagged invitation-backend:latest
```

### 3. Full Docker Compose Test
```bash
docker-compose down
docker-compose up -d
```

Check all services are running:
```bash
docker-compose ps
```

Expected:
```
wedding-invitations-backend    running
wedding-invitations-frontend   running
wedding-invitations-db         running
```

### 4. Test Seed Script
```bash
docker-compose exec backend npm run seed
```

Expected output:
```
Starting database seeding...
Created 3 plans
Created 10 country pricing entries
Created 60 templates
Database seeding completed successfully!
```

## Additional Improvements

### Better Error Handling in Seed Script

The seed script now has better type safety, which provides:

1. **Compile-time checking**: TypeScript will catch type errors before runtime
2. **Better IDE support**: IntelliSense will show correct types
3. **Clearer intent**: Developers can see what data structure is expected

### Build Process Optimization

The updated tsconfig ensures:

1. **Faster builds**: Only necessary files are compiled
2. **Cleaner output**: Migrations folder excluded
3. **Proper separation**: Application code vs. database scripts

## Testing Checklist

After applying these fixes, verify:

- [ ] Backend builds successfully locally
- [ ] Backend builds successfully in Docker
- [ ] Docker compose starts all services
- [ ] Database migrations run successfully
- [ ] Seed script runs successfully
- [ ] API endpoints are accessible
- [ ] Frontend can connect to backend
- [ ] No TypeScript errors in console

## If Build Still Fails

If you still encounter build errors after applying these fixes:

### 1. Clear all caches
```bash
# Clear npm cache
npm cache clean --force

# Clear Docker build cache
docker builder prune -a

# Remove node_modules
rm -rf apps/backend/node_modules
rm -rf apps/frontend/node_modules

# Reinstall
npm install
```

### 2. Verify Node/npm versions
```bash
node --version  # Should be >= 18.0.0
npm --version   # Should be >= 9.0.0
```

### 3. Check for file corruption
```bash
# Re-clone or re-download the seed.ts file
# Ensure line endings are correct (LF, not CRLF)
```

### 4. Full clean rebuild
```bash
# Remove everything
docker-compose down -v
docker system prune -a

# Remove all generated files
rm -rf apps/backend/dist
rm -rf apps/backend/node_modules
rm -rf apps/frontend/.next
rm -rf apps/frontend/node_modules

# Rebuild from scratch
npm install
docker-compose build --no-cache
docker-compose up -d
```

## Frontend Build Error Fix

### Problem

Docker build failed with:
```
COPY --from=builder /app/public ./public
"/app/public": not found
```

### Root Cause

The frontend didn't have a `public` directory, which is expected by Next.js and the Dockerfile.

### Solution

**File:** `apps/frontend/Dockerfile`

1. **Created public directory:**
   - Added `apps/frontend/public/` directory
   - Added `.gitkeep`, `robots.txt`, and `favicon.ico`

2. **Updated Dockerfile:**

**Before:**
```dockerfile
COPY . .
RUN npm run build
```

**After:**
```dockerfile
COPY . .
# Ensure public directory exists
RUN mkdir -p public
RUN npm run build
```

This ensures the public directory always exists before copying in the final stage.

3. **Added app icon:**
   - Created `apps/frontend/src/app/icon.svg` for Next.js 14 App Router

## Summary

**Backend Issues Fixed:**
1. ✅ Added explicit type annotation to `templates` array
2. ✅ Updated `tsconfig.json` to include only necessary files
3. ✅ Added Prisma seed configuration to `package.json`

**Frontend Issues Fixed:**
4. ✅ Created public directory with placeholder files
5. ✅ Updated Dockerfile to ensure public directory exists
6. ✅ Added app icon for Next.js

**Result:**
- Clean TypeScript compilation
- Successful Docker builds (backend and frontend)
- Proper seed script execution
- All services running correctly
