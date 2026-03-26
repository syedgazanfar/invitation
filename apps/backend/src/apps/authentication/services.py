"""
Authentication services.

Handles user login, admin login, logout, and token refresh.
Each method returns a consistent (success, data, error_code, error_message) tuple
so views stay thin and all logic is testable in isolation.
"""
import logging
from typing import Any, Dict, Optional, Tuple

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserActivityLog

logger = logging.getLogger(__name__)
User = get_user_model()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_client_ip(request) -> Optional[str]:
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _normalize_phone(phone: str) -> str:
    """
    Normalize an Indian phone number to E.164 format (+91XXXXXXXXXX).

    Handles inputs like:
        9876543210, 09876543210, 919876543210, +919876543210
    """
    only_digits = ''.join(ch for ch in phone if ch.isdigit())

    if len(only_digits) == 10:
        return '+91' + only_digits

    if len(only_digits) == 11 and only_digits.startswith('0'):
        return '+91' + only_digits[1:]

    if len(only_digits) == 12 and only_digits.startswith('91'):
        return '+' + only_digits

    if len(only_digits) == 13 and only_digits.startswith('091'):
        return '+' + only_digits[1:]

    # Already in E.164 form or unrecognised — return as-is and let the
    # DB lookup fail cleanly rather than silently mangling the value.
    return phone.strip()


def _find_user(identifier: str) -> Optional[User]:
    """
    Locate a user by username or phone number.

    Always does a select_related('current_plan') to avoid N+1 queries
    in the token-payload builder.
    """
    identifier = identifier.strip()
    if not identifier:
        return None

    qs = User.objects.select_related('current_plan')

    # Try username
    try:
        return qs.get(username=identifier)
    except User.DoesNotExist:
        pass

    # Try email
    try:
        return qs.get(email=identifier)
    except User.DoesNotExist:
        pass

    # Try as phone (normalised)
    try:
        return qs.get(phone=_normalize_phone(identifier))
    except User.DoesNotExist:
        pass

    return None


def _generate_tokens(user: User) -> Dict[str, str]:
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _build_user_payload(user: User) -> Dict[str, Any]:
    return {
        'id': str(user.id),
        'username': user.username,
        'phone': user.phone,
        'email': user.email,
        'full_name': user.full_name,
        'is_approved': user.is_approved,
        'is_phone_verified': user.is_phone_verified,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'current_plan': {
            'code': user.current_plan.code,
            'name': user.current_plan.name,
            'price_inr': float(user.current_plan.price_inr),
        } if user.current_plan else None,
    }


def _build_admin_payload(user: User) -> Dict[str, Any]:
    payload = _build_user_payload(user)
    payload['permissions'] = {
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
    }
    return payload


def _log_activity(
    user: User,
    activity_type: str,
    description: str,
    request=None,
) -> None:
    try:
        UserActivityLog.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=_get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            metadata={},
        )
    except Exception as exc:
        logger.warning(
            "Failed to log activity '%s' for user %s: %s",
            activity_type, user.id, exc,
        )


def _update_last_login_ip(user: User, request) -> None:
    ip = _get_client_ip(request)
    if not ip:
        return
    try:
        User.objects.filter(pk=user.pk).update(last_login_ip=ip)
    except Exception as exc:
        logger.warning("Failed to update last_login_ip for user %s: %s", user.id, exc)


# ---------------------------------------------------------------------------
# Public service
# ---------------------------------------------------------------------------

class LoginService:
    """
    Central authentication service.

    All public methods return a 4-tuple:
        (success: bool, data: dict | None, error_code: str, error_message: str | None)

    Error codes are stable string constants so frontend and tests can rely on them
    without parsing human-readable messages:

        LOGIN_SUCCESS       - authentication succeeded
        LOGOUT_SUCCESS      - token blacklisted
        TOKEN_REFRESHED     - new access token issued
        INVALID_CREDENTIALS - wrong username/password or user not found
        ACCOUNT_BLOCKED     - user.is_blocked is True
        PENDING_APPROVAL    - user.is_approved is False (regular users only)
        NOT_ADMIN           - admin endpoint called by a non-staff user
        TOKEN_INVALID       - refresh token is malformed, expired, or blacklisted
        VALIDATION_ERROR    - missing or blank required field
        SERVER_ERROR        - unexpected exception (logged server-side)
    """

    @staticmethod
    def user_login(
        identifier: str,
        password: str,
        request=None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str, Optional[str]]:
        """
        Authenticate a regular user by username or phone.

        Approval is required for standard users.
        Staff and superusers bypass the approval gate so that accounts created
        via the Django admin (createsuperuser / is_staff flag) can always log in.
        """
        try:
            user = _find_user(identifier)
            if user is None:
                return False, None, 'INVALID_CREDENTIALS', 'Invalid credentials'

            if not user.check_password(password):
                return False, None, 'INVALID_CREDENTIALS', 'Invalid credentials'

            if user.is_blocked:
                return False, None, 'ACCOUNT_BLOCKED', (
                    'Your account has been blocked. Please contact support.'
                )

            if not user.is_approved and not user.is_staff and not user.is_superuser:
                return False, None, 'PENDING_APPROVAL', (
                    'Your account is pending admin approval. '
                    'Please wait for verification or contact support.'
                )

            tokens = _generate_tokens(user)
            _update_last_login_ip(user, request)
            _log_activity(user, 'LOGIN', 'User logged in', request)

            return True, {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': _build_user_payload(user),
            }, 'LOGIN_SUCCESS', None

        except Exception as exc:
            logger.error("Unexpected error in user_login: %s", exc, exc_info=True)
            return False, None, 'SERVER_ERROR', 'An unexpected error occurred'

    @staticmethod
    def admin_login(
        identifier: str,
        password: str,
        request=None,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str, Optional[str]]:
        """
        Authenticate an admin (staff) user.

        Differences from user_login:
        - Requires is_staff=True; returns NOT_ADMIN otherwise.
        - Approval check is skipped — admins manage approvals, they are never
          gated behind one themselves.
        - Returns an extended payload that includes explicit permission flags.
        """
        try:
            user = _find_user(identifier)
            if user is None:
                return False, None, 'INVALID_CREDENTIALS', 'Invalid credentials'

            if not user.check_password(password):
                return False, None, 'INVALID_CREDENTIALS', 'Invalid credentials'

            if not user.is_staff:
                return False, None, 'NOT_ADMIN', (
                    'Access denied. Admin credentials required.'
                )

            if user.is_blocked:
                return False, None, 'ACCOUNT_BLOCKED', (
                    'This admin account has been blocked. '
                    'Please contact a superuser.'
                )

            tokens = _generate_tokens(user)
            _update_last_login_ip(user, request)
            _log_activity(user, 'LOGIN', 'Admin logged in via admin endpoint', request)

            return True, {
                'access': tokens['access'],
                'refresh': tokens['refresh'],
                'user': _build_admin_payload(user),
            }, 'LOGIN_SUCCESS', None

        except Exception as exc:
            logger.error("Unexpected error in admin_login: %s", exc, exc_info=True)
            return False, None, 'SERVER_ERROR', 'An unexpected error occurred'

    @staticmethod
    def logout(
        refresh_token: str,
        user: User,
        request=None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Logout by blacklisting the refresh token.

        Returns a 3-tuple: (success, error_code, error_message).
        """
        if not refresh_token or not refresh_token.strip():
            return False, 'VALIDATION_ERROR', 'refresh token is required'

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            _log_activity(user, 'LOGOUT', 'User logged out', request)
            return True, 'LOGOUT_SUCCESS', None

        except TokenError:
            return False, 'TOKEN_INVALID', 'Token is invalid or already blacklisted'

        except Exception as exc:
            logger.error("Unexpected error in logout: %s", exc, exc_info=True)
            return False, 'SERVER_ERROR', 'An unexpected error occurred'

    @staticmethod
    def refresh_access_token(
        refresh_token: str,
    ) -> Tuple[bool, Optional[str], str, Optional[str]]:
        """
        Issue a new access token from a valid, non-blacklisted refresh token.

        Returns a 4-tuple: (success, access_token, error_code, error_message).
        """
        if not refresh_token or not refresh_token.strip():
            return False, None, 'VALIDATION_ERROR', 'refresh token is required'

        try:
            token = RefreshToken(refresh_token)
            return True, str(token.access_token), 'TOKEN_REFRESHED', None

        except TokenError:
            return False, None, 'TOKEN_INVALID', 'Token is invalid or expired'

        except Exception as exc:
            logger.error("Unexpected error in refresh_access_token: %s", exc, exc_info=True)
            return False, None, 'SERVER_ERROR', 'An unexpected error occurred'
