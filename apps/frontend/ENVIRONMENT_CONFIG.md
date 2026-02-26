# Environment Configuration Guide

## Overview

This document explains how to configure environment variables for different deployment environments.

## Environment Files

The application uses environment-specific configuration files:

- `.env.example` - Template with all available variables (committed to git)
- `.env.development` - Development environment (committed to git)
- `.env.local` - Local overrides (NOT committed to git)
- `.env.production` - Production environment (NOT committed to git)
- `.env.staging` - Staging environment (NOT committed to git)

## Setup Instructions

### 1. Development Setup

For local development, copy the example file:

```bash
cp .env.example .env.local
```

Or use the provided `.env.development` file. Update values as needed:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_PUBLIC_URL=http://localhost:3000
REACT_APP_ENV=development
REACT_APP_RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxx
```

### 2. Production Setup

Create `.env.production` with production values:

```env
REACT_APP_API_URL=https://api.yourdomain.com/api/v1
REACT_APP_PUBLIC_URL=https://yourdomain.com
REACT_APP_ENV=production
REACT_APP_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true
```

**⚠️ SECURITY WARNING:**
- Never commit `.env.production` to git
- Never share production keys in public repositories
- Use separate keys for development and production

## Available Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | Backend API base URL | `https://api.example.com/api/v1` |
| `REACT_APP_PUBLIC_URL` | Frontend public URL | `https://example.com` |
| `REACT_APP_ENV` | Environment name | `development`, `staging`, `production` |
| `REACT_APP_RAZORPAY_KEY_ID` | Razorpay Key ID | `rzp_test_xxx` or `rzp_live_xxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REACT_APP_API_TIMEOUT` | API request timeout (ms) | `30000` |
| `REACT_APP_MAX_UPLOAD_SIZE` | Max file upload size (bytes) | `10485760` (10MB) |
| `REACT_APP_ENABLE_ANALYTICS` | Enable Google Analytics | `false` |
| `REACT_APP_GA_TRACKING_ID` | Google Analytics ID | - |
| `REACT_APP_ENABLE_ERROR_REPORTING` | Enable Sentry error tracking | `false` |
| `REACT_APP_SENTRY_DSN` | Sentry DSN URL | - |

## Environment Variable Precedence

Create React App loads environment files in this order (highest priority first):

1. `.env.production.local` (only for production builds)
2. `.env.local` (not loaded for test environment)
3. `.env.production` / `.env.development`
4. `.env`

Variables from higher priority files override lower priority files.

## Accessing Environment Variables

### Method 1: Direct Access (Not Recommended)

```typescript
const apiUrl = process.env.REACT_APP_API_URL;
```

### Method 2: Using Config Module (Recommended)

Import the centralized config:

```typescript
import config from './config/environment';

// Access configuration
const apiUrl = config.api.baseUrl;
const isProduction = config.isProduction;
const razorpayKey = config.razorpay.keyId;
```

Benefits:
- Type safety
- Centralized configuration
- Default values
- Validation in production

## Getting API Keys

### Razorpay

1. **Test Mode (Development)**
   - Login to [Razorpay Dashboard](https://dashboard.razorpay.com/)
   - Default mode is "Test Mode"
   - Navigate to Settings → API Keys
   - Copy Key ID (starts with `rzp_test_`)
   - Set as `REACT_APP_RAZORPAY_KEY_ID` in `.env.development`

2. **Live Mode (Production)**
   - Switch to "Live Mode" (top left toggle)
   - Navigate to Settings → API Keys
   - Generate new API keys
   - Copy Key ID (starts with `rzp_live_`)
   - Set as `REACT_APP_RAZORPAY_KEY_ID` in `.env.production`

**Important:** Never use live keys in development!

### Google Analytics (Optional)

1. Create a Google Analytics 4 property at [analytics.google.com](https://analytics.google.com/)
2. Get your Measurement ID (format: `G-XXXXXXXXXX`)
3. Set as `REACT_APP_GA_TRACKING_ID`
4. Enable with `REACT_APP_ENABLE_ANALYTICS=true`

### Sentry (Optional)

1. Create a project at [sentry.io](https://sentry.io/)
2. Copy the DSN from project settings
3. Set as `REACT_APP_SENTRY_DSN`
4. Enable with `REACT_APP_ENABLE_ERROR_REPORTING=true`

## Environment-Specific Behavior

### Development
- Detailed error messages
- Source maps enabled
- Hot module reloading
- React DevTools enabled
- Console logs visible
- Analytics disabled
- Test payment keys

### Production
- Minified code
- Optimized bundles
- Production error boundaries
- Analytics enabled (if configured)
- Error reporting to Sentry
- Live payment keys
- Service worker (if enabled)

## Validation

The config module (`src/config/environment.ts`) validates required variables in production:

```typescript
if (config.isProduction) {
  // Logs warnings for missing required variables
  // Check browser console on production build
}
```

## Testing Configuration

### Test Development Build
```bash
npm start
```
Visit: `http://localhost:3000`

### Test Production Build Locally
```bash
npm run build
npx serve -s build
```
Visit: `http://localhost:3000`

Check console for:
- Configuration warnings
- Missing environment variables
- API connection errors

## Troubleshooting

### Variable Not Updating

1. Restart the development server (`npm start`)
2. Clear build cache:
   ```bash
   rm -rf build node_modules/.cache
   npm start
   ```
3. Check variable name starts with `REACT_APP_`

### API Calls Failing

1. Verify `REACT_APP_API_URL` is correct
2. Check backend server is running
3. Verify CORS is configured on backend
4. Check browser console for errors

### Payment Not Working

1. Verify `REACT_APP_RAZORPAY_KEY_ID` is set
2. Check you're using correct mode (test/live)
3. Verify Razorpay script is loaded:
   - Check `public/index.html` for Razorpay script tag
4. Check browser console for Razorpay errors

### Environment Variables Not Found

**Common mistake:** Forgetting the `REACT_APP_` prefix

❌ Wrong:
```env
API_URL=http://localhost:8000
```

✅ Correct:
```env
REACT_APP_API_URL=http://localhost:8000
```

Only variables prefixed with `REACT_APP_` are embedded in the build.

## CI/CD Integration

### GitHub Actions

```yaml
- name: Build
  env:
    REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL }}
    REACT_APP_RAZORPAY_KEY_ID: ${{ secrets.RAZORPAY_KEY_ID }}
  run: npm run build
```

### Netlify

Add environment variables in: Site settings → Build & deploy → Environment

### Vercel

```bash
vercel env add REACT_APP_API_URL
vercel env add REACT_APP_RAZORPAY_KEY_ID
```

### Docker

Pass as build arguments:
```dockerfile
ARG REACT_APP_API_URL
ARG REACT_APP_RAZORPAY_KEY_ID
ENV REACT_APP_API_URL=$REACT_APP_API_URL
ENV REACT_APP_RAZORPAY_KEY_ID=$REACT_APP_RAZORPAY_KEY_ID
```

Build with:
```bash
docker build \
  --build-arg REACT_APP_API_URL=https://api.example.com/api/v1 \
  --build-arg REACT_APP_RAZORPAY_KEY_ID=rzp_live_xxx \
  -t invitation-app .
```

## Security Best Practices

1. ✅ **DO**
   - Use `.env.local` for local overrides
   - Keep `.env.production` out of version control
   - Use different keys for dev/staging/production
   - Rotate keys regularly
   - Use environment-specific error messages

2. ❌ **DON'T**
   - Commit production keys to git
   - Share keys in public repositories
   - Use production keys in development
   - Hard-code sensitive values
   - Include secrets in frontend code

## Support

For questions or issues:
- Review [PRODUCTION_BUILD.md](./PRODUCTION_BUILD.md) for build instructions
- Check the [main README](../../README.md) for general setup
- Create an issue in the repository
