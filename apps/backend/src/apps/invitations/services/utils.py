"""
Common utility functions for invitations services.

This module provides shared utilities used across the invitations service layer.
"""
import uuid
from typing import Optional
from django.utils import timezone


def get_client_ip(request) -> Optional[str]:
    """
    Extract client IP address from request.

    Args:
        request: Django request object

    Returns:
        IP address as string, or None if not available
    """
    if not request:
        return None

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')

    return ip


def get_user_agent(request) -> str:
    """
    Extract user agent string from request.

    Args:
        request: Django request object

    Returns:
        User agent string, or empty string if not available
    """
    if not request:
        return ''

    return request.META.get('HTTP_USER_AGENT', '')


def get_referrer(request) -> str:
    """
    Extract referrer URL from request.

    Args:
        request: Django request object

    Returns:
        Referrer URL, or empty string if not available
    """
    if not request:
        return ''

    return request.META.get('HTTP_REFERER', '')


def generate_order_number() -> str:
    """
    Generate a unique order number.

    Format: ORD-YYYYMMDD-RANDOM (e.g., ORD-20260225-A1B2C3)

    Returns:
        Unique order number string
    """
    prefix = 'ORD'
    timestamp = timezone.now().strftime('%Y%m%d')
    random_str = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{timestamp}-{random_str}"


def generate_slug() -> str:
    """
    Generate a unique 10-character slug for invitation.

    Uses nanoid for URL-safe random strings.

    Returns:
        10-character slug string
    """
    try:
        import nanoid
        return nanoid.generate(size=10)
    except ImportError:
        # Fallback to UUID if nanoid not available
        return uuid.uuid4().hex[:10]
