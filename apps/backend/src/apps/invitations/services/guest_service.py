"""
Guest management service with device fingerprinting.

This service handles guest registration, tracking, and anti-fraud measures.
"""
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import timedelta
from django.utils import timezone

from ..models import Guest, Invitation
from .utils import get_client_ip, get_user_agent

logger = logging.getLogger(__name__)


class GuestService:
    """Service for guest management with anti-fraud measures."""

    @staticmethod
    def generate_device_fingerprint(
        user_agent: str,
        screen_resolution: str = '',
        timezone_offset: str = '',
        languages: str = '',
        canvas_hash: str = ''
    ) -> str:
        """
        Generate unique device fingerprint from browser data.

        Combines multiple browser characteristics to create a unique fingerprint.

        Args:
            user_agent: Browser user agent string
            screen_resolution: Screen resolution (e.g., "1920x1080")
            timezone_offset: Timezone offset in minutes (e.g., "-420")
            languages: Browser languages (e.g., "en-US,en;q=0.9")
            canvas_hash: Canvas fingerprint hash

        Returns:
            SHA-256 hash of combined data
        """
        fingerprint_data = f"{user_agent}|{screen_resolution}|{timezone_offset}|{languages}|{canvas_hash}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    @staticmethod
    def parse_user_agent(user_agent: str) -> Dict[str, str]:
        """
        Parse user agent string to extract device info.

        Args:
            user_agent: User agent string

        Returns:
            Dictionary with device_type, browser, os
        """
        try:
            from user_agents import parse
            ua = parse(user_agent)

            device_type = 'mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop'
            browser = f"{ua.browser.family} {ua.browser.version_string}"
            os_name = f"{ua.os.family} {ua.os.version_string}"

            return {
                'device_type': device_type,
                'browser': browser,
                'os': os_name
            }
        except Exception as e:
            logger.error(f"Error parsing user agent: {e}")
            return {
                'device_type': 'unknown',
                'browser': 'unknown',
                'os': 'unknown'
            }

    @staticmethod
    def check_existing_guest(
        invitation_id: str,
        fingerprint: str,
        ip_address: str
    ) -> Optional[Guest]:
        """
        Check if a guest with same fingerprint or IP already exists.

        Checks in order:
        1. By fingerprint (most reliable)
        2. By IP address (within last 30 days)

        Args:
            invitation_id: Invitation UUID
            fingerprint: Device fingerprint
            ip_address: IP address

        Returns:
            Existing Guest object if found, None otherwise
        """
        # First check by fingerprint (most reliable)
        try:
            return Guest.objects.get(
                invitation_id=invitation_id,
                device_fingerprint=fingerprint
            )
        except Guest.DoesNotExist:
            pass

        # Then check by IP (backup method, recent only)
        cutoff_date = timezone.now() - timedelta(days=30)
        existing = Guest.objects.filter(
            invitation_id=invitation_id,
            ip_address=ip_address,
            viewed_at__gte=cutoff_date
        ).first()

        return existing

    @staticmethod
    def register_guest(
        invitation: Invitation,
        name: str,
        phone: str = '',
        message: str = '',
        fingerprint: str = '',
        ip_address: str = '',
        user_agent: str = '',
        session_id: str = '',
        is_test: bool = False,
        request = None
    ) -> Tuple[Optional[Guest], bool, str]:
        """
        Register a new guest with anti-fraud checks.

        Args:
            invitation: Invitation being accessed
            name: Guest name
            phone: Guest phone (optional)
            message: Guest message (optional)
            fingerprint: Device fingerprint
            ip_address: IP address
            user_agent: User agent string
            session_id: Session ID
            is_test: Is this a test link
            request: Django request object

        Returns:
            Tuple of (guest, created, message)
            - guest: Guest object
            - created: True if new guest, False if existing
            - message: Status message
        """
        try:
            # Check if invitation can accept guests
            if not invitation.can_accept_guest(is_test):
                return None, False, "Link limit reached or invitation expired"

            # Get IP and user agent from request if not provided
            if not ip_address and request:
                ip_address = get_client_ip(request) or '0.0.0.0'
            if not user_agent and request:
                user_agent = get_user_agent(request)

            # Check for existing guest
            existing = GuestService.check_existing_guest(
                invitation_id=invitation.id,
                fingerprint=fingerprint,
                ip_address=ip_address
            )

            if existing:
                # Update name if provided and different
                if name and name != existing.name:
                    existing.name = name
                    existing.save(update_fields=['name'])
                return existing, False, "Welcome back"

            # Parse user agent
            device_info = GuestService.parse_user_agent(user_agent)

            # Create user agent hash
            ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()

            # Create new guest
            guest = Guest.objects.create(
                invitation=invitation,
                name=name,
                phone=phone,
                message=message,
                device_fingerprint=fingerprint,
                ip_address=ip_address or '0.0.0.0',
                user_agent=user_agent,
                user_agent_hash=ua_hash,
                session_id=session_id,
                device_type=device_info['device_type'],
                browser=device_info['browser'],
                os=device_info['os'],
                is_test_link=is_test
            )

            # Update invitation counters
            invitation.record_guest(is_test)

            logger.info(f"Guest registered for invitation {invitation.slug}: {name}")
            return guest, True, "Successfully registered"

        except Exception as e:
            logger.error(f"Error registering guest: {e}", exc_info=True)
            return None, False, str(e)

    @staticmethod
    def update_rsvp(
        invitation: Invitation,
        fingerprint: str,
        attending: bool
    ) -> Tuple[bool, Optional[str]]:
        """
        Update RSVP status for a guest.

        Args:
            invitation: Invitation
            fingerprint: Device fingerprint
            attending: Attending status

        Returns:
            Tuple of (success, error_message)
        """
        try:
            guest = Guest.objects.get(
                invitation=invitation,
                device_fingerprint=fingerprint
            )

            guest.attending = attending
            guest.save(update_fields=['attending'])

            logger.info(f"RSVP updated for guest {guest.name}: {attending}")
            return True, None

        except Guest.DoesNotExist:
            return False, "Guest not found"
        except Exception as e:
            logger.error(f"Error updating RSVP: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_invitation_guests(invitation: Invitation):
        """
        Get all guests for an invitation.

        Args:
            invitation: Invitation to get guests for

        Returns:
            QuerySet of guests
        """
        return Guest.objects.filter(
            invitation=invitation
        ).order_by('-viewed_at')

    @staticmethod
    def get_guest_summary(guest: Guest) -> Dict[str, Any]:
        """
        Get guest summary data.

        Args:
            guest: Guest to summarize

        Returns:
            Dictionary with guest data
        """
        return {
            'id': str(guest.id),
            'name': guest.name,
            'phone': guest.phone,
            'message': guest.message,
            'attending': guest.attending,
            'device': {
                'type': guest.device_type,
                'browser': guest.browser,
                'os': guest.os
            },
            'is_test_link': guest.is_test_link,
            'viewed_at': guest.viewed_at.isoformat()
        }

    @staticmethod
    def export_guests_csv(invitation: Invitation) -> str:
        """
        Generate CSV data for guests.

        Args:
            invitation: Invitation to export guests for

        Returns:
            CSV string
        """
        import csv
        from io import StringIO

        guests = GuestService.get_invitation_guests(invitation)

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Name', 'Phone', 'Message', 'Attending',
            'Device Type', 'Browser', 'OS', 'Viewed At', 'Is Test Link'
        ])

        # Data
        for guest in guests:
            writer.writerow([
                guest.name,
                guest.phone or 'N/A',
                guest.message or 'N/A',
                'Yes' if guest.attending else 'No' if guest.attending is False else 'N/A',
                guest.device_type,
                guest.browser,
                guest.os,
                guest.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if guest.is_test_link else 'No'
            ])

        return output.getvalue()

    @staticmethod
    def get_guest_analytics(invitation: Invitation) -> Dict[str, Any]:
        """
        Get detailed guest analytics for an invitation.

        Args:
            invitation: Invitation to analyze

        Returns:
            Dictionary with analytics data
        """
        guests = Guest.objects.filter(invitation=invitation)

        # Device breakdown
        device_counts = {}
        for guest in guests:
            device_counts[guest.device_type] = device_counts.get(guest.device_type, 0) + 1

        # RSVP breakdown
        rsvp_yes = guests.filter(attending=True).count()
        rsvp_no = guests.filter(attending=False).count()
        rsvp_pending = guests.filter(attending__isnull=True).count()

        # Test vs regular
        test_guests = guests.filter(is_test_link=True).count()
        regular_guests = guests.filter(is_test_link=False).count()

        return {
            'total_guests': guests.count(),
            'device_breakdown': device_counts,
            'rsvp': {
                'yes': rsvp_yes,
                'no': rsvp_no,
                'pending': rsvp_pending
            },
            'link_type': {
                'test': test_guests,
                'regular': regular_guests
            }
        }
