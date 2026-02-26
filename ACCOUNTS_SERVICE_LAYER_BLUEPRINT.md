# Accounts App Service Layer Blueprint

## Overview

**Current State:** 487-line views.py with mixed business logic and presentation logic
**Goal:** Extract business logic into focused service modules

---

## Service Architecture

```
apps/backend/src/apps/accounts/services/
├── __init__.py                    # Export all services
├── authentication_service.py      # User registration, login, logout
├── user_profile_service.py        # Profile management, password changes
├── phone_verification_service.py  # OTP generation and verification
├── plan_service.py               # User plan management
├── activity_service.py           # Activity logging
└── utils.py                      # Common utilities (IP, phone normalization)
```

---

## Service Modules

### 1. `utils.py` - Common Utilities

**Purpose:** Shared utility functions used across services

**Functions:**
- `get_client_ip(request)` - Extract client IP from request
- `normalize_phone(phone)` - Normalize phone number to +91 format
- `get_user_by_identifier(identifier)` - Get user by username or phone

**Dependencies:** None

**Size:** ~50 lines

---

### 2. `activity_service.py` - Activity Logging

**Purpose:** Centralized activity logging for audit trail

**Class:** `ActivityService`

**Methods:**
- `log_activity(user, activity_type, description, request, metadata)` - Log user activity
- `log_login(user, request)` - Log user login
- `log_logout(user, request)` - Log user logout
- `log_registration(user, request)` - Log user registration
- `log_profile_update(user, request)` - Log profile update
- `log_password_change(user, request)` - Log password change
- `log_plan_change_request(user, new_plan, current_plan, request)` - Log plan change request

**Dependencies:**
- `models.UserActivityLog`
- `utils.get_client_ip`

**Size:** ~100 lines

---

### 3. `phone_verification_service.py` - Phone Verification

**Purpose:** Handle OTP generation, sending, and verification

**Class:** `PhoneVerificationService`

**Methods:**
- `normalize_phone(phone)` - Normalize phone number
- `generate_otp()` - Generate 6-digit OTP
- `send_otp(user, phone, request)` - Generate and send OTP via SMS
- `verify_otp(phone, otp)` - Verify OTP and mark phone as verified
- `mark_phone_verified(user)` - Mark user's phone as verified

**Dependencies:**
- `models.PhoneVerification`
- `utils.sms_service.SMSService`
- `utils.get_client_ip`

**Business Logic:**
- OTP generation (6-digit random number)
- OTP expiration (10 minutes)
- Phone normalization (+91 prefix)
- SMS sending via MSG91

**Size:** ~150 lines

---

### 4. `user_profile_service.py` - User Profile Management

**Purpose:** Handle user profile operations

**Class:** `UserProfileService`

**Methods:**
- `get_profile(user)` - Get user profile data
- `update_profile(user, data, request)` - Update user profile
- `change_password(user, old_password, new_password, request)` - Change user password
- `get_profile_stats(user)` - Get user statistics (orders, invitations)

**Dependencies:**
- `models.User`
- `activity_service.ActivityService`

**Business Logic:**
- Profile validation
- Password validation
- Activity logging on changes

**Size:** ~100 lines

---

### 5. `plan_service.py` - Plan Management

**Purpose:** Handle user plan operations

**Class:** `PlanService`

**Methods:**
- `get_user_plan(user)` - Get user's current plan with details
- `update_user_plan(user, plan)` - Update user's current plan
- `request_plan_change(user, new_plan_code, request)` - Request plan change
- `approve_plan_change(user, new_plan, admin)` - Approve plan change request
- `can_access_plan(user, plan_code)` - Check if user can access plan features
- `get_plan_hierarchy()` - Get plan tier hierarchy

**Dependencies:**
- `models.User`
- `apps.plans.models.Plan`
- `apps.invitations.models.Order`
- `activity_service.ActivityService`

**Business Logic:**
- Plan hierarchy (BASIC < PREMIUM < LUXURY)
- Plan change validation
- Order-based plan updates
- Activity logging

**Size:** ~150 lines

---

### 6. `authentication_service.py` - Authentication

**Purpose:** Handle user authentication flows

**Class:** `AuthenticationService`

**Methods:**
- `register_user(phone, username, email, full_name, password, request)` - Register new user
- `authenticate_user(identifier, password, request)` - Authenticate user (login)
- `logout_user(refresh_token, user, request)` - Logout user and blacklist token
- `generate_tokens(user)` - Generate JWT access and refresh tokens
- `validate_user_access(user)` - Check if user can access the platform
- `send_welcome_notifications(user)` - Send welcome email and notify admin

**Dependencies:**
- `models.User`
- `rest_framework_simplejwt.tokens.RefreshToken`
- `apps.admin_dashboard.services.NotificationService`
- `activity_service.ActivityService`
- `utils.get_client_ip`
- `utils.get_user_by_identifier`

**Business Logic:**
- User registration workflow
- Username/phone-based authentication
- Blocked user check
- Approval status check
- Token generation and blacklisting
- IP address tracking
- Admin notification on new user

**Size:** ~250 lines

---

## Benefits

### Before Service Layer:
- ❌ Business logic mixed with view logic
- ❌ Duplicate code across views
- ❌ Hard to test business logic
- ❌ Difficult to reuse logic
- ❌ Views are 487 lines long

### After Service Layer:
- ✅ Clean separation of concerns
- ✅ Reusable business logic
- ✅ Easy to unit test services
- ✅ Views become thin controllers (~200 lines)
- ✅ Clear service contracts
- ✅ Easier maintenance

---

## View Refactoring Example

### Before (views.py):
```python
class LoginView(generics.GenericAPIView):
    def post(self, request):
        # 80+ lines of business logic
        # - User lookup
        # - Password check
        # - Approval check
        # - Token generation
        # - Activity logging
        # - IP tracking
```

### After (views.py):
```python
class LoginView(generics.GenericAPIView):
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Delegate to service
        result = AuthenticationService.authenticate_user(
            identifier=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
            request=request
        )

        return Response(result)
```

---

## Implementation Strategy

### Phase 1: Create Service Files
1. Create `services/` directory
2. Create `utils.py` with common utilities
3. Create `activity_service.py`
4. Create `phone_verification_service.py`
5. Create `user_profile_service.py`
6. Create `plan_service.py`
7. Create `authentication_service.py`
8. Create `__init__.py` with exports

### Phase 2: Refactor Views
1. Update `RegisterView` to use `AuthenticationService`
2. Update `LoginView` to use `AuthenticationService`
3. Update `LogoutView` to use `AuthenticationService`
4. Update `ProfileView` to use `UserProfileService`
5. Update `PasswordChangeView` to use `UserProfileService`
6. Update `SendOTPView` to use `PhoneVerificationService`
7. Update `VerifyOTPView` to use `PhoneVerificationService`
8. Update `MyPlanView` to use `PlanService`
9. Update `RequestPlanChangeView` to use `PlanService`

### Phase 3: Testing
1. Write unit tests for each service
2. Test service methods independently
3. Integration tests for view + service
4. Verify all endpoints work correctly

---

## Service Design Principles

1. **Single Responsibility:** Each service handles one domain
2. **Stateless:** Services don't maintain state between calls
3. **Testable:** Easy to mock dependencies and unit test
4. **Reusable:** Can be used from views, tasks, management commands
5. **Type Hints:** Use type hints for better IDE support
6. **Error Handling:** Services raise specific exceptions
7. **Logging:** Services log important operations
8. **Transaction Safety:** Use database transactions where needed

---

## Service Return Format

All services return consistent dictionary format:

```python
{
    'success': bool,
    'message': str,
    'data': dict | None,
    'error_code': str | None
}
```

For exceptions, services raise specific exceptions that views can catch and convert to responses.

---

## Testing Strategy

### Unit Tests (services/tests/):
```
tests/
├── test_authentication_service.py
├── test_user_profile_service.py
├── test_phone_verification_service.py
├── test_plan_service.py
├── test_activity_service.py
└── test_utils.py
```

### Test Coverage Goals:
- Service methods: 90%+
- Edge cases: All major paths
- Error conditions: All error scenarios
- Integration: Key workflows end-to-end

---

## Migration Risk Mitigation

1. **Create services first** without modifying views
2. **Test services independently** with unit tests
3. **Gradually refactor views** one at a time
4. **Keep backup** of original views.py
5. **Test after each refactor** to ensure no breakage
6. **Run full test suite** before deployment

---

## Expected Metrics

### Views File:
- Before: 487 lines
- After: ~250 lines (48% reduction)

### Services:
- `utils.py`: ~50 lines
- `activity_service.py`: ~100 lines
- `phone_verification_service.py`: ~150 lines
- `user_profile_service.py`: ~100 lines
- `plan_service.py`: ~150 lines
- `authentication_service.py`: ~250 lines
- `__init__.py`: ~30 lines
- **Total:** ~830 lines (well-organized, testable)

---

## Next Steps

1. ✅ Create blueprint document
2. ⏳ Create `services/` directory
3. ⏳ Implement `utils.py`
4. ⏳ Implement `activity_service.py`
5. ⏳ Implement `phone_verification_service.py`
6. ⏳ Implement `user_profile_service.py`
7. ⏳ Implement `plan_service.py`
8. ⏳ Implement `authentication_service.py`
9. ⏳ Implement `__init__.py`
10. ⏳ Refactor views to use services
11. ⏳ Write unit tests
12. ⏳ Integration testing
13. ⏳ Documentation update
