# Deploying to a single server (Docker)

This deploys everything (Django backend, Celery, Next.js frontend, Postgres,
Redis, and the WA-AKG WhatsApp gateway) on one Linux server using
`docker-compose.prod.yml`, with the host's nginx as the only public entry point.

```
Internet ──► nginx (host, :80/:443, certbot TLS)
               ├─ yourdomain.com/            ► frontend   127.0.0.1:3000
               ├─ yourdomain.com/api|admin|static|ws ► backend 127.0.0.1:8000
               ├─ yourdomain.com/media/      ► media      127.0.0.1:8081
               └─ wa.yourdomain.com          ► wa-gateway 127.0.0.1:3001
Postgres, Redis, MySQL: internal Docker network only, never published.
```

## 1. Server

- Ubuntu 22.04/24.04, **at least 4 GB RAM** (building WA-AKG and Next.js is memory-hungry; add swap on smaller boxes).
- DNS: point `yourdomain.com`, `www.yourdomain.com` and `wa.yourdomain.com` (A records) at the server IP.

```bash
# Docker + compose plugin
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # log out and back in afterwards

# nginx + certbot + firewall
sudo apt update && sudo apt install -y nginx certbot python3-certbot-nginx
sudo ufw allow OpenSSH && sudo ufw allow 'Nginx Full' && sudo ufw enable
```

## 2. Code

```bash
git clone --recurse-submodules https://github.com/syedgazanfar/invitation.git
cd invitation
```

Forgot `--recurse-submodules`? Run `git submodule update --init` (otherwise `apps/wa-gateway` is empty and the build fails).

## 3. Settings

```bash
cp .env.production.example .env
nano .env
```

Replace every `yourdomain.com` and every `replace-with-...` value. Generate secrets with `openssl rand -hex 32`.
Leave `WA_AKG_API_KEY` / `WA_AKG_SESSION_ID` empty for now (step 6).
The compose file refuses to start if a required value is missing.

## 4. Start the stack

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend   # Ctrl+C to stop following
```

The first build takes a while. On start, the backend runs migrations, collects static files and seeds plans/templates.

Create a Django admin user:

```bash
docker compose -f docker-compose.prod.yml exec backend python src/manage.py createsuperuser
```

## 5. nginx + HTTPS

```bash
sudo cp nginx/production.conf /etc/nginx/sites-available/invitation
sudo sed -i 's/yourdomain.com/YOUR-REAL-DOMAIN/g' /etc/nginx/sites-available/invitation
sudo ln -s /etc/nginx/sites-available/invitation /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d YOUR-REAL-DOMAIN -d www.YOUR-REAL-DOMAIN -d wa.YOUR-REAL-DOMAIN
```

## 6. Connect WhatsApp

1. Open `https://wa.yourdomain.com` and log in with `WA_ADMIN_EMAIL` / `WA_ADMIN_PASSWORD`.
2. Create a session and scan the QR code with the WhatsApp account that should send messages (WhatsApp → Linked devices).
3. Copy the session ID, and create an API key under **Settings → API Keys**.
4. Put them in `.env` as `WA_AKG_SESSION_ID` and `WA_AKG_API_KEY`, set `WA_AKG_ADMIN_NUMBERS`, then:

```bash
docker compose -f docker-compose.prod.yml up -d backend celery
```

5. Submit a test enquiry at `https://yourdomain.com/enquiry` and check that the WhatsApp messages arrive.
   If not, look at the enquiry in `https://yourdomain.com/django-admin/` (Django admin; the WhatsApp error is shown there), and at
   `docker compose -f docker-compose.prod.yml logs celery`.

## Updating

```bash
git pull && git submodule update --init
docker compose -f docker-compose.prod.yml up -d --build
```

## Backups

Postgres (app data) and MySQL (WhatsApp session data) live in Docker volumes:

```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U postgres invitation_platform | gzip > backup-$(date +%F).sql.gz
docker compose -f docker-compose.prod.yml exec -T wa-gateway-db sh -c 'mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" wa_akg' | gzip > wa-backup-$(date +%F).sql.gz
```
