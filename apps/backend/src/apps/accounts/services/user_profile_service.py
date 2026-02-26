"""
User profile management service.

This service handles user profile operations including updates and password changes.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from .activity_service import ActivityService

logger = logging.getLogger(__name__)
User = get_user_model()


class UserProfileService:
    """Service for user profile management."""

    @staticmethod
    def get_profile(user: User) -> Dict[str, Any]:
        """
        Get user profile data.

        Args:
            user: User whose profile to retrieve

        Returns:
            Dictionary with profile data
        """
        return {
            'id': str(user.id),
            'phone': user.phone,
            'username': user.username,
            'email': user.email,
            'full_name': user.full_name,
            'is_phone_verified': user.is_phone_verified,
            'is_approved': user.is_approved,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat(),
            'active_orders_count': user.active_orders_count,
            'total_invitations': user.total_invitations,
            'current_plan': {
                'code': user.current_plan.code,
                'name': user.current_plan.name,
                'price_inr': float(user.current_plan.price_inr)
            } if user.current_plan else None
        }

    @staticmethod
    def update_profile(
        user: User,
        data: Dict[str, Any],
        request = None
    ) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Update user profile.

        Only allows updating: username, email, full_name

        Args:
            user: User to update
            data: Dictionary with fields to update
            request: Django request object (for activity logging)

        Returns:
            Tuple of (success, user, error_message)
        """
        try:
            # Fields that can be updated
            updatable_fields = ['username', 'email', 'full_name']
            updated_fields = []

            with transaction.atomic():
                for field in updatable_fields:
                    if field in data:
                        setattr(user, field, data[field])
                        updated_fields.append(field)

                # Validate before saving
                try:
                    user.full_clean()
                except ValidationError as e:
                    return False, None, str(e)

                if updated_fields:
                    user.save(update_fields=updated_fields + ['updated_at'])

                    # Log activity
                    ActivityService.log_profile_update(user, request, updated_fields)

            return True, user, None

        except Exception as e:
            logger.error(f"Error updating profile: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def change_password(
        user: User,
        old_password: str,
        new_password: str,
        request = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password.

        Args:
            user: User whose password to change
            old_password: Current password
            new_password: New password
            request: Django request object (for activity logging)

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Verify old password
            if not user.check_password(old_password):
                return False, "Current password is incorrect"

            # Validate new password
            try:
                validate_password(new_password, user=user)
            except ValidationError as e:
                return False, ', '.join(e.messages)

            # Set new password
            with transaction.atomic():
                user.set_password(new_password)
                user.save(update_fields=['password'])

                # Log activity
                ActivityService.log_password_change(user, request)

            return True, None

        except Exception as e:
            logger.error(f"Error changing password: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_profile_stats(user: User) -> Dict[str, Any]:
        """
        Get user profile statistics.

        Args:
            user: User whose stats to retrieve

        Returns:
            Dictionary with user statistics
        """
        # Import here to avoid circular imports
        from apps.invitations.models import Order

        # Get order statistics
        orders = user.orders.all()
        total_orders = orders.count()
        pending_orders = orders.filter(status='PENDING_APPROVAL').count()
        approved_orders = orders.filter(status='APPROVED').count()
        rejected_orders = orders.filter(status='REJECTED').count()

        # Get invitation statistics
        total_invitations = user.total_invitations
        active_invitations = user.invitations.filter(is_active=True).count() if hasattr(user, 'invitations') else 0

        return {
            'orders': {
                'total': total_orders,
                'pending': pending_orders,
                'approved': approved_orders,
                'rejected': rejected_orders
            },
            'invitations': {
                'total': total_invitations,
                'active': active_invitations
            },
            'account': {
                'is_approved': user.is_approved,
                'is_phone_verified': user.is_phone_verified,
                'member_since': user.created_at.isoformat(),
                'last_updated': user.updated_at.isoformat()
            }
        }

    @staticmethod
    def can_user_login(user: User) -> Tuple[bool, Optional[str]]:
        """
        Check if user can log in.

        Args:
            user: User to check

        Returns:
            Tuple of (can_login, reason_if_not)
        """
        # Check if user is blocked
        if user.is_blocked:
            return False, "Your account has been blocked. Please contact support."

        # Check if user is approved (skip for superusers and staff)
        if not user.is_approved and not user.is_superuser and not user.is_staff:
            return False, "Your account is pending admin approval. Please wait for verification or contact support."

        return True, None

    @staticmethod
    def update_last_login_ip(user: User, request) -> None:
        """
        Update user's last login IP address.

        Args:
            user: User who logged in
            request: Django request object
        """
        from .utils import get_client_ip

        ip = get_client_ip(request)
        if ip:
            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip'])

    @staticmethod
    def set_signup_ip(user: User, request) -> None:
        """
        Set user's signup IP address.

        Args:
            user: Newly registered user
            request: Django request object
        """
        from .utils import get_client_ip

        ip = get_client_ip(request)
        if ip:
            user.signup_ip = ip
            user.save(update_fields=['signup_ip'])
