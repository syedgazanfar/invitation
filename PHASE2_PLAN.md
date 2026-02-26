# Phase 2: Code Quality Improvements - Detailed Plan

**Date:** February 25, 2026
**Status:** In Progress

## Code Analysis Summary

### Current State Assessment

**Backend Code Statistics:**
- Total Python files: ~90
- Largest file: ai/services/photo_analysis.py (1,716 lines)
- Second largest: ai/services/message_generator.py (1,500 lines)
- Largest view file: ai/views.py (1,496 lines)
- Admin dashboard views: admin_dashboard/views.py (821 lines)

**Problems Identified:**
1. **Monolithic view files** - Single files with 10+ view classes
2. **Incomplete service layer** - Only 2/5 apps have services
3. **Business logic in views** - Should be extracted to services
4. **Test coverage incomplete** - Test files exist but coverage unknown
5. **Missing database indexes** - Performance optimization needed
6. **Potential N+1 queries** - Not optimized for list/dashboard views

## Refactoring Strategy

### Priority 1: Backend Structure (Tasks #1-5)

#### Task #1: Refactor AI Views Module ⏳
**Current:** Single 1,496-line file with 17 view classes
**Target:** Multiple focused modules

**New Structure:**
```
apps/backend/src/apps/ai/
├── views/
│   ├── __init__.py
│   ├── photo_analysis.py      # PhotoAnalysisViewSet, related views
│   ├── message_generation.py  # Message generation endpoints
│   ├── recommendations.py     # Template & style recommendations
│   ├── usage.py               # Usage stats and limits
│   └── helpers.py             # Shared response helpers
├── services/                  # Already exists
├── models.py
└── serializers.py
```

**Benefits:**
- Easier to navigate and understand
- Better code organization
- Simplified testing
- Reduced merge conflicts

---

#### Task #2: Refactor Admin Dashboard Views ⏳
**Current:** Single 821-line file with 13 view classes
**Target:** Multiple focused modules

**New Structure:**
```
apps/backend/src/apps/admin_dashboard/
├── views/
│   ├── __init__.py
│   ├── dashboard.py        # DashboardStatsView
│   ├── approvals.py        # Approval workflow views
│   ├── users.py            # User management views
│   └── notifications.py    # Notification views
├── services.py             # Already exists
├── consumers.py            # WebSocket consumers
└── models.py
```

---

#### Task #3: Create Service Layer for Accounts App ⏳
**Current:** Business logic mixed in views.py (487 lines)
**Target:** Clean separation with service layer

**New Structure:**
```
apps/backend/src/apps/accounts/
├── views.py                # Thin controllers
├── services/
│   ├── __init__.py
│   ├── auth_service.py     # Login, logout, token refresh
│   ├── user_service.py     # User CRUD operations
│   └── phone_verification_service.py  # OTP handling
├── models.py
└── serializers.py
```

**Services to Extract:**
- `AuthService`: JWT token management, login/logout
- `UserService`: User registration, profile updates
- `PhoneVerificationService`: OTP generation and verification

---

#### Task #4: Create Service Layer for Invitations App ⏳
**Current:** Some logic in views, some in models (266 lines views)
**Target:** Centralized business logic

**New Structure:**
```
apps/backend/src/apps/invitations/
├── views.py                # Thin controllers
├── public_views.py
├── payment_views.py
├── services/
│   ├── __init__.py
│   ├── invitation_service.py   # Invitation CRUD
│   ├── guest_service.py        # Guest registration
│   └── link_service.py         # Link generation & validation
├── models.py
└── serializers.py
```

**Services to Extract:**
- `InvitationService`: Create, update, activate invitations
- `GuestService`: Guest registration, fingerprint validation, limit enforcement
- `LinkService`: Slug generation, expiry checking

**Critical Logic to Centralize:**
- Device fingerprint validation
- Guest limit enforcement (regular vs test)
- Link expiry checking

---

#### Task #5: Create Service Layer for Plans App ⏳
**Current:** Simple views with pricing logic (130 lines)
**Target:** Service layer for complex calculations

**New Structure:**
```
apps/backend/src/apps/plans/
├── views.py                # Thin controllers
├── services/
│   ├── __init__.py
│   ├── plan_service.py     # Plan management
│   ├── pricing_service.py  # Pricing calculations
│   └── order_service.py    # Order lifecycle
├── models.py
└── serializers.py
```

**Services to Extract:**
- `PlanService`: Plan retrieval and management
- `PricingService`: Country-specific pricing, tax calculations
- `OrderService`: Order creation, status transitions

---

### Priority 2: Testing Infrastructure (Tasks #6-7)

#### Task #6: Add Comprehensive Unit Tests ⏳
**Target:** 80% code coverage for service layer

**Test Structure:**
```
apps/backend/tests/
├── unit/
│   ├── accounts/
│   │   ├── test_auth_service.py
│   │   ├── test_user_service.py
│   │   └── test_phone_verification_service.py
│   ├── invitations/
│   │   ├── test_invitation_service.py
│   │   ├── test_guest_service.py
│   │   └── test_link_service.py
│   ├── plans/
│   │   ├── test_plan_service.py
│   │   ├── test_pricing_service.py
│   │   └── test_order_service.py
│   └── admin_dashboard/
│       └── test_admin_services.py
└── fixtures/
    └── test_data.py
```

**Critical Tests:**
- Guest limit enforcement logic
- Device fingerprinting validation
- Pricing calculation accuracy
- Link expiry validation
- Order status transitions

**Testing Tools:**
- Django TestCase
- pytest-django
- factory_boy for test data
- Mock for external dependencies

---

#### Task #7: Add Integration Tests ⏳
**Target:** All critical user journeys tested

**Test Scenarios:**
1. **User Registration Flow:**
   - Register → Verify phone → Login → Get token

2. **Order & Approval Flow:**
   - Create order → Make payment → Admin approves → Link activates

3. **Guest Registration Flow:**
   - Open invitation → Enter name → Fingerprint check → Save guest

4. **Payment Flow:**
   - Create order → Create Razorpay order → Verify payment → Update status

**Test Structure:**
```
apps/backend/tests/
└── integration/
    ├── test_user_registration_flow.py
    ├── test_order_approval_flow.py
    ├── test_guest_registration_flow.py
    └── test_payment_flow.py
```

---

### Priority 3: Database Optimization (Tasks #8-9)

#### Task #8: Add Database Indexes ⏳
**Goal:** Optimize query performance for common operations

**Indexes to Add:**

**invitations.Invitation:**
```python
class Meta:
    indexes = [
        models.Index(fields=['slug']),  # Lookup by slug
        models.Index(fields=['status']),  # Filter by status
        models.Index(fields=['expires_at']),  # Expiry checking
        models.Index(fields=['user', '-created_at']),  # User's invitations
    ]
```

**invitations.Guest:**
```python
class Meta:
    indexes = [
        models.Index(fields=['invitation', 'device_fingerprint']),  # Composite
        models.Index(fields=['invitation', 'is_test']),  # Count by type
    ]
```

**plans.Order:**
```python
class Meta:
    indexes = [
        models.Index(fields=['status']),  # Filter by status
        models.Index(fields=['user', '-created_at']),  # User's orders
        models.Index(fields=['-created_at']),  # Recent orders
    ]
```

**accounts.User:**
```python
class Meta:
    indexes = [
        models.Index(fields=['email']),  # Already unique, but explicit
        models.Index(fields=['phone']),  # Phone lookup
        models.Index(fields=['is_approved']),  # Filter pending users
    ]
```

---

#### Task #9: Fix N+1 Query Issues ⏳
**Goal:** Optimize database queries in list views

**Common Issues:**

1. **Dashboard Stats:**
```python
# Before (N+1)
orders = Order.objects.all()
for order in orders:
    print(order.user.name)  # N queries

# After
orders = Order.objects.select_related('user').all()
```

2. **Invitation with Guests:**
```python
# Before (N+1)
invitations = Invitation.objects.all()
for inv in invitations:
    print(inv.guests.count())  # N queries

# After
invitations = Invitation.objects.prefetch_related('guests').all()
```

3. **Admin Dashboard:**
```python
# Before (multiple N+1)
users = User.objects.all()
for user in users:
    print(user.orders.count())  # N queries
    print(user.invitations.count())  # N queries

# After
users = User.objects.prefetch_related('orders', 'invitations').all()
```

**Tools to Use:**
- Django Debug Toolbar
- django-silk for profiling
- Manual EXPLAIN ANALYZE on slow queries

---

### Priority 4: Frontend Refactoring (Task #10)

#### Task #10: Create Component Library ⏳
**Goal:** Extract reusable components for consistency

**Current Issue:** Component duplication across features

**New Structure:**
```
apps/frontend/src/shared/components/
├── ui/
│   ├── Button/
│   │   ├── Button.tsx
│   │   ├── Button.test.tsx
│   │   └── Button.stories.tsx
│   ├── Input/
│   ├── Card/
│   ├── Modal/
│   └── Badge/
├── forms/
│   ├── FormField/
│   ├── FormSelect/
│   ├── FormDatePicker/
│   └── FormFileUpload/
├── layout/
│   ├── Page/
│   ├── Section/
│   ├── Container/
│   └── Grid/
└── feedback/
    ├── Loading/
    ├── ErrorBoundary/
    ├── SuccessMessage/
    └── EmptyState/
```

**Benefits:**
- Consistent UI across app
- Easier to maintain
- Reusable validation logic
- Faster development

---

## Implementation Order

### Week 1: Backend Refactoring
- **Day 1-2:** Tasks #1, #2 (Refactor view files)
- **Day 3-4:** Tasks #3, #4 (Create service layers)
- **Day 5:** Task #5 (Plans service layer)

### Week 2: Testing & Optimization
- **Day 1-2:** Task #6 (Unit tests)
- **Day 3:** Task #7 (Integration tests)
- **Day 4:** Task #8 (Database indexes)
- **Day 5:** Task #9 (Fix N+1 queries)

### Week 3: Frontend & Documentation
- **Day 1-3:** Task #10 (Component library)
- **Day 4-5:** Documentation updates, code review

---

## Success Criteria

### Code Quality Metrics
- ✅ No file over 500 lines
- ✅ All apps have service layer
- ✅ 80%+ test coverage on services
- ✅ All critical flows have integration tests
- ✅ No N+1 queries in dashboard/list views

### Performance Metrics
- ✅ Database queries optimized (indexes added)
- ✅ Dashboard loads in < 500ms
- ✅ Guest registration in < 200ms
- ✅ API endpoints respond in < 300ms avg

### Maintainability Metrics
- ✅ Clear separation of concerns
- ✅ Business logic in services, not views
- ✅ Reusable components extracted
- ✅ Consistent error handling
- ✅ Comprehensive documentation

---

## Risk Mitigation

**Risk 1: Breaking Changes**
- Mitigation: Write tests before refactoring
- Mitigation: Refactor incrementally, test after each change
- Mitigation: Keep git commits atomic and reversible

**Risk 2: Time Overruns**
- Mitigation: Focus on high-impact refactoring first
- Mitigation: Skip AI module if time-constrained (optional feature)
- Mitigation: Defer frontend refactoring if needed

**Risk 3: Test Coverage Gaps**
- Mitigation: Start with critical business logic tests
- Mitigation: Use coverage reports to identify gaps
- Mitigation: Continuous testing during development

---

## Current Status

**Started:** February 25, 2026
**Phase:** Backend Refactoring (Week 1)
**Current Task:** #1 - Refactor AI Views Module

**Progress:**
- [ ] Task #1: Refactor AI views module
- [ ] Task #2: Refactor admin dashboard views
- [ ] Task #3: Create service layer for accounts app
- [ ] Task #4: Create service layer for invitations app
- [ ] Task #5: Create service layer for plans app
- [ ] Task #6: Add comprehensive unit tests
- [ ] Task #7: Add integration tests
- [ ] Task #8: Database optimization - indexes
- [ ] Task #9: Fix N+1 query issues
- [ ] Task #10: Frontend component library

---

## Next Actions

1. Start Task #1: Refactor AI views module
2. Create views/ subdirectory in ai app
3. Split ai/views.py into focused modules
4. Update imports and URL configurations
5. Test all endpoints still work
6. Commit changes with clear message
