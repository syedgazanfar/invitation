"""
Device Fingerprinting Utilities

This module provides utilities for generating and validating device fingerprints
for the anti-fraud guest tracking system.
"""
import hashlib
import json
from typing import Dict, Optional


def generate_device_fingerprint(
    user_agent: str,
    screen_resolution: str = '',
    timezone_offset: str = '',
    languages: str = '',
    canvas_hash: str = '',
    webgl_hash: str = '',
    fonts: str = '',
    platform: str = ''
) -> str:
    """
    Generate a unique device fingerprint from browser characteristics.
    
    Args:
        user_agent: Browser user agent string
        screen_resolution: Screen resolution (e.g., "1920x1080")
        timezone_offset: Timezone offset (e.g., "-330" for IST)
        languages: Browser languages
        canvas_hash: Canvas fingerprint hash
        webgl_hash: WebGL fingerprint hash
        fonts: Installed fonts list
        platform: Platform (e.g., "Win32", "Linux x86_64")
    
    Returns:
        SHA-256 hash of the combined fingerprint data
    """
    # Combine all fingerprint components
    fingerprint_data = {
        'ua': user_agent,
        'sr': screen_resolution,
        'tz': timezone_offset,
        'lang': languages,
        'canvas': canvas_hash,
        'webgl': webgl_hash,
        'fonts': fonts,
        'platform': platform
    }
    
    # Create deterministic string representation
    fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
    
    # Generate hash
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()


def get_client_info(request) -> Dict:
    """
    Extract client information from request.
    
    Args:
        request: Django HTTP request object
    
    Returns:
        Dictionary with client information
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    return {
        'ip_address': ip,
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'referrer': request.META.get('HTTP_REFERER', ''),
        'accept_language': request.META.get('HTTP_ACCEPT_LANGUAGE', ''),
    }


def is_suspicious_activity(
    ip_address: str,
    user_agent: str,
    recent_guests_count: int,
    time_window_minutes: int = 60
) -> tuple[bool, Optional[str]]:
    """
    Check if the activity looks suspicious (potential fraud).
    
    Args:
        ip_address: Client IP address
        user_agent: User agent string
        recent_guests_count: Number of recent registrations from this IP
        time_window_minutes: Time window to check
    
    Returns:
        Tuple of (is_suspicious, reason)
    """
    # Too many registrations from same IP
    if recent_guests_count > 10:
        return True, f"Too many registrations from same IP ({recent_guests_count})"
    
    # Known bot user agents
    bot_keywords = ['bot', 'crawler', 'spider', 'scrape', 'headless']
    ua_lower = user_agent.lower()
    for keyword in bot_keywords:
        if keyword in ua_lower:
            return True, f"Suspected bot activity: {keyword}"
    
    return False, None


class FingerprintValidator:
    """
    Validator for device fingerprints
    """
    
    MIN_FINGERPRINT_LENGTH = 32
    MAX_FINGERPRINT_LENGTH = 64
    
    @classmethod
    def validate(cls, fingerprint: str) -> tuple[bool, Optional[str]]:
        """
        Validate a fingerprint string.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not fingerprint:
            return False, "Fingerprint is required"
        
        if len(fingerprint) < cls.MIN_FINGERPRINT_LENGTH:
            return False, f"Fingerprint too short (min {cls.MIN_FINGERPRINT_LENGTH} chars)"
        
        if len(fingerprint) > cls.MAX_FINGERPRINT_LENGTH:
            return False, f"Fingerprint too long (max {cls.MAX_FINGERPRINT_LENGTH} chars)"
        
        # Check if valid hex string (for SHA-256)
        try:
            int(fingerprint, 16)
        except ValueError:
            return False, "Invalid fingerprint format"
        
        return True, None
