"""
Invitations app services package.

This package provides business logic services for the invitations app:
- OrderService: Order management and approval workflow
- InvitationService: Invitation lifecycle management
- GuestService: Guest registration with device fingerprinting
- PaymentService: Razorpay payment integration
- AnalyticsService: Statistics and reporting
- Utils: Common utility functions

All services are stateless and can be imported and used throughout the application.
"""

from .order_service import OrderService
from .invitation_service import InvitationService
from .guest_service import GuestService
from .payment_service import PaymentService
from .analytics_service import AnalyticsService
from .utils import (
    get_client_ip,
    get_user_agent,
    get_referrer,
    generate_order_number,
    generate_slug
)

__all__ = [
    # Services
    'OrderService',
    'InvitationService',
    'GuestService',
    'PaymentService',
    'AnalyticsService',
    # Utils
    'get_client_ip',
    'get_user_agent',
    'get_referrer',
    'generate_order_number',
    'generate_slug',
]
