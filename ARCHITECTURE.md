# Digital Invitation Platform - Complete Architecture

## Project Overview
A production-ready digital invitation platform for Indian market handling 1000+ DAU.

## Tech Stack

### Backend
- **Framework**: Django 4.2 LTS + Django REST Framework
- **Database**: PostgreSQL 15
- **Cache**: Redis (for sessions, rate limiting, cache)
- **Task Queue**: Celery + Redis (for background tasks)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Admin**: Django Admin (customized) + Custom Admin APIs

### Frontend
- **Framework**: React 18 + TypeScript
- **UI Library**: Material-UI (MUI) v5
- **State Management**: Zustand
- **Routing**: React Router v6
- **Animations**: Framer Motion + GSAP
- **HTTP Client**: Axios

### DevOps
- **Containerization**: Docker + Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **WSGI**: Gunicorn

---

## Core Business Logic

### Link Tracking System (Anti-Fraud)

**The Problem**: User sends link to Person X, who opens and enters name. Count = 1.
But what if same person opens with different name? We need to prevent counting duplicates.

**The Solution - Device Fingerprint + Session + IP**:

```
When Guest opens invitation link:
  1. Generate device fingerprint (browser + OS + screen + fonts hash)
  2. Check if fingerprint exists for this invitation
  3. If YES → Show already filled name, don't count again
  4. If NO → Allow name entry, save fingerprint, count += 1
  5. Backup: Store IP address + User-Agent hash
  6. Cookie: Set persistent cookie as additional check
```

**Fingerprint Components**:
- Browser + Version
- Operating System
- Screen Resolution
- Installed Fonts (subset)
- Canvas/WebGL fingerprint
- Timezone
- Language

**Edge Cases Handled**:
- Same person, different browser → Counts as new (acceptable - rare)
- Same person, incognito mode → IP + User-Agent hash catches it
- Different people, same device → Cookie/fingerprint shared (rare, acceptable)
- VPN users → Still tracked by device fingerprint

---

## Plan Structure

| Plan | Regular Links | Test Links | Price (INR) | Templates |
|------|--------------|------------|-------------|-----------|
| Basic | 100 | 5 | 150 | Basic Templates |
| Premium | 150 | 5 | 350 | Basic + Premium |
| Luxury | 200 | 5 | 500 | All Templates |

**Link Validity**: 15 days from approval date

---

## Invitation Categories

### Event Types
1. **Wedding Invitation**
   - Hindu Wedding
   - Muslim Wedding (Nikah)
   - Christian Wedding
   - Sikh Wedding
   - Inter-faith Wedding

2. **Birthday Invitation**
   - 1st Birthday
   - Kids Birthday
   - Sweet 16
   - 18th Birthday
   - 50th/60th Milestone

3. **Small Party**
   - House Warming
   - Engagement
   - Anniversary
   - Baby Shower
   - Farewell Party

4. **Religious/Festival**
   - Ramzan/Ramadan Mubarak
   - Eid Mubarak
   - Diwali Party
   - Durga Puja
   - Christmas
   - New Year Party
   - Navratri
   - Ganesh Chaturthi

---

## Database Schema

### User Model
```python
class User(AbstractUser):
    phone = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # For admin approval workflow
    is_blocked = models.BooleanField(default=False)
```

### Plan Model
```python
class Plan(models.Model):
    code = models.CharField(max_length=20, unique=True)  # BASIC, PREMIUM, LUXURY
    name = models.CharField(max_length=100)
    regular_links = models.IntegerField()
    test_links = models.IntegerField(default=5)
    price_inr = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
```

### Order Model (Payment/Approval Workflow)
```python
class OrderStatus(models.TextChoices):
    PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    EXPIRED = 'EXPIRED', 'Expired'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50)  # WEDDING, BIRTHDAY, etc.
    
    # Status workflow
    status = models.CharField(max_length=20, choices=OrderStatus.choices)
    
    # Payment info (manual for now)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20)
    payment_notes = models.TextField(blank=True)
    
    # Admin approval
    approved_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='approved_orders')
    approved_at = models.DateTimeField(null=True)
    admin_notes = models.TextField(blank=True)
    
    # Link counts (admin can modify)
    granted_regular_links = models.IntegerField()
    granted_test_links = models.IntegerField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Invitation Model
```python
class Invitation(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    
    # Unique sharing link
    slug = models.CharField(max_length=32, unique=True)
    
    # Template selection
    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    
    # Event Details
    event_title = models.CharField(max_length=200)
    event_date = models.DateTimeField()
    event_venue = models.TextField()
    host_name = models.CharField(max_length=200)
    custom_message = models.TextField(blank=True)
    
    # Media
    banner_image = models.ImageField(upload_to='invitations/banners/')
    gallery_images = models.JSONField(default=list)  # Array of image URLs
    
    # Link validity
    link_expires_at = models.DateTimeField()
    
    # Status
    is_active = models.BooleanField(default=False)  # Only active after approval
    is_expired = models.BooleanField(default=False)
    
    # Usage tracking
    regular_links_used = models.IntegerField(default=0)
    test_links_used = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

### Guest Model (Link Tracking)
```python
class Guest(models.Model):
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE)
    
    # Guest info
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField(blank=True)
    
    # Anti-fraud tracking
    device_fingerprint = models.CharField(max_length=64, db_index=True)
    ip_address = models.GenericIPAddressField()
    user_agent_hash = models.CharField(max_length=64)
    session_id = models.CharField(max_length=64)
    
    # Link type
    is_test_link = models.BooleanField(default=False)
    
    # Timestamps
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['invitation', 'device_fingerprint']
```

### Template Model
```python
class Template(models.Model):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE)
    category = models.CharField(max_length=50)  # WEDDING, BIRTHDAY, etc.
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='templates/')
    
    # Animation configuration
    animation_type = models.CharField(max_length=50)
    animation_config = models.JSONField(default=dict)
    
    # Theme colors (JSON with primary, secondary, accent colors)
    theme_colors = models.JSONField(default=dict)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## API Endpoints

### Authentication
```
POST /api/auth/register/          - User registration
POST /api/auth/login/             - User login (JWT)
POST /api/auth/refresh/           - Refresh token
POST /api/auth/logout/            - Logout
POST /api/auth/verify-phone/      - Phone verification
```

### Plans & Templates (Public)
```
GET /api/plans/                   - List all plans
GET /api/plans/<code>/            - Get plan details
GET /api/templates/               - List templates (filter by plan, category)
GET /api/templates/<id>/          - Get template details
GET /api/categories/              - List invitation categories
```

### User Dashboard
```
GET /api/user/profile/            - Get profile
PUT /api/user/profile/            - Update profile
GET /api/user/orders/             - List user's orders
POST /api/user/orders/            - Create new order
GET /api/user/orders/<id>/        - Get order details
```

### Invitation Management
```
POST /api/invitations/            - Create invitation (after order approval)
GET /api/invitations/<slug>/      - Get invitation details
PUT /api/invitations/<slug>/      - Update invitation
GET /api/invitations/<slug>/stats/ - Get view statistics
GET /api/invitations/<slug>/guests/ - List guests
GET /api/invitations/<slug>/export/ - Export guests to CSV
```

### Public Invitation (No Auth)
```
GET /api/invite/<slug>/           - Get invitation public data
POST /api/invite/<slug>/register/ - Register guest (name entry)
GET /api/invite/<slug>/check/     - Check if already registered
```

### Admin APIs
```
GET /api/admin/dashboard/         - Dashboard stats
GET /api/admin/orders/            - List all orders (filter by status)
POST /api/admin/orders/<id>/approve/   - Approve order
POST /api/admin/orders/<id>/reject/    - Reject order
POST /api/admin/orders/<id>/grant-links/ - Grant extra/demo links
GET /api/admin/users/             - List users
GET /api/admin/statistics/        - Platform statistics
```

---

## Frontend Structure

```
frontend/
├── public/
│   └── templates/              # Template thumbnails
├── src/
│   ├── components/
│   │   ├── common/             # Reusable components
│   │   │   ├── Navbar.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── LoadingScreen.tsx
│   │   │   └── ProtectedRoute.tsx
│   │   ├── animations/         # Animation wrapper components
│   │   │   ├── FadeIn.tsx
│   │   │   ├── SlideUp.tsx
│   │   │   ├── Confetti.tsx
│   │   │   └── PageTransition.tsx
│   │   └── templates/          # Invitation templates
│   │       ├── WeddingTemplate1.tsx
│   │       ├── BirthdayTemplate1.tsx
│   │       └── ...
│   ├── pages/
│   │   ├── Home/               # Landing page
│   │   ├── Auth/
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── Plans/              # Plan selection
│   │   │   └── Plans.tsx
│   │   ├── Templates/          # Template selection
│   │   │   └── Templates.tsx
│   │   ├── Dashboard/          # User dashboard
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   └── Invitations.tsx
│   │   ├── InvitationBuilder/  # Create/edit invitation
│   │   │   └── Builder.tsx
│   │   └── Invite/             # Public invitation page
│   │       └── InvitationPage.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useFingerprint.ts   # Device fingerprint hook
│   ├── store/
│   │   ├── authStore.ts
│   │   └── invitationStore.ts
│   ├── services/
│   │   ├── api.ts              # Axios instance
│   │   ├── auth.service.ts
│   │   ├── plan.service.ts
│   │   └── invitation.service.ts
│   ├── utils/
│   │   ├── fingerprint.ts      # Device fingerprinting
│   │   ├── constants.ts
│   │   └── helpers.ts
│   ├── types/
│   │   └── index.ts
│   ├── theme.ts                # MUI theme configuration
│   └── App.tsx
└── package.json
```

---

## Animation Strategy

### Template Animations

Each template has an animation configuration:

```typescript
interface AnimationConfig {
  type: 'elegant' | 'fun' | 'traditional' | 'modern';
  entrance: {
    hero: string;      // Hero image animation
    title: string;     // Title reveal
    details: string;   // Event details
  };
  effects: {
    particles?: boolean;    // Floating particles/hearts
    confetti?: boolean;     // Confetti on open
    music?: boolean;        // Background music option
  };
  transitions: {
    betweenSections: string;
    galleryScroll: string;
  };
}
```

### Animation Libraries Usage

1. **Framer Motion**: 
   - Page transitions
   - Component entrances
   - Gesture animations
   - Layout animations

2. **GSAP**:
   - Complex timeline animations
   - Scroll-triggered effects
   - Text reveals
   - Parallax effects

3. **CSS Animations**:
   - Simple hover effects
   - Loading spinners
   - Micro-interactions

### Example Animation Flow (Wedding Template)

```
1. Page Load:
   - Fade in from black (0.5s)
   - Background image scale from 1.1 to 1.0 (2s, ease-out)
   
2. Hero Section:
   - Couple names slide up + fade in (staggered, 0.8s delay)
   - Wedding date fades in below names
   - Decorative elements float in from sides
   
3. Scroll Down:
   - Event details reveal with slide-up
   - Venue map fades in
   - Gallery images stagger reveal
   
4. Guest Entry:
   - Modal slides up
   - Input field focuses with glow effect
   - Submit button pulses gently
   
5. Success:
   - Confetti burst
   - Thank you message scales in
```

---

## Admin Dashboard Features

### Dashboard Overview
- Total Users
- Today's Orders
- Pending Approvals
- Active Invitations
- Revenue (calculated)

### Order Management
- Filter by status
- Quick approve/reject
- View user details
- Grant additional links
- Add admin notes

### User Management
- List all users
- Block/unblock users
- View user activity

### Statistics
- Daily/weekly/monthly views
- Popular templates
- Conversion rates
- Geographic distribution

---

## Security Measures

1. **Rate Limiting**: 100 requests/minute per IP
2. **CSRF Protection**: Enabled for all state-changing requests
3. **SQL Injection**: Protected by Django ORM
4. **XSS Protection**: React sanitization + Django escaping
5. **File Upload**: Validate image type, max size 5MB
6. **JWT Security**: Short expiry (15 min), secure refresh tokens
7. **Admin Security**: 2FA recommended for admin accounts

---

## Scaling Strategy for 1000+ DAU

### Database Optimization
- Index on `slug`, `device_fingerprint`, `status` fields
- Database connection pooling (PgBouncer)
- Read replicas for GET requests

### Caching Strategy
- Redis cache for:
  - Public invitation pages (TTL: 5 minutes)
  - Template data (TTL: 1 hour)
  - Plan data (TTL: 24 hours)
  - User sessions

### CDN
- Static files on CDN
- Template images on CDN
- User-uploaded images on S3 + CloudFront

### Background Tasks (Celery)
- Expire links daily
- Cleanup old fingerprints
- Generate statistics
- Send notifications

---

## Deployment Architecture

```
                    ┌─────────────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
     ┌──────▼──────┐ ┌─────▼─────┐ ┌─────▼─────┐
     │  React App  │ │  Django   │ │  Django   │
     │   (Static)  │ │  App #1   │ │  App #2   │
     └─────────────┘ │ (Gunicorn)│ │ (Gunicorn)│
                     └─────┬─────┘ └───────────┘
                           │
                     ┌─────▼─────┐
                     │  Redis    │
                     │ (Cache +  │
                     │  Queue)   │
                     └─────┬─────┘
                           │
                     ┌─────▼─────┐
                     │ PostgreSQL│
                     │   (RDS)   │
                     └───────────┘
```

---

## Development Plan

### Phase 1: Core Setup (Day 1)
- Django project setup
- Database models
- Basic APIs
- React + MUI setup

### Phase 2: Auth & Plans (Day 2)
- Authentication system
- Plan selection flow
- Template browsing

### Phase 3: Invitation System (Day 3-4)
- Invitation builder
- Link generation
- Device fingerprinting
- Guest registration

### Phase 4: Animations (Day 5-6)
- Animation templates
- Public invitation pages
- Effects and transitions

### Phase 5: Admin Dashboard (Day 7)
- Admin APIs
- Approval workflow
- Statistics

### Phase 6: Production Ready (Day 8)
- Docker setup
- Nginx configuration
- Performance optimization
- Testing

---

## Cost Estimation (India Deployment)

### Infrastructure (AWS India)
- EC2 t3.medium (2 vCPU, 4GB): ~4000 INR/month
- RDS db.t3.micro: ~2500 INR/month
- ElastiCache cache.t3.micro: ~1500 INR/month
- S3 + CloudFront: ~500 INR/month (depends on usage)
- **Total: ~8500 INR/month**

### Domain & SSL
- Domain: ~800 INR/year
- SSL Certificate: Free (Let's Encrypt)

---

## Next Steps

1. Approve this architecture
2. I'll implement the complete Django backend
3. Implement the React + MUI frontend
4. Create animation templates
5. Setup Docker for production deployment

Let me know if you want any changes or additions!
