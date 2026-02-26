# Deployment Guide

## Overview

This guide covers the complete deployment process for the Digital Invitation Platform, including frontend (React), backend (Django), and database (PostgreSQL) setup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Setup](#database-setup)
6. [Domain & SSL Configuration](#domain--ssl-configuration)
7. [Monitoring & Logging](#monitoring--logging)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Accounts

- [ ] Domain registrar account (Namecheap, GoDaddy, etc.)
- [ ] Cloud provider account (AWS, DigitalOcean, Heroku, etc.)
- [ ] Razorpay account (Live Mode activated)
- [ ] Email service (SendGrid, AWS SES, etc.)
- [ ] SMS service (Twilio, AWS SNS, etc.)

### Required Software

- [ ] Git
- [ ] Node.js 18+ & npm
- [ ] Python 3.10+
- [ ] PostgreSQL 14+
- [ ] Docker (optional, recommended)

---

## Infrastructure Setup

### Option 1: Single Server (Small Scale)

**Suitable for:** Up to 10,000 users, MVP deployment

**Requirements:**
- 2 CPU cores
- 4GB RAM
- 50GB SSD
- Ubuntu 22.04 LTS

**Providers:**
- DigitalOcean Droplet ($24/month)
- AWS EC2 t3.medium ($30/month)
- Linode Shared CPU ($24/month)

### Option 2: Separate Servers (Medium Scale)

**Suitable for:** 10,000+ users, production-grade

**Setup:**
- **Frontend Server:** Static hosting (Netlify, Vercel, CloudFront)
- **Backend Server:** Application server (EC2, DigitalOcean)
- **Database Server:** Managed PostgreSQL (RDS, DigitalOcean Managed DB)

### Option 3: Docker + Kubernetes (Large Scale)

**Suitable for:** 100,000+ users, enterprise-grade

**Setup:**
- Docker containers for frontend and backend
- Kubernetes for orchestration
- Load balancer for traffic distribution
- Auto-scaling based on demand

---

## Backend Deployment

### Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.10 python3-pip python3-venv -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Nginx
sudo apt install nginx -y

# Install certbot for SSL
sudo apt install certbot python3-certbot-nginx -y
```

### Step 2: Clone Repository

```bash
# Create app directory
sudo mkdir -p /var/www/invitation-app
sudo chown $USER:$USER /var/www/invitation-app

# Clone repository
cd /var/www/invitation-app
git clone <your-repository-url> .
```

### Step 3: Backend Configuration

```bash
cd apps/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create production environment file
nano .env.production
```

**.env.production:**
```env
# Django Settings
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/invitation_db

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com

# Razorpay
RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx
RAZORPAY_KEY_SECRET=<your-secret>

# Email (SendGrid example)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# SMS (Twilio example)
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
TWILIO_PHONE_NUMBER=<your-twilio-number>

# Media Files
MEDIA_URL=/media/
MEDIA_ROOT=/var/www/invitation-app/media

# Static Files
STATIC_URL=/static/
STATIC_ROOT=/var/www/invitation-app/staticfiles
```

### Step 4: Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql
```

```sql
CREATE DATABASE invitation_db;
CREATE USER invitation_user WITH PASSWORD 'strong_password';
ALTER ROLE invitation_user SET client_encoding TO 'utf8';
ALTER ROLE invitation_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE invitation_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE invitation_db TO invitation_user;
\q
```

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 5: Gunicorn Setup

```bash
# Install Gunicorn
pip install gunicorn

# Test Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/invitation-backend.service
```

```ini
[Unit]
Description=Invitation Platform Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/invitation-app/apps/backend
Environment="PATH=/var/www/invitation-app/apps/backend/venv/bin"
ExecStart=/var/www/invitation-app/apps/backend/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/invitation-app/apps/backend/gunicorn.sock \
    config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable invitation-backend
sudo systemctl start invitation-backend
sudo systemctl status invitation-backend
```

### Step 6: Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/invitation-backend
```

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /var/www/invitation-app/staticfiles/;
    }

    location /media/ {
        alias /var/www/invitation-app/media/;
    }

    location / {
        proxy_pass http://unix:/var/www/invitation-app/apps/backend/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/invitation-backend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Frontend Deployment

### Option 1: Netlify (Recommended for Beginners)

1. **Connect Repository**
   - Login to [Netlify](https://netlify.com)
   - Click "New site from Git"
   - Connect your GitHub/GitLab repository
   - Select branch: `main` or `production`

2. **Build Settings**
   - Build command: `npm run build`
   - Publish directory: `build/`
   - Base directory: `apps/frontend`

3. **Environment Variables**
   Add in Netlify dashboard:
   ```
   REACT_APP_API_URL=https://api.yourdomain.com/api/v1
   REACT_APP_PUBLIC_URL=https://yourdomain.com
   REACT_APP_ENV=production
   REACT_APP_RAZORPAY_KEY_ID=rzp_live_xxxxxxxxxx
   ```

4. **Deploy**
   - Click "Deploy site"
   - Wait for build to complete
   - Get temporary URL (e.g., `random-name.netlify.app`)

5. **Custom Domain**
   - Site settings → Domain management
   - Add custom domain: `yourdomain.com`
   - Configure DNS records as instructed
   - SSL automatically configured by Netlify

### Option 2: Vercel

Similar to Netlify:
```bash
npm install -g vercel
cd apps/frontend
vercel --prod
```

Follow prompts to configure deployment.

### Option 3: AWS S3 + CloudFront

1. **Build Frontend**
```bash
cd apps/frontend
npm run build
```

2. **Create S3 Bucket**
```bash
aws s3 mb s3://yourdomain-frontend
aws s3 sync build/ s3://yourdomain-frontend
```

3. **Configure S3 for Static Hosting**
   - Enable static website hosting
   - Set index document: `index.html`
   - Set error document: `index.html` (for SPA routing)

4. **Create CloudFront Distribution**
   - Origin: S3 bucket
   - Viewer protocol: Redirect HTTP to HTTPS
   - Alternate domain: `yourdomain.com`
   - SSL certificate: Request from ACM

5. **Configure DNS**
   - Add CNAME record: `yourdomain.com` → CloudFront domain

### Option 4: Self-Hosted (Nginx)

```bash
# Build frontend
cd apps/frontend
npm run build

# Copy to server
scp -r build/ user@server:/var/www/invitation-app/frontend
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/invitation-app/frontend/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1000;

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

---

## Database Setup

### Option 1: Self-Hosted PostgreSQL

Already covered in Backend Step 4.

### Option 2: Managed Database (Recommended)

**DigitalOcean Managed PostgreSQL:**
1. Create database cluster
2. Copy connection string
3. Update `DATABASE_URL` in backend `.env.production`
4. Whitelist backend server IP

**AWS RDS PostgreSQL:**
1. Create RDS instance (db.t3.micro for dev)
2. Configure security group (allow port 5432 from backend)
3. Get endpoint URL
4. Update connection string in backend

**Connection string format:**
```
postgresql://username:password@hostname:5432/database_name
```

---

## Domain & SSL Configuration

### 1. DNS Configuration

**For separate frontend and backend:**

```
Type    Name    Value                       TTL
A       @       <frontend-server-ip>        3600
A       www     <frontend-server-ip>        3600
A       api     <backend-server-ip>         3600
```

**For static hosting (Netlify/Vercel):**
```
CNAME   @       <netlify-domain>.netlify.app    3600
CNAME   www     <netlify-domain>.netlify.app    3600
A       api     <backend-server-ip>              3600
```

### 2. SSL Certificate (Let's Encrypt)

**For backend (Nginx):**
```bash
sudo certbot --nginx -d api.yourdomain.com
```

**For frontend (if self-hosted):**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

**Auto-renewal:**
```bash
# Test renewal
sudo certbot renew --dry-run

# Renewal happens automatically via cron
```

---

## Monitoring & Logging

### 1. Application Monitoring

**Backend (Django):**
- Install Sentry: `pip install sentry-sdk`
- Configure in `settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="<your-sentry-dsn>",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    environment="production",
)
```

**Frontend (React):**
- Already configured in `src/config/environment.ts`
- Set `REACT_APP_SENTRY_DSN` and `REACT_APP_ENABLE_ERROR_REPORTING=true`

### 2. Server Monitoring

**Install monitoring agent:**
```bash
# Datadog
DD_API_KEY=<your-key> bash -c "$(curl -L https://s3.amazonaws.com/dd-agent/scripts/install_script.sh)"

# Or New Relic
curl -Ls https://download.newrelic.com/install/newrelic-cli/scripts/install.sh | bash
```

### 3. Log Management

**Centralized logging with ELK Stack (optional):**
```bash
# Install Filebeat
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.x.x-amd64.deb
sudo dpkg -i filebeat-8.x.x-amd64.deb
```

**Or use CloudWatch (AWS) / Stackdriver (GCP)**

---

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /var/www/invitation-app
            git pull origin main
            cd apps/backend
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            sudo systemctl restart invitation-backend

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build Frontend
        working-directory: apps/frontend
        env:
          REACT_APP_API_URL: ${{ secrets.REACT_APP_API_URL }}
          REACT_APP_RAZORPAY_KEY_ID: ${{ secrets.RAZORPAY_KEY_ID }}
        run: |
          npm ci
          npm run build

      - name: Deploy to Netlify
        uses: nwtgck/actions-netlify@v2
        with:
          publish-dir: './apps/frontend/build'
          production-deploy: true
        env:
          NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
          NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
```

---

## Troubleshooting

### Backend Issues

**500 Internal Server Error:**
```bash
# Check Django logs
sudo journalctl -u invitation-backend -n 50

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

**Database connection failed:**
```bash
# Test PostgreSQL connection
psql -h localhost -U invitation_user -d invitation_db

# Check if service is running
sudo systemctl status postgresql
```

**Static files not loading:**
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check permissions
sudo chown -R www-data:www-data /var/www/invitation-app/staticfiles
```

### Frontend Issues

**Blank page:**
- Check browser console for errors
- Verify `REACT_APP_API_URL` is correct
- Check for CORS errors (configure backend)

**API calls failing:**
- Verify backend is accessible: `curl https://api.yourdomain.com/api/v1/`
- Check CORS configuration in Django settings
- Verify SSL certificates

---

## Post-Deployment

- [ ] Run API tests from [API_TESTING_CHECKLIST.md](./API_TESTING_CHECKLIST.md)
- [ ] Test all critical user flows
- [ ] Set up monitoring alerts
- [ ] Configure automated backups
- [ ] Document rollback procedures
- [ ] Update team on deployment status

---

## Support

For deployment issues:
- Check [PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)
- Review application logs
- Contact DevOps team
- Create issue in repository
