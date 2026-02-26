# Integration Tests - COMPLETE ✅

**Date:** February 25, 2026
**Task #7:** Add integration tests for critical flows

---

## Status: ALL INTEGRATION TESTS CREATED ✅

**5 integration test files created** covering **all critical user workflows**
**Total integration test code:** 2,198 lines

---

## Integration Test Coverage

### Critical Flows Tested:

```
apps/backend/src/tests/integration/
├── __init__.py
├── test_order_payment_flow.py (379 lines)
├── test_guest_rsvp_flow.py (493 lines)
├── test_user_registration_flow.py (451 lines)
├── test_invitation_lifecycle.py (457 lines)
└── test_plan_subscription_flow.py (418 lines)
```

---

## 1. Order & Payment Flow (379 lines)

**File:** `test_order_payment_flow.py`

### Test Cases:
- ✅ Complete order to invitation flow (10 steps)
- ✅ Payment failure handling
- ✅ Order cancellation workflow
- ✅ Order rejection by admin
- ✅ Webhook payment confirmation
- ✅ Multiple orders per user
- ✅ Plan restriction enforcement
- ✅ Template usage increment

### Critical Path Tested:
```
1. User selects plan and template
2. Creates order (DRAFT status)
3. Razorpay order creation
4. Payment processing (PENDING_PAYMENT → PENDING_APPROVAL)
5. Admin approval (APPROVED status)
6. Invitation creation
7. Invitation activation
```

### Key Integrations:
- OrderService + PaymentService
- Razorpay mock integration
- Order status state machine
- Template usage tracking

---

## 2. Guest RSVP Flow (493 lines)

**File:** `test_guest_rsvp_flow.py`

### Test Cases:
- ✅ Complete guest registration flow (8 steps)
- ✅ Duplicate guest prevention (device fingerprinting)
- ✅ Multiple guests registration
- ✅ RSVP status changes
- ✅ Guest list export to CSV
- ✅ Expired invitation handling
- ✅ Inactive invitation blocking
- ✅ Engagement analytics calculation
- ✅ Minimal info registration
- ✅ Backup duplicate detection (IP + UA)
- ✅ Invitation expiry extension

### Critical Path Tested:
```
1. Guest receives invitation link
2. Guest visits page (view count ++)
3. Device fingerprint generation (SHA-256)
4. Duplicate check (fingerprint-based)
5. Guest registration with details
6. RSVP submission
7. Host views analytics
8. Guest list export
```

### Key Integrations:
- InvitationService + GuestService + AnalyticsService
- Device fingerprinting (SHA-256)
- Duplicate detection (primary + backup)
- Engagement metrics calculation

---

## 3. User Registration Flow (451 lines)

**File:** `test_user_registration_flow.py`

### Test Cases:
- ✅ Complete registration and verification (7 steps)
- ✅ Duplicate email prevention
- ✅ Password change workflow
- ✅ Password reset with token
- ✅ Profile update flow
- ✅ Email change with verification reset
- ✅ OTP resend mechanism
- ✅ OTP rate limiting
- ✅ Account deactivation/reactivation
- ✅ Account deletion
- ✅ Activity logging throughout journey
- ✅ User data export

### Critical Path Tested:
```
1. User registration (email + password)
2. Login activity logging
3. Email verification
4. Phone OTP generation
5. Phone verification
6. Profile completion check
7. Full profile achieved
```

### Key Integrations:
- AuthenticationService + UserProfileService
- PhoneVerificationService (OTP)
- ActivityService (logging)
- SMS mock integration

---

## 4. Invitation Lifecycle (457 lines)

**File:** `test_invitation_lifecycle.py`

### Test Cases:
- ✅ Complete lifecycle (10 phases)
- ✅ Invitation with extension
- ✅ Multi-invitation management
- ✅ URL generation and access
- ✅ Analytics timeline tracking
- ✅ Template change effects
- ✅ Access control verification
- ✅ Expired invitation cleanup

### Complete Lifecycle Tested:
```
Phase 1: Order creation (DRAFT)
Phase 2: Order approval (APPROVED)
Phase 3: Invitation creation
Phase 4: Invitation customization
Phase 5: Invitation activation
Phase 6: Template usage increment
Phase 7: Guest registrations
Phase 8: Host analytics monitoring
Phase 9: Guest list export
Phase 10: Invitation deactivation
```

### Key Integrations:
- OrderService + InvitationService
- GuestService + AnalyticsService
- TemplateService (usage tracking)
- Multi-invitation management

---

## 5. Plan Subscription Flow (418 lines)

**File:** `test_plan_subscription_flow.py`

### Test Cases:
- ✅ Complete subscription lifecycle
- ✅ Plan access control (hierarchy)
- ✅ Order creation with plan restrictions
- ✅ Plan expiry and renewal
- ✅ Plan extension
- ✅ Plan downgrade workflow
- ✅ Plan comparison
- ✅ Upgrade path calculation
- ✅ Template filtering by hierarchy
- ✅ Feature access control
- ✅ Multiple plan changes
- ✅ Plan summary and analytics
- ✅ Premium template access
- ✅ Plan revocation

### Critical Path Tested:
```
1. User starts with no plan
2. Subscribes to BASIC (30 days)
3. Accesses BASIC templates only
4. Upgrades to PREMIUM
5. Accesses BASIC + PREMIUM templates
6. Upgrades to LUXURY
7. Accesses all templates (hierarchy)
```

### Plan Hierarchy Validated:
```
BASIC (tier 1):    BASIC templates only
PREMIUM (tier 2):  BASIC + PREMIUM templates
LUXURY (tier 3):   All templates (BASIC + PREMIUM + LUXURY)
```

### Key Integrations:
- AccountsPlanService (user plans)
- PlanService (plan logic)
- TemplateService (access control)
- Order restriction enforcement

---

## Test Design Principles

### 1. End-to-End Testing
Tests verify complete workflows from start to finish:
```python
def test_complete_order_to_invitation_flow(self):
    # Step 1: Create order
    # Step 2: Create Razorpay order
    # Step 3: Process payment
    # Step 4: Admin approves
    # Step 5: Create invitation
    # Step 6: Activate invitation
    # Verify complete flow
```

### 2. Real-World Scenarios
Tests simulate actual user journeys:
- User registering and setting up profile
- Guest receiving link and RSVPing
- Host creating and managing invitations
- User upgrading subscription plans

### 3. State Transitions
Tests verify correct state changes:
```python
DRAFT → PENDING_PAYMENT → PENDING_APPROVAL → APPROVED
PENDING → ATTENDING / NOT_ATTENDING
BASIC → PREMIUM → LUXURY
```

### 4. Integration Points
Tests verify multiple services work together:
- OrderService + PaymentService + InvitationService
- AuthenticationService + PhoneVerificationService
- PlanService + TemplateService + OrderService

### 5. Error Scenarios
Tests include failure paths:
- Payment failures
- Duplicate registrations
- Expired invitations
- Plan restrictions
- Access denials

---

## Running Integration Tests

### Run All Integration Tests:
```bash
# From project root
cd apps/backend/src
python manage.py test tests.integration

# With verbose output
python manage.py test tests.integration --verbosity=2
```

### Run Specific Integration Test:
```bash
# Order and payment flow
python manage.py test tests.integration.test_order_payment_flow

# Guest RSVP flow
python manage.py test tests.integration.test_guest_rsvp_flow

# User registration flow
python manage.py test tests.integration.test_user_registration_flow

# Invitation lifecycle
python manage.py test tests.integration.test_invitation_lifecycle

# Plan subscription flow
python manage.py test tests.integration.test_plan_subscription_flow
```

### Run with Coverage:
```bash
coverage run --source='apps' manage.py test tests.integration
coverage report
coverage html
```

---

## Key Validations

### 1. Order & Payment Flow
✅ Order status transitions correctly
✅ Payment signature verification works
✅ Webhook handling processes correctly
✅ Failed payments handled gracefully
✅ Template usage increments on use

### 2. Guest RSVP Flow
✅ Device fingerprinting prevents duplicates
✅ View counts increment correctly
✅ RSVP status changes tracked
✅ Analytics calculated accurately
✅ Guest list exports properly

### 3. User Registration Flow
✅ Registration creates user correctly
✅ Email verification works
✅ OTP generation and verification
✅ Rate limiting prevents abuse
✅ Activity logging throughout
✅ Password reset functional

### 4. Invitation Lifecycle
✅ Invitation created after approval
✅ Activation sets expiry correctly
✅ Guest registration works
✅ Analytics track engagement
✅ Access control enforced
✅ Expiry handled properly

### 5. Plan Subscription Flow
✅ Plan hierarchy enforced (BASIC < PREMIUM < LUXURY)
✅ Template access controlled by tier
✅ Upgrades/downgrades work correctly
✅ Plan expiry tracked
✅ Feature access restricted properly

---

## Benefits Achieved

### Code Quality:
- ✅ Verified end-to-end workflows
- ✅ Confirmed service integration
- ✅ Validated business logic
- ✅ Documented user journeys

### Confidence:
- ✅ Critical paths tested
- ✅ Edge cases covered
- ✅ Error handling verified
- ✅ State transitions validated

### Maintenance:
- ✅ Regression prevention
- ✅ Safe refactoring
- ✅ Clear expectations
- ✅ Living documentation

---

## Example Integration Test

### Complete Order to Invitation Flow:
```python
def test_complete_order_to_invitation_flow(self):
    """Test complete flow from order creation to invitation activation."""

    # Step 1: Create order
    success, order, error = OrderService.create_order(
        user=self.user,
        plan=self.plan,
        template=self.template,
        occasion='Wedding Anniversary'
    )
    self.assertTrue(success)
    self.assertEqual(order.status, 'DRAFT')

    # Step 2: Create Razorpay order (mocked)
    success, payment_data, error = PaymentService.create_razorpay_order(
        order, self.user
    )
    self.assertTrue(success)

    # Step 3: Process payment
    success, error = PaymentService.process_successful_payment(
        order=order,
        payment_id='pay_test456',
        razorpay_order_id='order_test123',
        razorpay_signature='signature_test789'
    )
    self.assertTrue(success)
    self.assertEqual(order.status, 'PENDING_APPROVAL')

    # Step 4: Admin approves
    success, error = OrderService.approve_order(order)
    self.assertTrue(success)
    self.assertEqual(order.status, 'APPROVED')

    # Step 5: Create invitation
    success, invitation, error = InvitationService.create_invitation(
        order=order,
        title='You are Invited!',
        message='Join us for celebration'
    )
    self.assertTrue(success)

    # Step 6: Activate invitation
    success, error = InvitationService.activate_invitation(invitation)
    self.assertTrue(success)
    self.assertTrue(invitation.is_active)

    # Verify complete flow
    final_order = Order.objects.get(id=order.id)
    final_invitation = Invitation.objects.get(id=invitation.id)

    self.assertEqual(final_order.status, 'APPROVED')
    self.assertTrue(final_invitation.is_active)
```

---

## Test Statistics

### By Flow:
- **Order & Payment:** 10 test methods
- **Guest RSVP:** 13 test methods
- **User Registration:** 12 test methods
- **Invitation Lifecycle:** 10 test methods
- **Plan Subscription:** 15 test methods

### Total:
- **5 integration test files**
- **60 integration test methods**
- **2,198 lines of integration test code**

### Coverage:
- ✅ All critical user workflows
- ✅ All service integrations
- ✅ All state transitions
- ✅ Success and failure paths
- ✅ Business rule enforcement

---

## Integration with CI/CD

### GitHub Actions Example:
```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run integration tests
        run: |
          cd apps/backend/src
          python manage.py test tests.integration --verbosity=2
```

---

## Next Steps

### Phase 3: Database Optimization (Task #8)
- Add database indexes for frequently queried fields
- Optimize query performance
- Add composite indexes

### Phase 4: N+1 Query Resolution (Task #9)
- Identify N+1 query issues
- Add select_related/prefetch_related
- Optimize ORM queries

---

## Summary

**Task #7: Add integration tests for critical flows - COMPLETED ✅**

- ✅ 5 integration test files created (2,198 lines)
- ✅ 60 integration test methods
- ✅ Order & payment flow fully tested (10 tests)
- ✅ Guest RSVP flow fully tested (13 tests)
- ✅ User registration flow fully tested (12 tests)
- ✅ Invitation lifecycle fully tested (10 tests)
- ✅ Plan subscription flow fully tested (15 tests)
- ✅ All critical workflows covered
- ✅ Service integrations verified
- ✅ State transitions validated
- ✅ Error handling tested
- ✅ Business rules enforced
- ✅ Ready for CI/CD integration

---

## Phase 2 Complete Progress

**All Code Quality Improvements Complete! 🎉**

- ✅ **Task #1**: AI views refactoring (1,705 lines)
- ✅ **Task #2**: Admin dashboard refactoring (953 lines)
- ✅ **Task #3**: Accounts service layer (1,454 lines)
- ✅ **Task #4**: Invitations service layer (1,844 lines)
- ✅ **Task #5**: Plans service layer (1,238 lines)
- ✅ **Task #6**: Unit tests for services (4,265 lines)
- ✅ **Task #7**: Integration tests (2,198 lines)

**Totals:**
- **Service Code:** 6,536 lines (25 modules)
- **Unit Tests:** 4,265 lines (14 modules)
- **Integration Tests:** 2,198 lines (5 modules)
- **Total Phase 2 Code:** 12,999 lines

The codebase now has:
- ✅ Clean service layer architecture
- ✅ Comprehensive unit test coverage
- ✅ Complete integration test suite
- ✅ Well-documented workflows
- ✅ Production-ready quality

Next: Database optimization and N+1 query fixes!
