# Invitations App Service Layer Blueprint

## Overview

**Current State:** 720 lines across 3 view files with mixed business logic
**Goal:** Extract business logic into focused service modules

---

## Current Files Analysis

```
views.py - 266 lines
├── Order views (OrderListView, OrderDetailView, OrderCreateView)
├── Invitation views (InvitationListView, InvitationDetailView, etc.)
└── Guest views (GuestListView, ExportGuestsView)

payment_views.py - 175 lines
├── Razorpay order creation
├── Payment verification
└── Webhook handling

public_views.py - 279 lines
├── Public invitation viewing
├── Guest status checking
├── Guest registration (with device fingerprinting)
└── RSVP updates

Total: 720 lines
```

---

## Service Architecture

```
apps/backend/src/apps/invitations/services/
├── __init__.py                 # Export all services
├── utils.py                    # Common utilities
├── order_service.py            # Order management
├── invitation_service.py       # Invitation management
├── guest_service.py            # Guest registration & tracking
├── payment_service.py          # Razorpay payment integration
└── analytics_service.py        # Statistics & reporting
```

---

## Service Modules

### 1. `utils.py` - Common Utilities

**Purpose:** Shared utility functions

**Functions:**
- `get_client_ip(request)` - Extract client IP
- `get_user_agent(request)` - Extract user agent
- `generate_order_number()` - Generate unique order number
- `generate_slug()` - Generate unique invitation slug

**Dependencies:** None

**Size:** ~70 lines

---

### 2. `order_service.py` - Order Management

**Purpose:** Handle order lifecycle and business rules

**Class:** `OrderService`

**Methods:**
- `create_order(user, plan_code, event_type, event_name, request)` - Create new order
- `get_user_orders(user)` - List user's orders
- `get_order_details(order_id, user)` - Get order by ID
- `can_user_order_plan(user, plan_code)` - Validate plan ordering rules
- `approve_order(order, admin, notes)` - Approve order
- `reject_order(order, admin, reason)` - Reject order
- `grant_additional_links(order, regular, test, admin)` - Grant bonus links
- `get_order_summary(order)` - Get order summary with stats
- `update_order_status(order, new_status, admin)` - Update order status

**Dependencies:**
- `models.Order`, `models.OrderStatus`
- `apps.plans.models.Plan`
- `apps.accounts.services.ActivityService`
- `invitation_service.InvitationService` (for activation)

**Business Logic:**
- Plan lock validation (users can only reorder current plan)
- First order sets user's current plan
- Order number generation
- Link count management
- Status workflow enforcement
- Activity logging

**Size:** ~250 lines

---

### 3. `invitation_service.py` - Invitation Management

**Purpose:** Handle invitation lifecycle

**Class:** `InvitationService`

**Methods:**
- `create_invitation(order, template, event_data, media_data, user)` - Create invitation
- `update_invitation(invitation, data, user)` - Update invitation details
- `get_user_invitations(user)` - List user's invitations
- `get_invitation_by_slug(slug, user)` - Get invitation by slug
- `get_public_invitation(slug)` - Get invitation for public viewing
- `activate_invitation(invitation)` - Activate after approval
- `expire_invitation(invitation)` - Mark as expired
- `check_invitation_validity(invitation)` - Validate if still accessible
- `increment_view_count(invitation, request)` - Track views
- `log_invitation_view(invitation, request)` - Log view details
- `can_edit_invitation(invitation)` - Check edit permissions

**Dependencies:**
- `models.Invitation`, `models.InvitationViewLog`
- `apps.plans.models.Template`
- `utils.generate_slug`

**Business Logic:**
- Slug generation (unique 10-char nanoid)
- Link expiry calculation (configurable validity period)
- View tracking
- Active/expired state management
- Media upload handling
- Share URL generation

**Size:** ~200 lines

---

### 4. `guest_service.py` - Guest Management

**Purpose:** Handle guest registration with anti-fraud measures

**Class:** `GuestService`

**Methods:**
- `register_guest(invitation, name, phone, message, device_data, request)` - Register new guest
- `check_existing_guest(invitation, fingerprint, ip_address)` - Check for duplicates
- `generate_device_fingerprint(device_data)` - Create device fingerprint
- `parse_user_agent(user_agent)` - Parse browser/OS info
- `can_register_guest(invitation, is_test)` - Validate registration eligibility
- `update_rsvp(invitation, fingerprint, attending)` - Update RSVP status
- `get_invitation_guests(invitation, user)` - List guests for invitation
- `export_guests_csv(invitation, user)` - Export guests to CSV

**Dependencies:**
- `models.Guest`, `models.Invitation`
- `user_agents` library for parsing
- `hashlib` for fingerprinting

**Business Logic:**
- Device fingerprinting (SHA-256 hash)
  - User agent
  - Screen resolution
  - Timezone offset
  - Languages
  - Canvas hash
- Duplicate detection:
  1. By fingerprint (primary)
  2. By IP + User Agent (backup)
- Link limit enforcement
- Test vs regular link tracking
- User agent parsing for analytics

**Size:** ~250 lines

---

### 5. `payment_service.py` - Payment Integration

**Purpose:** Handle Razorpay payment processing

**Class:** `PaymentService`

**Methods:**
- `create_razorpay_order(order, user)` - Create Razorpay order
- `verify_payment_signature(payment_data)` - Verify payment signature
- `process_payment_success(order, payment_id, payment_method)` - Handle successful payment
- `process_webhook_payment(webhook_data)` - Process webhook callback
- `get_razorpay_client()` - Get initialized Razorpay client
- `prepare_payment_prefill(user)` - Prepare user data for checkout

**Dependencies:**
- `models.Order`, `models.OrderStatus`
- `razorpay` SDK
- `django.conf.settings`

**Business Logic:**
- Razorpay order creation (amount in paise)
- Signature verification
- Webhook validation
- Order status transitions:
  - DRAFT/PENDING_PAYMENT → PENDING_APPROVAL (on payment)
- Payment metadata tracking
- Admin notification on payment received

**Configuration:**
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `RAZORPAY_WEBHOOK_SECRET`

**Size:** ~150 lines

---

### 6. `analytics_service.py` - Statistics & Reporting

**Purpose:** Generate statistics and reports

**Class:** `AnalyticsService`

**Methods:**
- `get_invitation_stats(invitation, user)` - Get invitation statistics
- `get_order_stats(order, user)` - Get order statistics
- `get_user_dashboard_stats(user)` - Get user's overall stats
- `export_guests_to_csv(invitation, user)` - Generate CSV export
- `get_guest_analytics(invitation, user)` - Detailed guest analytics
- `get_device_breakdown(invitation, user)` - Device type statistics
- `get_view_timeline(invitation, user)` - View trends over time

**Dependencies:**
- `models.Invitation`, `models.Guest`, `models.Order`, `models.InvitationViewLog`

**Statistics Generated:**
- **Invitation Stats:**
  - Total views
  - Unique guests
  - Link usage (regular/test)
  - Remaining links
  - Expiry countdown
  - RSVP counts
- **Order Stats:**
  - Payment status
  - Approval status
  - Link allocations
  - Link usage
- **Guest Analytics:**
  - Device breakdown (mobile/desktop/tablet)
  - Browser distribution
  - OS distribution
  - Geographic distribution (by IP)
  - View timeline

**Size:** ~180 lines

---

## Benefits

### Before Service Layer:
- ❌ 720 lines across 3 files with mixed concerns
- ❌ Business logic in views and models
- ❌ Duplicate code (IP extraction, fingerprinting)
- ❌ Hard to test payment logic
- ❌ Guest registration logic complex and in views
- ❌ No clear separation of concerns

### After Service Layer:
- ✅ ~1,100 lines of organized, reusable code
- ✅ Clear separation: views (HTTP) vs services (business logic)
- ✅ Easy to unit test each service independently
- ✅ Services reusable from tasks, management commands
- ✅ Complex logic (fingerprinting, payment) isolated
- ✅ Better error handling and logging
- ✅ Clear service contracts

---

## Key Business Logic to Extract

### Order Management:
1. **Plan Lock Validation**
   - Users locked to current plan
   - Can only reorder same plan
   - Plan change requires admin approval

2. **Order Number Generation**
   - Format: `ORD-YYYYMMDD-RANDOM`
   - Unique constraint

3. **Link Management**
   - Regular links (from plan)
   - Test links (default 5)
   - Admin can grant additional links

4. **Status Workflow**
   - DRAFT → PENDING_PAYMENT → PENDING_APPROVAL → APPROVED
   - Can also be REJECTED, EXPIRED, CANCELLED

### Invitation Management:
1. **Slug Generation**
   - 10-character nanoid
   - Unique constraint

2. **Link Validity**
   - Configurable validity period (default 15 days)
   - Auto-expiry check
   - Manual expiry option

3. **Activation**
   - Happens after order approval
   - Sets expiry date
   - Activates link

### Guest Registration:
1. **Device Fingerprinting**
   - SHA-256 hash of:
     - User agent
     - Screen resolution
     - Timezone offset
     - Languages
     - Canvas hash

2. **Duplicate Detection**
   - Primary: Fingerprint match
   - Backup: IP + User Agent (30 days)

3. **Link Limits**
   - Enforces regular link limit
   - Enforces test link limit
   - Prevents over-registration

### Payment Processing:
1. **Razorpay Integration**
   - Create order (amount in paise)
   - Verify signature
   - Process webhook

2. **Order Status Update**
   - On payment: PENDING_APPROVAL
   - Payment metadata stored

---

## Migration Strategy

### Phase 1: Create Services
1. Create `services/` directory
2. Implement `utils.py`
3. Implement `order_service.py`
4. Implement `invitation_service.py`
5. Implement `guest_service.py`
6. Implement `payment_service.py`
7. Implement `analytics_service.py`
8. Create `__init__.py` with exports

### Phase 2: Test Services (Optional)
1. Write unit tests for each service
2. Mock dependencies
3. Test edge cases

### Phase 3: Refactor Views (Optional)
1. Update views to use services
2. Thin controllers pattern
3. Maintain backward compatibility

---

## Expected Metrics

### Views Files:
- Before: 720 lines total
- After: ~400 lines (44% reduction)

### Services:
- `utils.py`: ~70 lines
- `order_service.py`: ~250 lines
- `invitation_service.py`: ~200 lines
- `guest_service.py`: ~250 lines
- `payment_service.py`: ~150 lines
- `analytics_service.py`: ~180 lines
- `__init__.py`: ~40 lines
- **Total:** ~1,140 lines (well-organized, testable)

---

## Service Design Principles

1. **Stateless:** No instance state between calls
2. **Transaction Safety:** Use `@transaction.atomic` where needed
3. **Error Handling:** Try-except with logging
4. **Return Format:** Consistent `(success, data, error)` tuples
5. **Type Hints:** All parameters and returns typed
6. **Logging:** All errors and important operations logged
7. **Testable:** Easy to mock and unit test

---

## Complex Logic Examples

### Device Fingerprinting Logic (guest_service.py):
```python
@staticmethod
def generate_device_fingerprint(user_agent, screen_resolution,
                                timezone_offset, languages, canvas_hash=''):
    """
    Generate unique device fingerprint.

    Combines multiple browser characteristics:
    - User agent string
    - Screen resolution (width x height)
    - Timezone offset (-420, +330, etc.)
    - Browser languages (en-US,en;q=0.9)
    - Canvas fingerprint hash

    Returns: SHA-256 hash
    """
    data = f"{user_agent}|{screen_resolution}|{timezone_offset}|{languages}|{canvas_hash}"
    return hashlib.sha256(data.encode()).hexdigest()
```

### Order Plan Validation Logic (order_service.py):
```python
@staticmethod
def can_user_order_plan(user, plan_code):
    """
    Check if user can order a specific plan.

    Rules:
    - If user has no current plan: Can order any plan
    - If user has current plan: Can only reorder same plan
    - To change plans: Must request via admin

    Returns: (can_order, reason_if_not)
    """
    if not user.current_plan:
        return True, None

    if plan_code.upper() != user.current_plan.code:
        return False, f"You are locked to {user.current_plan.name}. Contact admin to change plans."

    return True, None
```

### Invitation Activation Logic (invitation_service.py):
```python
@staticmethod
def activate_invitation(invitation):
    """
    Activate invitation after order approval.

    - Sets is_active = True
    - Calculates expiry date (validity period from settings)
    - Saves invitation

    Returns: (success, error_message)
    """
    from django.conf import settings
    validity_days = settings.INVITATION_SETTINGS.get('LINK_VALIDITY_DAYS', 15)

    invitation.is_active = True
    invitation.link_expires_at = timezone.now() + timedelta(days=validity_days)
    invitation.save(update_fields=['is_active', 'link_expires_at'])

    return True, None
```

---

## Next Steps

1. ✅ Create blueprint document
2. ⏳ Create `services/` directory
3. ⏳ Implement `utils.py`
4. ⏳ Implement `order_service.py`
5. ⏳ Implement `invitation_service.py`
6. ⏳ Implement `guest_service.py`
7. ⏳ Implement `payment_service.py`
8. ⏳ Implement `analytics_service.py`
9. ⏳ Implement `__init__.py`
10. ⏳ (Optional) Refactor views
11. ⏳ (Optional) Write unit tests

---

## Integration Points

### With Other Apps:
- **accounts app:** User model, ActivityService
- **plans app:** Plan, Template models
- **admin_dashboard app:** NotificationService (admin alerts)

### External Services:
- **Razorpay:** Payment processing
- **MSG91/Twilio:** (Future) SMS notifications to guests
- **AWS S3/CloudFront:** Media storage (future)

---

## Security Considerations

1. **Device Fingerprinting:** Anti-fraud measure to prevent spam
2. **Payment Verification:** Signature validation for Razorpay
3. **Webhook Security:** Signature verification for webhooks
4. **IP Logging:** Track all guest registrations
5. **Rate Limiting:** (Future) Prevent brute-force registrations

---

## Performance Optimizations

1. **select_related/prefetch_related:** In query methods
2. **Bulk Operations:** When updating multiple guests
3. **Index Usage:** Device fingerprint, IP address indexed
4. **Caching:** (Future) Cache public invitation data

---

## Testing Strategy

### Unit Tests:
- Each service method tested independently
- Mock external dependencies (Razorpay, etc.)
- Test edge cases and error conditions

### Integration Tests:
- Full workflows (order → payment → approval → invitation)
- Guest registration flow
- Payment webhook processing

### Test Coverage Goals:
- Services: 85%+
- Critical paths: 100%
