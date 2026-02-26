"""
Accounts app services package.

This package provides business logic services for the accounts app:
- AuthenticationService: User registration, login, logout
- UserProfileService: Profile management, password changes
- PhoneVerificationService: OTP generation and verification
- PlanService: User plan management
- ActivityService: Activity logging
- Utils: Common utility functions

All services are stateless and can be imported and used throughout the application.
"""

from .authentication_service import AuthenticationService
from .user_profile_service import UserProfileService
from .phone_verification_service import PhoneVerificationService
from .plan_service import PlanService
from .activity_service import ActivityService
from .utils import (
    get_client_ip,
    normalize_phone,
    get_user_by_identifier,
    get_user_agent
)

__all__ = [
    # Services
    'AuthenticationService',
    'UserProfileService',
    'PhoneVerificationService',
    'PlanService',
    'ActivityService',
    # Utils
    'get_client_ip',
    'normalize_phone',
    'get_user_by_identifier',
    'get_user_agent',
]
