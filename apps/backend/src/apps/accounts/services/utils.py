"""
Common utility functions for accounts services.

This module provides shared utilities used across the accounts service layer.
"""
from typing import Optional
from django.contrib.auth import get_user_model

User = get_user_model()


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


def normalize_phone(phone: str) -> str:
    """
    Normalize phone number to +91 format.

    Args:
        phone: Phone number string (with or without +91 prefix)

    Returns:
        Normalized phone number with +91 prefix

    Examples:
        >>> normalize_phone("9876543210")
        "+919876543210"
        >>> normalize_phone("+91 9876543210")
        "+919876543210"
        >>> normalize_phone("91-9876543210")
        "+919876543210"
    """
    # Remove spaces and hyphens
    phone = phone.replace(' ', '').replace('-', '')

    # Add +91 prefix if not present
    if not phone.startswith('+91'):
        # Take last 10 digits and add +91
        phone = '+91' + phone[-10:]

    return phone


def get_user_by_identifier(identifier: str) -> Optional[User]:
    """
    Get user by username or phone number.

    Tries to find user by username first, then by normalized phone number.

    Args:
        identifier: Username or phone number

    Returns:
        User object if found, None otherwise
    """
    # Try username first
    try:
        return User.objects.get(username=identifier)
    except User.DoesNotExist:
        pass

    # Try phone number
    try:
        phone = normalize_phone(identifier)
        return User.objects.get(phone=phone)
    except (User.DoesNotExist, IndexError, ValueError):
        pass

    return None


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
