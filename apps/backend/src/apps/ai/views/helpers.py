"""
Shared helper functions and constants.

This module is part of the refactored AI views structure.
Generated automatically by refactor_ai_views_advanced.py
"""

import logging
from typing import Dict, Any, Optional

from rest_framework import status
from rest_framework.response import Response


# =============================================================================
# Constants
# =============================================================================

# Logger
logger = logging.getLogger(__name__)


MAX_FILE_SIZE_MB = 10

MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

ALLOWED_IMAGE_TYPES = frozenset([
    'image/jpeg', 'image/png', 'image/webp', 'image/jpg'
])

RATE_LIMIT_HEADER = 'X-RateLimit-Limit'

RATE_LIMIT_REMAINING_HEADER = 'X-RateLimit-Remaining'

RATE_LIMIT_RESET_HEADER = 'X-RateLimit-Reset'



def create_success_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> Response:
    """Create a standardized success response.
    
    Args:
        data: Response data payload.
        status_code: HTTP status code.
        meta: Optional metadata (pagination, rate limits, etc.).
        
    Returns:
        DRF Response object.
    """
    response_data: Dict[str, Any] = {
        'success': True,
        'data': data
    }
    
    if meta:
        response_data['meta'] = meta
    
    return Response(response_data, status=status_code)



def create_error_response(
    message: str,
    error_code: str = 'ERROR',
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> Response:
    """Create a standardized error response.
    
    Args:
        message: Human-readable error message.
        error_code: Machine-readable error code.
        status_code: HTTP status code.
        details: Additional error details.
        
    Returns:
        DRF Response object.
    """
    response_data: Dict[str, Any] = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        }
    }
    
    if details:
        response_data['error']['details'] = details
    
    return Response(response_data, status=status_code)



def add_rate_limit_headers(
    response: Response,
    limit: int,
    remaining: int,
    reset_seconds: int = 3600
) -> Response:
    """Add rate limit headers to response.
    
    Args:
        response: DRF Response object.
        limit: Rate limit cap.
        remaining: Remaining requests.
        reset_seconds: Seconds until limit resets.
        
    Returns:
        Modified Response object.
    """
    response[RATE_LIMIT_HEADER] = limit
    response[RATE_LIMIT_REMAINING_HEADER] = remaining
    response[RATE_LIMIT_RESET_HEADER] = reset_seconds
    return response


