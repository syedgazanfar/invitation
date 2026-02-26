"""
Authentication service for user registration, login, and logout.

This service handles all authentication-related operations including token management.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken

from .activity_service import ActivityService
from .user_profile_service import UserProfileService
from .utils import get_user_by_identifier, get_client_ip

# Import admin notification service
try:
    from apps.admin_dashboard.services import NotificationService
except ImportError:
    NotificationService = None

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthenticationService:
    """Service for user authentication operations."""

    @staticmethod
    def register_user(
        phone: str,
        username: str,
        email: str,
        full_name: str,
        password: str,
        request = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Register a new user.

        Args:
            phone: Phone number (will be normalized)
            username: Username
            email: Email address
            full_name: User's full name
            password: Password
            request: Django request object

        Returns:
            Tuple of (success, response_data, error_message)
            response_data contains: tokens, user info
        """
        from .utils import normalize_phone

        try:
            # Normalize phone
            normalized_phone = normalize_phone(phone)

            # Check if user exists
            if User.objects.filter(phone=normalized_phone).exists():
                return False, None, "A user with this phone number already exists"

            if User.objects.filter(username=username).exists():
                return False, None, "A user with this username already exists"

            # Validate password
            try:
                validate_password(password)
            except ValidationError as e:
                return False, None, ', '.join(e.messages)

            # Create user
            with transaction.atomic():
                user = User.objects.create_user(
                    phone=normalized_phone,
                    username=username,
                    email=email,
                    full_name=full_name,
                    password=password
                )

                # Set signup IP
                UserProfileService.set_signup_ip(user, request)

                # Send welcome notifications
                AuthenticationService.send_welcome_notifications(user)

                # Log activity
                ActivityService.log_registration(user, request)

            # Generate tokens
            tokens = AuthenticationService.generate_tokens(user)

            response_data = {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': {
                    'id': str(user.id),
                    'phone': user.phone,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_phone_verified': user.is_phone_verified,
                    'is_approved': user.is_approved
                }
            }

            return True, response_data, None

        except Exception as e:
            logger.error(f"Error in register_user: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def authenticate_user(
        identifier: str,
        password: str,
        request = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Authenticate user with username or phone and password.

        Args:
            identifier: Username or phone number
            password: Password
            request: Django request object

        Returns:
            Tuple of (success, response_data, error_message)
            response_data contains: tokens, user info
        """
        try:
            # Find user by username or phone
            user = get_user_by_identifier(identifier)

            if not user:
                return False, None, "Invalid credentials"

            # Check password
            if not user.check_password(password):
                return False, None, "Invalid credentials"

            # Validate user can access platform
            can_login, reason = UserProfileService.can_user_login(user)
            if not can_login:
                return False, None, reason

            # Update last login IP
            UserProfileService.update_last_login_ip(user, request)

            # Generate tokens
            tokens = AuthenticationService.generate_tokens(user)

            # Log activity
            ActivityService.log_login(user, request)

            response_data = {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': {
                    'id': str(user.id),
                    'phone': user.phone,
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'is_phone_verified': user.is_phone_verified,
                    'is_approved': user.is_approved,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'current_plan': {
                        'code': user.current_plan.code,
                        'name': user.current_plan.name
                    } if user.current_plan else None
                }
            }

            return True, response_data, None

        except Exception as e:
            logger.error(f"Error in authenticate_user: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def logout_user(
        refresh_token: str,
        user: User,
        request = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Logout user by blacklisting the refresh token.

        Args:
            refresh_token: Refresh token to blacklist
            user: User logging out
            request: Django request object

        Returns:
            Tuple of (success, error_message)
        """
        try:
            if not refresh_token:
                return False, "Refresh token is required"

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()

            # Log activity
            ActivityService.log_logout(user, request)

            return True, None

        except Exception as e:
            logger.error(f"Error in logout_user: {e}", exc_info=True)
            return False, "Invalid token"

    @staticmethod
    def generate_tokens(user: User) -> Dict[str, str]:
        """
        Generate JWT access and refresh tokens for a user.

        Args:
            user: User to generate tokens for

        Returns:
            Dictionary with 'access' and 'refresh' tokens
        """
        refresh = RefreshToken.for_user(user)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        }

    @staticmethod
    def validate_user_access(user: User) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate if user can access the platform.

        Args:
            user: User to validate

        Returns:
            Tuple of (can_access, error_message, error_code)
        """
        # Check if user is blocked
        if user.is_blocked:
            return False, "Your account has been blocked. Please contact support.", "ACCOUNT_BLOCKED"

        # Check if user is approved (skip for superusers and staff)
        if not user.is_approved and not user.is_superuser and not user.is_staff:
            return (
                False,
                "Your account is pending admin approval. Please wait for verification or contact support.",
                "PENDING_APPROVAL"
            )

        return True, None, None

    @staticmethod
    def send_welcome_notifications(user: User) -> None:
        """
        Send welcome notifications to user and admin.

        Args:
            user: Newly registered user
        """
        if NotificationService:
            try:
                # Send welcome email to user
                NotificationService.send_welcome_email(user)

                # Notify admin about new registration
                NotificationService.notify_admin_new_user(user)
            except Exception as e:
                # Don't let notification failures break registration
                logger.error(f"Failed to send welcome notifications: {e}", exc_info=True)

    @staticmethod
    def get_user_info(user: User) -> Dict[str, Any]:
        """
        Get comprehensive user information for authentication response.

        Args:
            user: User whose info to retrieve

        Returns:
            Dictionary with user information
        """
        return {
            'id': str(user.id),
            'phone': user.phone,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'is_phone_verified': user.is_phone_verified,
            'is_approved': user.is_approved,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_blocked': user.is_blocked,
            'current_plan': {
                'code': user.current_plan.code,
                'name': user.current_plan.name,
                'price_inr': float(user.current_plan.price_inr)
            } if user.current_plan else None,
            'created_at': user.created_at.isoformat(),
            'phone_verified_at': user.phone_verified_at.isoformat() if user.phone_verified_at else None,
            'approved_at': user.approved_at.isoformat() if user.approved_at else None
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (success, access_token, error_message)
        """
        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)

            return True, access_token, None

        except Exception as e:
            logger.error(f"Error refreshing token: {e}", exc_info=True)
            return False, None, "Invalid or expired refresh token"
