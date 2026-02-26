# Changelog

All notable changes to the Digital Invitation Platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-02-26 - Production Ready Release

### Added

#### Frontend
- **Plans & Pricing Page** (`/plans`)
  - Display all subscription plans with pricing
  - Feature comparison table
  - Direct links to order creation

- **Templates Showcase Page** (`/templates`)
  - Browse all invitation templates
  - Filter by plan and category
  - Template preview with featured badge
  - Responsive card grid layout

- **Guest Management Page** (`/dashboard/guests`)
  - View all guests across invitations
  - Filter by specific invitation
  - Search by name, phone, or message
  - Statistics cards (total, attending, not attending, no response)
  - Export guest list to CSV
  - Guest details modal with device information
  - Pagination support

- **User Profile Page** (`/dashboard/profile`)
  - View and edit profile information
  - Change password functionality
  - Link usage statistics
  - Account status display

- **OTP Verification Flow**
  - Phone number verification with OTP
  - Resend OTP functionality
  - 5-minute expiry timer
  - Secure OTP validation

- **Forgot Password Flow**
  - Password reset via OTP
  - Secure password update
  - Success confirmation

- **Loading Skeletons**
  - DashboardSkeleton for dashboard cards
  - TemplateCardSkeleton for template grids
  - PlanCardSkeleton for pricing cards
  - TableSkeleton for data tables
  - Improved perceived performance

- **Pagination**
  - Added to Orders table
  - Added to MyInvitations grid (3x3 layout)
  - Added to Admin Orders table
  - Added to Admin Users table
  - Configurable rows per page

- **Error Boundaries**
  - Application-wide error boundary
  - Graceful error handling with fallback UI
  - Error reporting integration

- **Form Validation**
  - Client-side validation for all forms
  - Real-time validation feedback
  - Error message display
  - Required field indicators

#### Backend
- Admin dashboard API endpoints
- User approval/rejection system
- Link granting system
- Order management endpoints
- Guest management API
- Guest data export (CSV)
- Payment verification endpoints
- Notification system

#### Infrastructure
- Production environment configuration
- Environment-specific builds (development/production)
- Centralized config module (`src/config/environment.ts`)
- Security headers and CORS configuration
- Error tracking integration (Sentry)
- Analytics integration (Google Analytics)

#### Documentation
- `DEPLOYMENT_GUIDE.md` - Complete deployment instructions
- `PRODUCTION_CHECKLIST.md` - Pre-deployment checklist
- `API_TESTING_CHECKLIST.md` - Comprehensive API testing guide
- `ENVIRONMENT_CONFIG.md` - Environment variable documentation
- `PRODUCTION_BUILD.md` - Frontend build and optimization guide
- `CHANGELOG.md` - Version history and changes

### Changed
- Improved API error handling with detailed error messages
- Enhanced security with sanitized inputs
- Optimized database queries with indexing
- Updated Material-UI components to v5 patterns
- Refactored authentication flow with token refresh
- Improved mobile responsiveness across all pages

### Fixed
- **Security:** Removed sensitive payment data from frontend (Issue #8)
- CORS issues between frontend and backend
- Token refresh on authentication expiry
- SPA routing on production deployments
- Form validation edge cases
- Mobile menu responsiveness
- Image upload size limits

### Security
- Removed Razorpay secret key from frontend
- Implemented environment variable validation
- Added input sanitization
- Enabled HTTPS enforcement
- Configured security headers (CSP, HSTS, X-Frame-Options)
- Implemented rate limiting (backend)
- Added CSRF protection
- Secured API endpoints with proper authentication

### Performance
- Code splitting with React.lazy()
- Route-based lazy loading
- Image optimization
- Bundle size optimization (<5MB total)
- Implemented caching strategies
- Gzip compression enabled
- Static asset caching

### Deprecated
- None

### Removed
- Test payment data from production builds
- Console.log statements from production
- Unused dependencies
- Mock data from API responses

---

## [0.9.0] - 2026-02-15 - Beta Release

### Added
- Initial application structure
- User authentication (register/login/logout)
- Dashboard with statistics
- Invitation builder
- Payment integration (Razorpay)
- Admin dashboard
- Real-time updates (WebSocket)

### Changed
- Migrated from JavaScript to TypeScript
- Upgraded to React 18
- Implemented Zustand for state management

### Fixed
- Multiple authentication bugs
- Payment verification issues
- Mobile layout problems

---

## [0.5.0] - 2026-01-30 - Alpha Release

### Added
- Basic frontend structure
- Backend API scaffolding
- Database schema design
- User model and authentication
- Initial routing setup

---

## Version Guidelines

### Version Format: MAJOR.MINOR.PATCH

- **MAJOR**: Incompatible API changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Change Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security vulnerability fixes
- **Performance**: Performance improvements

---

## Upcoming Features (Roadmap)

### v1.1.0 (Planned)
- [ ] Multi-language support (i18n)
- [ ] WhatsApp invitation sharing
- [ ] Custom domain for invitations
- [ ] Advanced analytics dashboard
- [ ] Invitation preview before publishing
- [ ] Guest import from CSV/Excel
- [ ] Email invitations (alternative to SMS)
- [ ] Invitation scheduling

### v1.2.0 (Planned)
- [ ] Mobile app (React Native)
- [ ] Push notifications
- [ ] Offline support (PWA)
- [ ] Advanced template customization
- [ ] Video backgrounds for invitations
- [ ] Gift registry integration
- [ ] Photo gallery for guests

### v2.0.0 (Future)
- [ ] AI-powered invitation design
- [ ] Virtual event support
- [ ] Live streaming integration
- [ ] Social media integration
- [ ] Marketplace for templates
- [ ] Affiliate program

---

## Migration Guides

### Migrating from 0.9.0 to 1.0.0

**Backend:**
```bash
# Update dependencies
pip install -r requirements.txt

# Run new migrations
python manage.py migrate

# Recollect static files
python manage.py collectstatic --noinput
```

**Frontend:**
```bash
# Update dependencies
npm install

# Update environment variables (see ENVIRONMENT_CONFIG.md)
cp .env.example .env.production
# Edit .env.production with production values

# Rebuild
npm run build
```

**Database:**
- No breaking schema changes
- Indexes added for performance (automatic via migrations)

**Configuration:**
- New environment variables added (optional):
  - `REACT_APP_ENABLE_ANALYTICS`
  - `REACT_APP_ENABLE_ERROR_REPORTING`
  - `REACT_APP_SENTRY_DSN`
  - `REACT_APP_GA_TRACKING_ID`

---

## Support

For questions about changes or migration:
- Create an issue in the repository
- Review documentation in `/docs`
- Contact the development team

---

**Last Updated:** 2026-02-26
