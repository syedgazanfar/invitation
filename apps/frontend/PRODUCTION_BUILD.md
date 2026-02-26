# Production Build Guide

## Overview

This guide explains how to configure, build, and optimize the React frontend for production deployment.

## Environment Configuration

### 1. Setup Production Environment Variables

Create or update `.env.production` file with your production configuration:

```env
# API URL - Your production backend API
REACT_APP_API_URL=https://api.yourdomain.com/api/v1

# Public URL - Your production frontend domain
REACT_APP_PUBLIC_URL=https://yourdomain.com

# Environment
REACT_APP_ENV=production

# Razorpay Production Keys
REACT_APP_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx

# Optional: Analytics
REACT_APP_GA_TRACKING_ID=UA-XXXXXXXXX-X

# Optional: Error Tracking
REACT_APP_SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_ERROR_REPORTING=true
```

### 2. Get Razorpay Production Keys

1. Login to [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Switch to "Live Mode" (top left)
3. Navigate to Settings → API Keys
4. Generate new API keys for production
5. Copy the `Key ID` to `REACT_APP_RAZORPAY_KEY_ID`

**⚠️ IMPORTANT:** Never commit production keys to git. Keep `.env.production` in `.gitignore`.

## Building for Production

### 1. Install Dependencies

```bash
cd apps/frontend
npm install
```

### 2. Build the Application

```bash
npm run build
```

This command:
- Sets `NODE_ENV=production`
- Loads variables from `.env.production`
- Minifies JavaScript and CSS
- Optimizes images and assets
- Generates source maps (for debugging)
- Outputs to `build/` directory

### 3. Build Output

The `build/` directory will contain:
- `index.html` - Entry point
- `static/js/` - Minified JavaScript bundles
- `static/css/` - Minified CSS files
- `static/media/` - Optimized images and fonts
- `asset-manifest.json` - Asset mapping
- `manifest.json` - PWA manifest

### 4. Test Production Build Locally

Install a static file server:
```bash
npm install -g serve
```

Serve the build directory:
```bash
serve -s build -l 3000
```

Visit `http://localhost:3000` to test the production build.

## Build Optimizations

### Automatic Optimizations (via Create React App)

1. **Code Splitting** - React.lazy() and Suspense for route-based splitting
2. **Tree Shaking** - Removes unused code
3. **Minification** - Terser for JS, cssnano for CSS
4. **Asset Optimization** - Image compression, font subsetting
5. **Caching** - Hashed filenames for cache busting
6. **Service Worker** - (If enabled) for offline support

### Bundle Size Analysis

To analyze your bundle size:

```bash
npm install --save-dev source-map-explorer
```

Add to `package.json` scripts:
```json
"analyze": "source-map-explorer 'build/static/js/*.js'"
```

Run analysis:
```bash
npm run build
npm run analyze
```

### Performance Checklist

- [ ] All images are optimized (use WebP where possible)
- [ ] Lazy load routes and heavy components
- [ ] Use React.memo() for expensive components
- [ ] Enable gzip/brotli compression on server
- [ ] Use CDN for static assets
- [ ] Set proper cache headers
- [ ] Enable HTTP/2

## Deployment

### Option 1: Static Hosting (Recommended)

Deploy to services like:
- **Netlify** - `netlify deploy --prod`
- **Vercel** - `vercel --prod`
- **AWS S3 + CloudFront**
- **Google Cloud Storage + CDN**
- **Azure Static Web Apps**

### Option 2: Traditional Server (Nginx)

1. Copy `build/` directory to server
2. Configure Nginx:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/invitation-app/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json;

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Single Page App routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

3. Setup SSL with Let's Encrypt:
```bash
sudo certbot --nginx -d yourdomain.com
```

### Option 3: Docker

Create `Dockerfile`:
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t invitation-frontend .
docker run -p 80:80 invitation-frontend
```

## Environment-Specific Builds

### Development Build
```bash
npm start
# Uses .env.development
# Runs on http://localhost:3000
```

### Staging Build
```bash
# Create .env.staging
REACT_APP_ENV=staging
REACT_APP_API_URL=https://api-staging.yourdomain.com/api/v1

# Build
npm run build
# Manually set NODE_ENV or create custom script
```

### Production Build
```bash
npm run build
# Uses .env.production
# Outputs to build/
```

## Post-Deployment Checklist

- [ ] Verify all environment variables are set correctly
- [ ] Test critical user flows (login, registration, payment)
- [ ] Check browser console for errors
- [ ] Verify API endpoints are reachable
- [ ] Test on multiple browsers (Chrome, Firefox, Safari, Edge)
- [ ] Test on mobile devices
- [ ] Verify payment gateway integration
- [ ] Check analytics tracking (if enabled)
- [ ] Monitor error tracking (Sentry, etc.)
- [ ] Set up monitoring and alerts
- [ ] Configure CDN and caching
- [ ] Enable SSL/HTTPS
- [ ] Set up CI/CD pipeline

## Troubleshooting

### Build Fails

1. Clear cache: `rm -rf node_modules package-lock.json && npm install`
2. Check Node version: `node -v` (should be 14+)
3. Check for TypeScript errors: `npx tsc --noEmit`

### Blank Page After Deploy

1. Check browser console for errors
2. Verify `REACT_APP_API_URL` is correct
3. Check for CORS issues in backend
4. Verify nginx/server routing for SPA

### API Calls Failing

1. Check `REACT_APP_API_URL` in production
2. Verify backend is accessible from frontend domain
3. Check CORS configuration on backend
4. Verify SSL certificates (no mixed content)

### Payment Integration Not Working

1. Verify `REACT_APP_RAZORPAY_KEY_ID` is set
2. Ensure you're using Live Mode keys (not Test Mode)
3. Check Razorpay dashboard for errors
4. Verify webhook URLs are configured

## Security Best Practices

1. **Never expose sensitive keys** in frontend code
2. **Use environment variables** for all configuration
3. **Enable HTTPS** for all production domains
4. **Set security headers** (CSP, HSTS, X-Frame-Options)
5. **Keep dependencies updated** - `npm audit fix`
6. **Use API rate limiting** on backend
7. **Implement proper CORS** policies
8. **Sanitize user inputs** on both frontend and backend

## Maintenance

### Regular Updates
```bash
# Check for outdated packages
npm outdated

# Update dependencies
npm update

# Security audit
npm audit
npm audit fix
```

### Monitoring
- Set up uptime monitoring (UptimeRobot, Pingdom)
- Monitor error rates (Sentry, LogRocket)
- Track performance metrics (Lighthouse CI)
- Monitor API response times

## Support

For issues or questions:
- Check the [main README](../../README.md)
- Review [DEPLOYMENT_GUIDE.md](../../DEPLOYMENT_GUIDE.md)
- Create an issue in the repository
