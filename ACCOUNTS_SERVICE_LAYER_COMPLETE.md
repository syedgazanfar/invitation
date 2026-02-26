# Accounts App Service Layer - COMPLETE

## Status: SERVICE LAYER CREATED ✅

**Date:** February 25, 2026
**Original views.py:** 487 lines with mixed business logic
**Service Layer:** 7 files, 1,454 lines of well-organized business logic

---

## Created Service Files

```
apps/backend/src/apps/accounts/services/
├── __init__.py (39 lines) - Package exports
├── utils.py (104 lines) - Common utilities
├── activity_service.py (235 lines) - Activity logging
├── phone_verification_service.py (211 lines) - OTP verification
├── user_profile_service.py (239 lines) - Profile management
├── plan_service.py (294 lines) - Plan management
└── authentication_service.py (332 lines) - Authentication

Total: 1,454 lines of testable business logic
```

---

## Service Breakdown

### 1. utils.py (104 lines)
**Purpose:** Common utility functions used across services

**Functions:**
- `get_client_ip(request)` - Extract client IP from request
- `normalize_phone(phone)` - Normalize phone to +91 format
- `get_user_by_identifier(identifier)` - Get user by username or phone
- `get_user_agent(request)` - Extract user agent string

**Dependencies:** None

**Key Features:**
- Phone normalization with +91 prefix
- Flexible user lookup (username or phone)
- IP extraction with X-Forwarded-For support

---

### 2. activity_service.py (235 lines)
**Purpose:** Centralized activity logging for audit trail

**Class:** `ActivityService`

**Methods:**
- `log_activity()` - General activity logging
- `log_login()` - Log user login
- `log_logout()` - Log user logout
- `log_registration()` - Log user registration
- `log_profile_update()` - Log profile updates
- `log_password_change()` - Log password changes
- `log_plan_change_request()` - Log plan change requests
- `log_order_created()` - Log order creation
- `log_invitation_created()` - Log invitation creation
- `log_invitation_shared()` - Log invitation sharing

**Dependencies:**
- `models.UserActivityLog`
- `utils.get_client_ip`, `utils.get_user_agent`

**Key Features:**
- Automatic IP and user agent tracking
- Structured metadata storage (JSON)
- Error handling (doesn't break app on logging failure)
- Supports all ActivityType enums

---

### 3. phone_verification_service.py (211 lines)
**Purpose:** Handle OTP generation, sending, and verification

**Class:** `PhoneVerificationService`

**Constants:**
- `OTP_LENGTH = 6` - OTP digit length
- `OTP_EXPIRY_MINUTES = 10` - OTP validity period

**Methods:**
- `generate_otp()` - Generate 6-digit random OTP
- `create_otp_record()` - Create OTP verification record
- `send_otp()` - Generate and send OTP via SMS
- `verify_otp()` - Verify OTP and mark phone verified
- `mark_phone_verified()` - Mark user's phone as verified
- `get_otp_status()` - Get OTP status for user

**Dependencies:**
- `models.PhoneVerification`
- `utils.sms_service.SMSService`
- `utils.normalize_phone`, `utils.get_client_ip`

**Key Features:**
- Random 6-digit OTP generation
- 10-minute expiration
- SMS sending via MSG91 (or dev mode without SMS)
- Phone normalization
- OTP usage tracking
- IP address logging

**Return Format:**
- `send_otp()` returns: `(success, otp, error_message)`
- `verify_otp()` returns: `(success, user, error_message)`

---

### 4. user_profile_service.py (239 lines)
**Purpose:** Handle user profile operations

**Class:** `UserProfileService`

**Methods:**
- `get_profile()` - Get user profile data
- `update_profile()` - Update user profile fields
- `change_password()` - Change user password
- `get_profile_stats()` - Get user statistics
- `can_user_login()` - Check if user can access platform
- `update_last_login_ip()` - Update login IP
- `set_signup_ip()` - Set signup IP

**Updatable Fields:**
- `username`, `email`, `full_name`

**Dependencies:**
- `models.User`
- `activity_service.ActivityService`
- `apps.invitations.models.Order`

**Key Features:**
- Field-level update tracking
- Password validation
- Activity logging on changes
- Comprehensive statistics (orders, invitations)
- Login eligibility checks (blocked, approval status)
- IP tracking

**Return Format:**
- `update_profile()` returns: `(success, user, error_message)`
- `change_password()` returns: `(success, error_message)`
- `can_user_login()` returns: `(can_login, reason_if_not)`

---

### 5. plan_service.py (294 lines)
**Purpose:** Handle user plan operations

**Class:** `PlanService`

**Constants:**
- `PLAN_HIERARCHY = {'BASIC': 1, 'PREMIUM': 2, 'LUXURY': 3}`

**Methods:**
- `get_user_plan()` - Get user's current plan with details
- `update_user_plan()` - Update user's current plan
- `request_plan_change()` - Request plan change (requires admin approval)
- `approve_plan_change()` - Approve plan change request
- `reject_plan_change()` - Reject plan change request
- `can_access_plan()` - Check if user can access plan features
- `get_plan_hierarchy()` - Get plan tier hierarchy
- `get_available_plans_for_user()` - Get upgrade/downgrade options

**Dependencies:**
- `models.User`
- `apps.plans.models.Plan`
- `apps.invitations.models.Order`
- `activity_service.ActivityService`

**Key Features:**
- Automatic plan sync from orders
- Plan hierarchy-based access control
- Plan change request workflow
- Activity logging for plan changes
- Upgrade/downgrade suggestions

**Business Logic:**
- Users can access their plan tier and below
- Plan change requires admin approval
- Checks for duplicate requests
- Validates plan exists and is active

**Return Format:**
- `request_plan_change()` returns: `(success, plan_data, error_message)`
- `approve_plan_change()` returns: `(success, error_message)`
- `reject_plan_change()` returns: `(success, error_message)`

---

### 6. authentication_service.py (332 lines)
**Purpose:** Handle user authentication flows

**Class:** `AuthenticationService`

**Methods:**
- `register_user()` - Register new user
- `authenticate_user()` - Authenticate user (login)
- `logout_user()` - Logout and blacklist token
- `generate_tokens()` - Generate JWT tokens
- `validate_user_access()` - Check platform access
- `send_welcome_notifications()` - Send welcome emails
- `get_user_info()` - Get comprehensive user info
- `refresh_access_token()` - Refresh access token

**Dependencies:**
- `models.User`
- `rest_framework_simplejwt.tokens.RefreshToken`
- `apps.admin_dashboard.services.NotificationService`
- `activity_service.ActivityService`
- `user_profile_service.UserProfileService`
- `utils.get_user_by_identifier`, `utils.get_client_ip`

**Key Features:**
- Username or phone-based authentication
- Phone normalization during registration
- Password validation
- JWT token generation and blacklisting
- Blocked user checks
- Approval status validation
- IP tracking (signup and login)
- Welcome notifications (user + admin)
- Activity logging

**Business Logic:**
- Registration creates user and sends notifications
- Login checks: password, blocked status, approval status
- Logout blacklists refresh token
- Superusers and staff bypass approval checks

**Return Format:**
- `register_user()` returns: `(success, response_data, error_message)`
- `authenticate_user()` returns: `(success, response_data, error_message)`
- `logout_user()` returns: `(success, error_message)`
- `validate_user_access()` returns: `(can_access, error_message, error_code)`

---

## Benefits Achieved

### Before Service Layer:
- ❌ 487-line views.py with mixed concerns
- ❌ Business logic scattered in views
- ❌ Duplicate code (phone normalization, IP extraction, etc.)
- ❌ Hard to test business logic
- ❌ Difficult to reuse logic from other parts of app
- ❌ No clear separation of concerns

### After Service Layer:
- ✅ Clean separation: views (presentation) vs services (business logic)
- ✅ 1,454 lines of organized, reusable code
- ✅ Easy to unit test each service independently
- ✅ Services can be used from views, tasks, management commands
- ✅ Clear service contracts with type hints
- ✅ Consistent error handling
- ✅ Comprehensive documentation

---

## Service Design Principles Applied

1. **Single Responsibility:** Each service handles one domain
   - AuthenticationService: Only authentication
   - PlanService: Only plan management
   - etc.

2. **Stateless:** Services don't maintain state between calls
   - All data passed as parameters
   - No instance variables

3. **Testable:** Easy to mock dependencies and unit test
   - Services use other services (dependency injection)
   - Clear input/output contracts

4. **Reusable:** Can be used anywhere
   - From views (HTTP layer)
   - From Celery tasks (background jobs)
   - From management commands (CLI)
   - From admin actions

5. **Type Hints:** Better IDE support
   - All parameters and returns have type hints
   - Easier to understand expected data

6. **Error Handling:** Services handle errors gracefully
   - Try-except blocks for unexpected errors
   - Logging of errors
   - Return tuples with success/error indicators

7. **Transaction Safety:** Database operations are atomic
   - Use `transaction.atomic()` where needed
   - Ensures data consistency

---

## Next Steps

### Phase 1: COMPLETED ✅
- ✅ Create `services/` directory
- ✅ Implement `utils.py`
- ✅ Implement `activity_service.py`
- ✅ Implement `phone_verification_service.py`
- ✅ Implement `user_profile_service.py`
- ✅ Implement `plan_service.py`
- ✅ Implement `authentication_service.py`
- ✅ Implement `__init__.py`

### Phase 2: Refactor Views (PENDING)
1. ⏳ Update `RegisterView` to use `AuthenticationService`
2. ⏳ Update `LoginView` to use `AuthenticationService`
3. ⏳ Update `LogoutView` to use `AuthenticationService`
4. ⏳ Update `ProfileView` to use `UserProfileService`
5. ⏳ Update `PasswordChangeView` to use `UserProfileService`
6. ⏳ Update `SendOTPView` to use `PhoneVerificationService`
7. ⏳ Update `VerifyOTPView` to use `PhoneVerificationService`
8. ⏳ Update `MyPlanView` to use `PlanService`
9. ⏳ Update `RequestPlanChangeView` to use `PlanService`

### Phase 3: Testing (PENDING)
1. ⏳ Write unit tests for each service
2. ⏳ Test service methods independently
3. ⏳ Integration tests for view + service
4. ⏳ Verify all endpoints work correctly

---

## Usage Examples

### Example 1: Using AuthenticationService

```python
from apps.accounts.services import AuthenticationService

# Register a new user
success, data, error = AuthenticationService.register_user(
    phone="+919876543210",
    username="john_doe",
    email="john@example.com",
    full_name="John Doe",
    password="SecurePass123!",
    request=request
)

if success:
    print(f"Access token: {data['access']}")
    print(f"User ID: {data['user']['id']}")
else:
    print(f"Error: {error}")
```

### Example 2: Using PhoneVerificationService

```python
from apps.accounts.services import PhoneVerificationService

# Send OTP
success, otp, error = PhoneVerificationService.send_otp(
    user=user,
    phone="+919876543210",
    request=request
)

if success:
    print(f"OTP sent! (Dev mode OTP: {otp})")

# Verify OTP
success, user, error = PhoneVerificationService.verify_otp(
    phone="+919876543210",
    otp="123456"
)

if success:
    print(f"Phone verified for user: {user.username}")
```

### Example 3: Using PlanService

```python
from apps.accounts.services import PlanService

# Request plan change
success, plan_data, error = PlanService.request_plan_change(
    user=user,
    new_plan_code="PREMIUM",
    request=request
)

if success:
    print(f"Plan change requested to: {plan_data['name']}")

# Check plan access
can_access = PlanService.can_access_plan(user, "PREMIUM")
print(f"Can access PREMIUM: {can_access}")
```

---

## Testing Strategy

### Unit Tests Location:
```
apps/backend/src/apps/accounts/tests/
├── test_authentication_service.py
├── test_user_profile_service.py
├── test_phone_verification_service.py
├── test_plan_service.py
├── test_activity_service.py
└── test_utils.py
```

### Test Coverage Goals:
- **Service methods:** 90%+ coverage
- **Edge cases:** All major code paths
- **Error conditions:** All error scenarios
- **Integration:** Key workflows end-to-end

### Key Test Cases:
1. **AuthenticationService:**
   - Register with valid data
   - Register with duplicate phone/username
   - Login with username/phone
   - Login with wrong password
   - Login blocked user
   - Login unapproved user

2. **PhoneVerificationService:**
   - Generate and send OTP
   - Verify valid OTP
   - Verify expired OTP
   - Verify used OTP
   - Mark phone verified

3. **PlanService:**
   - Request plan change
   - Duplicate plan change request
   - Plan access control (hierarchy)
   - Approve/reject plan change

4. **UserProfileService:**
   - Update profile fields
   - Change password (valid/invalid)
   - Check login eligibility

5. **ActivityService:**
   - Log various activity types
   - Handle logging failures gracefully

---

## File Size Comparison

### Before:
- `views.py`: 487 lines (mixed concerns)

### After:
- `views.py`: 487 lines (will be reduced to ~250 lines after refactoring)
- `services/`: 1,454 lines (pure business logic)

**Note:** While total lines increased, the code is now:
- Better organized
- Easily testable
- Highly reusable
- Well documented
- Maintainable

---

## Performance Considerations

1. **Database Queries:** Services use `select_related` where appropriate
2. **Transactions:** Atomic operations for data consistency
3. **Caching:** Can add caching layer in services if needed
4. **N+1 Queries:** Will be addressed in separate optimization task

---

## Security Features

1. **Password Validation:** Uses Django's password validators
2. **Phone Normalization:** Consistent format prevents duplicates
3. **Token Blacklisting:** Logout invalidates refresh tokens
4. **Activity Logging:** Complete audit trail
5. **IP Tracking:** Security and analytics
6. **Approval Workflow:** Admin verification before access

---

## API Response Format

All service methods return consistent formats:

### Success Response:
```python
(True, data_dict, None)
```

### Error Response:
```python
(False, None, "Error message")
```

### Validation Response:
```python
(can_proceed, reason_if_not, optional_error_code)
```

---

## Summary

**Task #3: Create Service Layer for Accounts App - PHASE 1 COMPLETE ✅**

- ✅ 7 service files created (1,454 lines)
- ✅ Clean separation of concerns
- ✅ Comprehensive business logic coverage
- ✅ Type hints and documentation
- ✅ Error handling and logging
- ✅ Transaction safety
- ⏳ Views refactoring (Phase 2)
- ⏳ Unit tests (Phase 3)

The service layer is ready for use! Next step is to refactor views.py to use these services, which will reduce views.py from 487 to ~250 lines.
