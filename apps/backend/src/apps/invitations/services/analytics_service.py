"""
Analytics and reporting service.

This service provides statistics, analytics, and reporting for invitations.
"""
import logging
from typing import Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import Invitation, Guest, Order, InvitationViewLog
from .guest_service import GuestService

logger = logging.getLogger(__name__)
User = get_user_model()


class AnalyticsService:
    """Service for analytics and reporting."""

    @staticmethod
    def get_invitation_stats(invitation: Invitation) -> Dict[str, Any]:
        """
        Get comprehensive invitation statistics.

        Args:
            invitation: Invitation to get stats for

        Returns:
            Dictionary with statistics
        """
        # Calculate expires_in_days
        expires_in_days = 0
        if invitation.link_expires_at:
            delta = invitation.link_expires_at - timezone.now()
            expires_in_days = max(0, delta.days)

        # Get guest analytics
        guest_analytics = GuestService.get_guest_analytics(invitation)

        return {
            'views': {
                'total': invitation.total_views,
                'unique_guests': invitation.unique_guests
            },
            'links': {
                'regular': {
                    'granted': invitation.order.granted_regular_links,
                    'used': invitation.regular_links_used,
                    'remaining': invitation.remaining_regular_links
                },
                'test': {
                    'granted': invitation.order.granted_test_links,
                    'used': invitation.test_links_used,
                    'remaining': invitation.remaining_test_links
                }
            },
            'validity': {
                'is_active': invitation.is_active,
                'is_expired': invitation.is_expired,
                'is_valid': invitation.is_link_valid,
                'expires_at': invitation.link_expires_at.isoformat() if invitation.link_expires_at else None,
                'expires_in_days': expires_in_days
            },
            'guests': guest_analytics
        }

    @staticmethod
    def get_order_stats(order: Order) -> Dict[str, Any]:
        """
        Get order statistics.

        Args:
            order: Order to get stats for

        Returns:
            Dictionary with order statistics
        """
        has_invitation = hasattr(order, 'invitation') and order.invitation

        stats = {
            'order': {
                'number': order.order_number,
                'status': order.status,
                'created_at': order.created_at.isoformat()
            },
            'payment': {
                'amount': float(order.payment_amount),
                'method': order.payment_method,
                'status': order.payment_status,
                'received_at': order.payment_received_at.isoformat() if order.payment_received_at else None
            },
            'links': {
                'regular_granted': order.granted_regular_links,
                'test_granted': order.granted_test_links,
                'used': order.used_links_count,
                'remaining': order.remaining_links
            },
            'approval': {
                'is_approved': order.status == 'APPROVED',
                'approved_at': order.approved_at.isoformat() if order.approved_at else None,
                'approved_by': order.approved_by.username if order.approved_by else None
            },
            'has_invitation': has_invitation
        }

        # Add invitation stats if exists
        if has_invitation:
            stats['invitation'] = AnalyticsService.get_invitation_stats(order.invitation)

        return stats

    @staticmethod
    def get_user_dashboard_stats(user: User) -> Dict[str, Any]:
        """
        Get overall statistics for a user's dashboard.

        Args:
            user: User to get stats for

        Returns:
            Dictionary with dashboard statistics
        """
        # Order statistics
        orders = Order.objects.filter(user=user)
        total_orders = orders.count()
        pending_orders = orders.filter(status='PENDING_APPROVAL').count()
        approved_orders = orders.filter(status='APPROVED').count()
        rejected_orders = orders.filter(status='REJECTED').count()

        # Invitation statistics
        invitations = Invitation.objects.filter(user=user)
        total_invitations = invitations.count()
        active_invitations = invitations.filter(is_active=True, is_expired=False).count()
        expired_invitations = invitations.filter(is_expired=True).count()

        # Guest statistics (across all invitations)
        total_guests = Guest.objects.filter(invitation__user=user).count()
        total_views = invitations.aggregate(
            total=models.Sum('total_views')
        )['total'] or 0

        # Link usage
        total_links_granted = orders.aggregate(
            regular=models.Sum('granted_regular_links'),
            test=models.Sum('granted_test_links')
        )
        total_links_used = invitations.aggregate(
            regular=models.Sum('regular_links_used'),
            test=models.Sum('test_links_used')
        )

        return {
            'orders': {
                'total': total_orders,
                'pending': pending_orders,
                'approved': approved_orders,
                'rejected': rejected_orders
            },
            'invitations': {
                'total': total_invitations,
                'active': active_invitations,
                'expired': expired_invitations
            },
            'engagement': {
                'total_views': total_views,
                'total_guests': total_guests
            },
            'links': {
                'granted': {
                    'regular': total_links_granted['regular'] or 0,
                    'test': total_links_granted['test'] or 0
                },
                'used': {
                    'regular': total_links_used['regular'] or 0,
                    'test': total_links_used['test'] or 0
                }
            }
        }

    @staticmethod
    def get_view_timeline(invitation: Invitation, days: int = 7) -> Dict[str, Any]:
        """
        Get view timeline for an invitation.

        Args:
            invitation: Invitation to analyze
            days: Number of days to include (default 7)

        Returns:
            Dictionary with timeline data
        """
        from datetime import timedelta
        from collections import defaultdict

        cutoff_date = timezone.now() - timedelta(days=days)

        view_logs = InvitationViewLog.objects.filter(
            invitation=invitation,
            viewed_at__gte=cutoff_date
        ).order_by('viewed_at')

        # Group by date
        views_by_date = defaultdict(int)
        for log in view_logs:
            date_key = log.viewed_at.strftime('%Y-%m-%d')
            views_by_date[date_key] += 1

        # Convert to sorted list
        timeline = [
            {'date': date, 'views': count}
            for date, count in sorted(views_by_date.items())
        ]

        return {
            'days': days,
            'total_views': len(view_logs),
            'timeline': timeline
        }

    @staticmethod
    def get_device_breakdown(invitation: Invitation) -> Dict[str, Any]:
        """
        Get device type breakdown for guests.

        Args:
            invitation: Invitation to analyze

        Returns:
            Dictionary with device statistics
        """
        guests = Guest.objects.filter(invitation=invitation)

        device_counts = {}
        browser_counts = {}
        os_counts = {}

        for guest in guests:
            # Device type
            device_counts[guest.device_type] = device_counts.get(guest.device_type, 0) + 1

            # Browser (simplified)
            browser_family = guest.browser.split()[0] if guest.browser else 'Unknown'
            browser_counts[browser_family] = browser_counts.get(browser_family, 0) + 1

            # OS (simplified)
            os_family = guest.os.split()[0] if guest.os else 'Unknown'
            os_counts[os_family] = os_counts.get(os_family, 0) + 1

        return {
            'total_guests': guests.count(),
            'device_types': device_counts,
            'browsers': browser_counts,
            'operating_systems': os_counts
        }

    @staticmethod
    def get_rsvp_summary(invitation: Invitation) -> Dict[str, Any]:
        """
        Get RSVP summary for an invitation.

        Args:
            invitation: Invitation to analyze

        Returns:
            Dictionary with RSVP statistics
        """
        guests = Guest.objects.filter(invitation=invitation)

        rsvp_yes = guests.filter(attending=True).count()
        rsvp_no = guests.filter(attending=False).count()
        rsvp_pending = guests.filter(attending__isnull=True).count()

        return {
            'total_guests': guests.count(),
            'yes': rsvp_yes,
            'no': rsvp_no,
            'pending': rsvp_pending,
            'response_rate': round((rsvp_yes + rsvp_no) / guests.count() * 100, 1) if guests.count() > 0 else 0
        }


# Import at the end to avoid circular imports
from django.db import models
