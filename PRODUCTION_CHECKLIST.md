# Production Deployment Checklist

## Overview

Use this checklist before deploying to production to ensure everything is configured correctly and securely.

**Deployment Date:** _______________
**Deployed By:** _______________
**Version:** _______________

---

## Pre-Deployment

### Code Quality

- [ ] All tests pass locally
- [ ] No console errors in browser
- [ ] No linting errors (`npm run lint`)
- [ ] Code reviewed and approved
- [ ] Latest changes merged to `main` branch
- [ ] Git tags created for release version

### Environment Configuration

#### Backend

- [ ] `.env.production` created with all required variables
- [ ] `DEBUG=False` in production settings
- [ ] `SECRET_KEY` is strong and unique (50+ characters)
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] `CORS_ALLOWED_ORIGINS` set to frontend domain only
- [ ] Database credentials are secure and not default values
- [ ] Razorpay Live Mode keys configured
- [ ] Email service configured (SendGrid/SES)
- [ ] SMS service configured (Twilio/SNS)
- [ ] Media files storage configured (S3 or local with backups)
- [ ] Static files path configured correctly

#### Frontend

- [ ] `.env.production` created
- [ ] `REACT_APP_API_URL` points to production backend
- [ ] `REACT_APP_PUBLIC_URL` set to production domain
- [ ] `REACT_APP_ENV=production`
- [ ] Razorpay Live Key ID configured
- [ ] Analytics enabled (if using)
- [ ] Error reporting configured (Sentry)
- [ ] All environment variables validated

### Security

- [ ] All secrets removed from version control
- [ ] `.env.production` added to `.gitignore`
- [ ] No hardcoded API keys in source code
- [ ] HTTPS enforced for all domains
- [ ] SSL certificates installed and valid
- [ ] Security headers configured (CSP, HSTS, X-Frame-Options)
- [ ] CORS policy restricts to known origins only
- [ ] Rate limiting implemented on API
- [ ] SQL injection protection verified
- [ ] XSS protection enabled
- [ ] CSRF tokens implemented
- [ ] Authentication tokens expire appropriately
- [ ] File upload size limits enforced
- [ ] Input validation on all forms
- [ ] Sensitive data encrypted at rest

### Database

- [ ] Production database created
- [ ] Database backups configured (automated)
- [ ] Database credentials rotated from defaults
- [ ] Database accessible only from backend server
- [ ] Database connection pooling configured
- [ ] Indexes created for performance
- [ ] Migrations tested and ready
- [ ] Sample/test data removed from production DB
- [ ] Database monitoring enabled

### Infrastructure

- [ ] Server provisioned with adequate resources
  - [ ] CPU: 2+ cores recommended
  - [ ] RAM: 4GB+ recommended
  - [ ] Storage: 50GB+ recommended
- [ ] OS updated and patched
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] SSH keys configured (password auth disabled)
- [ ] Non-root user created for deployments
- [ ] Automatic security updates enabled
- [ ] Monitoring agent installed
- [ ] Log rotation configured

### Domain & DNS

- [ ] Domain purchased and active
- [ ] DNS records configured:
  - [ ] A record for frontend
  - [ ] A record for backend API
  - [ ] MX records for email (if self-hosted)
- [ ] DNS propagation verified (`nslookup`, `dig`)
- [ ] WWW and non-WWW redirects configured
- [ ] SSL certificates obtained (Let's Encrypt/ACM)
- [ ] Certificate auto-renewal configured

---

## Deployment Steps

### Backend Deployment

- [ ] Code deployed to server
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database migrations applied (`python manage.py migrate`)
- [ ] Static files collected (`python manage.py collectstatic`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Gunicorn service started and enabled
- [ ] Nginx configured and restarted
- [ ] Backend accessible at API domain
- [ ] Health check endpoint returns 200 OK

### Frontend Deployment

- [ ] Production build created (`npm run build`)
- [ ] Build folder generated without errors
- [ ] Build size optimized (<5MB for JS bundles)
- [ ] Files uploaded to hosting service
- [ ] Environment variables configured in hosting platform
- [ ] Custom domain configured
- [ ] SSL enabled and working
- [ ] Frontend accessible at main domain
- [ ] No 404 errors on page refresh (SPA routing works)

### Database Deployment

- [ ] Production database created
- [ ] Initial migrations applied
- [ ] Database user created with limited privileges
- [ ] Connection string updated in backend
- [ ] Database connection tested
- [ ] Sample data removed (if any)

---

## Post-Deployment Testing

### Smoke Tests (Critical Paths)

- [ ] Frontend loads without errors
- [ ] All pages accessible (no 404s)
- [ ] Static assets load (images, CSS, JS)
- [ ] API health check passes
- [ ] Admin panel accessible

### Authentication Tests

- [ ] User registration works
- [ ] OTP sending and verification works
- [ ] User login works
- [ ] Password reset works
- [ ] JWT token refresh works
- [ ] Protected routes require authentication
- [ ] Logout clears session correctly

### Core Functionality Tests

- [ ] Plans page displays correctly
- [ ] Templates page loads all templates
- [ ] Order creation works
- [ ] Payment integration works (test with small amount)
- [ ] Admin approval flow works
- [ ] Invitation creation works
- [ ] Invitation builder saves correctly
- [ ] Public invitation page loads
- [ ] Guest registration works
- [ ] RSVP updates work
- [ ] Guest list displays correctly
- [ ] CSV export works
- [ ] Email notifications sent
- [ ] SMS notifications sent (if enabled)

### Admin Tests

- [ ] Admin login works
- [ ] Dashboard statistics display correctly
- [ ] User management works
- [ ] Order approval works
- [ ] Link granting works
- [ ] Notifications display

### Performance Tests

- [ ] Page load time <3 seconds
- [ ] API response time <500ms
- [ ] Images optimized and load quickly
- [ ] No memory leaks
- [ ] Database queries optimized

### Browser Compatibility

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)

### Responsive Design

- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

---

## Monitoring & Alerts

### Application Monitoring

- [ ] Error tracking enabled (Sentry)
- [ ] Error alerts configured
- [ ] Performance monitoring enabled
- [ ] User analytics enabled (Google Analytics/Mixpanel)
- [ ] Uptime monitoring configured (UptimeRobot)

### Server Monitoring

- [ ] CPU usage monitoring
- [ ] Memory usage monitoring
- [ ] Disk space monitoring
- [ ] Network traffic monitoring
- [ ] Alert thresholds configured
- [ ] Notification channels set up (email/Slack)

### Log Management

- [ ] Application logs accessible
- [ ] Server logs accessible
- [ ] Database logs accessible
- [ ] Log rotation configured
- [ ] Log retention policy set (30 days recommended)

---

## Backup & Recovery

### Backups

- [ ] Database backup configured
  - [ ] Frequency: Daily (minimum)
  - [ ] Retention: 30 days (minimum)
  - [ ] Storage: Off-site location
- [ ] Media files backup configured
- [ ] Backup restoration tested
- [ ] Backup alerts configured

### Disaster Recovery

- [ ] Recovery plan documented
- [ ] Backup restoration procedure tested
- [ ] RTO (Recovery Time Objective) defined
- [ ] RPO (Recovery Point Objective) defined
- [ ] Emergency contacts list updated

---

## Documentation

- [ ] API documentation updated
- [ ] Deployment guide reviewed
- [ ] Environment variables documented
- [ ] Architecture diagram created
- [ ] Runbook created for common issues
- [ ] README updated with production info
- [ ] CHANGELOG created for this release

---

## Security Hardening

### Server Hardening

- [ ] Unnecessary services disabled
- [ ] Root login disabled
- [ ] SSH key-only authentication
- [ ] Fail2ban installed and configured
- [ ] UFW/iptables firewall enabled
- [ ] Automatic security updates enabled
- [ ] Regular security audits scheduled

### Application Hardening

- [ ] Dependency vulnerabilities checked (`npm audit`, `pip check`)
- [ ] No exposed admin endpoints
- [ ] Rate limiting on login endpoints
- [ ] CAPTCHA on registration (if needed)
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Content Security Policy configured

---

## Compliance & Legal

- [ ] Privacy policy page created
- [ ] Terms of service page created
- [ ] Cookie consent implemented (if required)
- [ ] GDPR compliance checked (if applicable)
- [ ] Data retention policy defined
- [ ] User data export functionality (if required)
- [ ] User data deletion functionality (if required)

---

## Performance Optimization

### Frontend

- [ ] Code splitting implemented
- [ ] Lazy loading for routes
- [ ] Images optimized (WebP format)
- [ ] CSS minified
- [ ] JavaScript minified
- [ ] Gzip compression enabled
- [ ] Browser caching configured
- [ ] CDN configured (if using)
- [ ] Service worker enabled (if PWA)

### Backend

- [ ] Database indexes created
- [ ] Query optimization done
- [ ] API response caching (Redis/Memcached)
- [ ] Static files served via CDN or Nginx
- [ ] Gunicorn workers configured (2-4x CPU cores)
- [ ] Connection pooling enabled
- [ ] Slow query logging enabled

---

## Third-Party Services

### Razorpay (Payment Gateway)

- [ ] Live Mode activated
- [ ] API keys rotated to live keys
- [ ] Test mode keys removed
- [ ] Webhooks configured
- [ ] Payment success flow tested
- [ ] Payment failure flow tested
- [ ] Refund process tested

### Email Service

- [ ] Production account created
- [ ] Sender domain verified
- [ ] SPF records configured
- [ ] DKIM records configured
- [ ] DMARC records configured
- [ ] Email templates tested
- [ ] Bounce handling configured
- [ ] Unsubscribe handling configured

### SMS Service

- [ ] Production account created
- [ ] Phone number verified/purchased
- [ ] SMS templates tested
- [ ] Delivery reports enabled
- [ ] Opt-out handling configured

### Analytics

- [ ] Google Analytics configured
- [ ] Conversion tracking set up
- [ ] Custom events defined
- [ ] Goals configured
- [ ] Dashboard created

### Error Tracking

- [ ] Sentry project created
- [ ] DSN configured in app
- [ ] Error alerts configured
- [ ] Team notifications set up

---

## Team & Operations

### Access Control

- [ ] Production access limited to authorized personnel
- [ ] Admin credentials shared securely (1Password, LastPass)
- [ ] 2FA enabled for all admin accounts
- [ ] Access logs enabled
- [ ] Regular access audits scheduled

### Communication

- [ ] Deployment announcement sent to team
- [ ] Customer support team notified
- [ ] Known issues documented
- [ ] Incident response plan in place
- [ ] On-call schedule defined

### Post-Launch

- [ ] Monitor error rates for 24 hours
- [ ] Check performance metrics
- [ ] Review user feedback
- [ ] Fix critical bugs immediately
- [ ] Schedule post-mortem meeting

---

## Go-Live Decision

### Final Checks

- [ ] All critical tests pass
- [ ] No known critical bugs
- [ ] Performance meets requirements
- [ ] Security audit completed
- [ ] Team ready for go-live
- [ ] Rollback plan documented

### Sign-Off

**Technical Lead:** _______________  Date: _______________
**Product Owner:** _______________  Date: _______________
**Security Officer:** _______________  Date: _______________

---

## Post-Launch (Within 24 Hours)

- [ ] Monitor error rates
- [ ] Check server resource usage
- [ ] Review user activity logs
- [ ] Address any critical issues
- [ ] Send launch announcement
- [ ] Gather initial user feedback

---

## Post-Launch (Within 1 Week)

- [ ] Performance optimization based on real data
- [ ] Address non-critical bugs
- [ ] Adjust server resources if needed
- [ ] Review analytics data
- [ ] Plan next release

---

## Rollback Plan

In case of critical issues:

1. **Immediate Actions**
   - [ ] Stop deployment
   - [ ] Notify team
   - [ ] Assess impact

2. **Frontend Rollback**
   ```bash
   # Netlify/Vercel
   - Revert to previous deployment in dashboard

   # Self-hosted
   git checkout <previous-commit>
   npm run build
   # Deploy previous build
   ```

3. **Backend Rollback**
   ```bash
   cd /var/www/invitation-app
   git checkout <previous-commit>
   source venv/bin/activate
   python manage.py migrate <previous-migration>
   sudo systemctl restart invitation-backend
   ```

4. **Database Rollback**
   ```bash
   # Restore from backup
   psql invitation_db < backup_YYYYMMDD.sql
   ```

5. **Post-Rollback**
   - [ ] Verify system stability
   - [ ] Communicate status to users
   - [ ] Document issues
   - [ ] Plan fix and redeployment

---

## Emergency Contacts

**Technical Lead:** _______________ (Phone: _______________)
**DevOps Engineer:** _______________ (Phone: _______________)
**Product Owner:** _______________ (Phone: _______________)
**Customer Support:** _______________ (Email: _______________)

---

## Notes

_Document any issues encountered during deployment, workarounds applied, or decisions made:_

---

**Deployment Status:** [ ] Pending  [ ] In Progress  [ ] Completed  [ ] Rolled Back

**Final Sign-Off:** _______________ Date: _______________
