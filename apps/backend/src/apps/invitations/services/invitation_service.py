"""
Invitation management service.

This service handles invitation lifecycle, activation, and tracking.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import timedelta
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.conf import settings

from ..models import Invitation, InvitationViewLog, Order
from .utils import generate_slug, get_client_ip, get_user_agent, get_referrer

logger = logging.getLogger(__name__)
User = get_user_model()


class InvitationService:
    """Service for invitation management."""

    @staticmethod
    def create_invitation(
        order: Order,
        template_id: str,
        event_data: Dict[str, Any],
        host_data: Dict[str, Any],
        media_data: Dict[str, Any],
        user: User
    ) -> Tuple[bool, Optional[Invitation], Optional[str]]:
        """
        Create a new invitation.

        Args:
            order: Order for this invitation
            template_id: Template UUID
            event_data: Event details (title, date, venue, etc.)
            host_data: Host information (name, phone, message)
            media_data: Media files (banner, gallery, music)
            user: User creating invitation

        Returns:
            Tuple of (success, invitation, error_message)
        """
        from apps.plans.models import Template

        try:
            # Validate order can have invitation
            from .order_service import OrderService
            can_create, reason = OrderService.can_create_invitation(order)
            if not can_create:
                return False, None, reason

            # Validate template
            try:
                template = Template.objects.get(id=template_id, is_active=True)
            except Template.DoesNotExist:
                return False, None, "Invalid template selected"

            # Create invitation
            with transaction.atomic():
                invitation = Invitation.objects.create(
                    order=order,
                    user=user,
                    template=template,
                    slug=generate_slug(),
                    # Event details
                    event_title=event_data.get('title'),
                    event_date=event_data.get('date'),
                    event_venue=event_data.get('venue'),
                    event_address=event_data.get('address', ''),
                    event_map_link=event_data.get('map_link', ''),
                    # Host information
                    host_name=host_data.get('name'),
                    host_phone=host_data.get('phone', ''),
                    custom_message=host_data.get('message', ''),
                    # Media
                    banner_image=media_data.get('banner'),
                    gallery_images=media_data.get('gallery', []),
                    background_music=media_data.get('music'),
                    # Initially inactive until approved
                    is_active=False
                )

                # If order is already approved, activate immediately
                if order.status == 'APPROVED':
                    InvitationService.activate_invitation(invitation)

            logger.info(f"Invitation {invitation.slug} created for order {order.order_number}")
            return True, invitation, None

        except Exception as e:
            logger.error(f"Error creating invitation: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def activate_invitation(invitation: Invitation) -> Tuple[bool, Optional[str]]:
        """
        Activate invitation after order approval.

        Sets:
        - is_active = True
        - link_expires_at = now + validity_days

        Args:
            invitation: Invitation to activate

        Returns:
            Tuple of (success, error_message)
        """
        try:
            validity_days = getattr(
                settings,
                'INVITATION_LINK_VALIDITY_DAYS',
                settings.INVITATION_SETTINGS.get('LINK_VALIDITY_DAYS', 15)
            )

            invitation.is_active = True
            invitation.link_expires_at = timezone.now() + timedelta(days=validity_days)
            invitation.save(update_fields=['is_active', 'link_expires_at'])

            logger.info(f"Invitation {invitation.slug} activated (expires: {invitation.link_expires_at})")
            return True, None

        except Exception as e:
            logger.error(f"Error activating invitation: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def expire_invitation(invitation: Invitation) -> Tuple[bool, Optional[str]]:
        """
        Mark invitation as expired.

        Args:
            invitation: Invitation to expire

        Returns:
            Tuple of (success, error_message)
        """
        try:
            invitation.is_expired = True
            invitation.expired_at = timezone.now()
            invitation.save(update_fields=['is_expired', 'expired_at'])

            logger.info(f"Invitation {invitation.slug} marked as expired")
            return True, None

        except Exception as e:
            logger.error(f"Error expiring invitation: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def check_and_expire_if_needed(invitation: Invitation) -> bool:
        """
        Check if invitation should be expired and expire it if needed.

        Args:
            invitation: Invitation to check

        Returns:
            True if invitation is valid, False if expired
        """
        if invitation.is_expired:
            return False

        if invitation.link_expires_at and timezone.now() > invitation.link_expires_at:
            InvitationService.expire_invitation(invitation)
            return False

        return True

    @staticmethod
    def get_public_invitation(slug: str) -> Tuple[bool, Optional[Invitation], Optional[str]]:
        """
        Get invitation for public viewing.

        Args:
            slug: Invitation slug

        Returns:
            Tuple of (success, invitation, error_message)
        """
        try:
            invitation = Invitation.objects.select_related('template').get(
                slug=slug,
                is_active=True
            )

            # Check expiry
            if not InvitationService.check_and_expire_if_needed(invitation):
                return False, None, "This invitation link has expired"

            return True, invitation, None

        except Invitation.DoesNotExist:
            return False, None, "Invitation not found or not active"
        except Exception as e:
            logger.error(f"Error getting public invitation: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_user_invitations(user: User):
        """
        Get all invitations for a user.

        Args:
            user: User whose invitations to retrieve

        Returns:
            QuerySet of invitations
        """
        return Invitation.objects.filter(
            user=user
        ).select_related('template', 'order').order_by('-created_at')

    @staticmethod
    def get_invitation_by_slug(slug: str, user: User) -> Tuple[bool, Optional[Invitation], Optional[str]]:
        """
        Get invitation by slug for authenticated user.

        Args:
            slug: Invitation slug
            user: User requesting invitation

        Returns:
            Tuple of (success, invitation, error_message)
        """
        try:
            invitation = Invitation.objects.select_related(
                'template', 'order', 'order__plan'
            ).get(slug=slug, user=user)

            return True, invitation, None

        except Invitation.DoesNotExist:
            return False, None, "Invitation not found"
        except Exception as e:
            logger.error(f"Error getting invitation: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def update_invitation(
        invitation: Invitation,
        event_data: Optional[Dict[str, Any]] = None,
        host_data: Optional[Dict[str, Any]] = None,
        media_data: Optional[Dict[str, Any]] = None,
        user: User = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update invitation details.

        Args:
            invitation: Invitation to update
            event_data: Event details to update
            host_data: Host information to update
            media_data: Media files to update
            user: User making the update

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check if can be edited
            if invitation.is_expired:
                return False, "Cannot edit expired invitation"

            with transaction.atomic():
                # Update event details
                if event_data:
                    for key, value in event_data.items():
                        if hasattr(invitation, f'event_{key}'):
                            setattr(invitation, f'event_{key}', value)

                # Update host information
                if host_data:
                    for key, value in host_data.items():
                        if key == 'message':
                            invitation.custom_message = value
                        elif hasattr(invitation, f'host_{key}'):
                            setattr(invitation, f'host_{key}', value)

                # Update media
                if media_data:
                    if 'banner' in media_data and media_data['banner']:
                        invitation.banner_image = media_data['banner']
                    if 'gallery' in media_data:
                        invitation.gallery_images = media_data['gallery']
                    if 'music' in media_data:
                        invitation.background_music = media_data['music']

                invitation.save()

            logger.info(f"Invitation {invitation.slug} updated")
            return True, None

        except Exception as e:
            logger.error(f"Error updating invitation: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def increment_view_count(invitation: Invitation) -> None:
        """
        Increment total view count.

        Args:
            invitation: Invitation to increment views for
        """
        invitation.total_views += 1
        invitation.save(update_fields=['total_views'])

    @staticmethod
    def log_invitation_view(invitation: Invitation, request) -> None:
        """
        Log an invitation view for analytics.

        Args:
            invitation: Invitation being viewed
            request: Django request object
        """
        try:
            InvitationViewLog.objects.create(
                invitation=invitation,
                ip_address=get_client_ip(request) or '0.0.0.0',
                user_agent=get_user_agent(request),
                referrer=get_referrer(request)
            )
        except Exception as e:
            # Don't let logging failures break the view
            logger.error(f"Failed to log invitation view: {e}")

    @staticmethod
    def get_share_url(invitation: Invitation) -> str:
        """
        Get the full shareable URL for an invitation.

        Args:
            invitation: Invitation to get URL for

        Returns:
            Full shareable URL
        """
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/invite/{invitation.slug}"

    @staticmethod
    def get_invitation_summary(invitation: Invitation) -> Dict[str, Any]:
        """
        Get comprehensive invitation summary.

        Args:
            invitation: Invitation to summarize

        Returns:
            Dictionary with invitation summary data
        """
        return {
            'id': str(invitation.id),
            'slug': invitation.slug,
            'share_url': InvitationService.get_share_url(invitation),
            'event': {
                'title': invitation.event_title,
                'date': invitation.event_date.isoformat(),
                'venue': invitation.event_venue,
                'address': invitation.event_address,
                'map_link': invitation.event_map_link
            },
            'host': {
                'name': invitation.host_name,
                'phone': invitation.host_phone,
                'message': invitation.custom_message
            },
            'template': {
                'id': str(invitation.template.id),
                'name': invitation.template.name
            },
            'status': {
                'is_active': invitation.is_active,
                'is_expired': invitation.is_expired,
                'is_valid': invitation.is_link_valid,
                'expires_at': invitation.link_expires_at.isoformat() if invitation.link_expires_at else None
            },
            'stats': {
                'total_views': invitation.total_views,
                'unique_guests': invitation.unique_guests,
                'regular_links_used': invitation.regular_links_used,
                'test_links_used': invitation.test_links_used,
                'remaining_regular': invitation.remaining_regular_links,
                'remaining_test': invitation.remaining_test_links
            },
            'created_at': invitation.created_at.isoformat(),
            'updated_at': invitation.updated_at.isoformat()
        }
