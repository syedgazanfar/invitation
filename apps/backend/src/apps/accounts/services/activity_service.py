"""
Activity logging service for user actions.

This service provides centralized activity logging for audit trail and analytics.
"""
import logging
from typing import Optional, Dict, Any
from django.contrib.auth import get_user_model

from ..models import UserActivityLog
from .utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)
User = get_user_model()


class ActivityService:
    """Service for logging user activities."""

    @staticmethod
    def log_activity(
        user: User,
        activity_type: str,
        description: str = '',
        request = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UserActivityLog]:
        """
        Log a user activity.

        Args:
            user: User performing the activity
            activity_type: Type of activity (from UserActivityLog.ActivityType)
            description: Optional description of the activity
            request: Django request object (for IP and user agent)
            metadata: Optional additional metadata

        Returns:
            UserActivityLog object if successful, None otherwise
        """
        try:
            activity_log = UserActivityLog.objects.create(
                user=user,
                activity_type=activity_type,
                description=description,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata=metadata or {}
            )
            return activity_log
        except Exception as e:
            # Don't let logging failures break the app
            logger.error(f"Failed to log activity: {e}", exc_info=True)
            return None

    @staticmethod
    def log_login(user: User, request) -> None:
        """
        Log user login activity.

        Args:
            user: User who logged in
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.LOGIN,
            description='User logged in',
            request=request
        )

    @staticmethod
    def log_logout(user: User, request) -> None:
        """
        Log user logout activity.

        Args:
            user: User who logged out
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.LOGOUT,
            description='User logged out',
            request=request
        )

    @staticmethod
    def log_registration(user: User, request) -> None:
        """
        Log user registration activity.

        Args:
            user: Newly registered user
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.LOGIN,
            description='User registered and logged in',
            request=request
        )

    @staticmethod
    def log_profile_update(user: User, request, updated_fields: Optional[list] = None) -> None:
        """
        Log profile update activity.

        Args:
            user: User whose profile was updated
            request: Django request object
            updated_fields: List of field names that were updated
        """
        description = 'Profile updated'
        metadata = {}
        if updated_fields:
            metadata['updated_fields'] = updated_fields
            description += f": {', '.join(updated_fields)}"

        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.PROFILE_UPDATE,
            description=description,
            request=request,
            metadata=metadata
        )

    @staticmethod
    def log_password_change(user: User, request) -> None:
        """
        Log password change activity.

        Args:
            user: User who changed password
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.PASSWORD_CHANGE,
            description='Password changed',
            request=request
        )

    @staticmethod
    def log_plan_change_request(
        user: User,
        new_plan_code: str,
        current_plan_code: Optional[str],
        request
    ) -> None:
        """
        Log plan change request activity.

        Args:
            user: User requesting plan change
            new_plan_code: Code of requested plan
            current_plan_code: Code of current plan (if any)
            request: Django request object
        """
        description = f'Requested plan change to {new_plan_code}'
        if current_plan_code:
            description += f' from {current_plan_code}'

        ActivityService.log_activity(
            user=user,
            activity_type='PLAN_CHANGE_REQUEST',
            description=description,
            request=request,
            metadata={
                'requested_plan': new_plan_code,
                'current_plan': current_plan_code
            }
        )

    @staticmethod
    def log_order_created(user: User, order_id: str, plan_code: str, request) -> None:
        """
        Log order creation activity.

        Args:
            user: User who created the order
            order_id: ID of the created order
            plan_code: Code of the plan ordered
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.ORDER_CREATED,
            description=f'Created order for {plan_code} plan',
            request=request,
            metadata={
                'order_id': str(order_id),
                'plan_code': plan_code
            }
        )

    @staticmethod
    def log_invitation_created(user: User, invitation_id: str, request) -> None:
        """
        Log invitation creation activity.

        Args:
            user: User who created the invitation
            invitation_id: ID of the created invitation
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.INVITATION_CREATED,
            description='Created invitation',
            request=request,
            metadata={'invitation_id': str(invitation_id)}
        )

    @staticmethod
    def log_invitation_shared(user: User, invitation_id: str, share_method: str, request) -> None:
        """
        Log invitation sharing activity.

        Args:
            user: User who shared the invitation
            invitation_id: ID of the shared invitation
            share_method: Method used to share (e.g., 'whatsapp', 'email')
            request: Django request object
        """
        ActivityService.log_activity(
            user=user,
            activity_type=UserActivityLog.ActivityType.INVITATION_SHARED,
            description=f'Shared invitation via {share_method}',
            request=request,
            metadata={
                'invitation_id': str(invitation_id),
                'share_method': share_method
            }
        )
