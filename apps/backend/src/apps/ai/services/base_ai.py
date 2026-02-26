"""
Base AI Service with common functionality.

This module provides the base class for all AI services, including:
- Retry logic for failed requests
- Error handling with specific exception types
- Caching helpers
- Rate limiting checks
- Structured logging

Example:
    >>> from .base_ai import BaseAIService, AIServiceError
    >>> class MyAIService(BaseAIService):
    ...     def make_request(self, endpoint: str, data: Dict, headers: Optional[Dict] = None) -> Dict:
    ...         # Implementation
    ...         pass
"""

import time
import hashlib
import logging
from functools import wraps
from typing import Any, Callable, Optional, Dict, Type, Union, Tuple
from datetime import datetime, timedelta

from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# =============================================================================
# Logger Configuration
# =============================================================================

logger = logging.getLogger(__name__)


# =============================================================================
# Custom Exceptions
# =============================================================================

class AIServiceError(Exception):
    """Base exception for AI service errors.
    
    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code for client handling.
        details: Additional error context for debugging.
    """
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize AI service error.
        
        Args:
            message: Human-readable error description.
            error_code: Machine-readable error identifier.
            details: Additional error context.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'AI_SERVICE_ERROR'
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for API responses.
        
        Returns:
            Dictionary containing error details.
        """
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details
        }


class RateLimitError(AIServiceError):
    """Exception raised when rate limit is exceeded.
    
    Attributes:
        retry_after: Seconds until the rate limit resets.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        """Initialize rate limit error.
        
        Args:
            message: Error description.
            retry_after: Seconds until rate limit reset.
        """
        super().__init__(message, error_code='RATE_LIMIT_EXCEEDED')
        self.retry_after = retry_after


class AuthenticationError(AIServiceError):
    """Exception raised when AI service authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        """Initialize authentication error.
        
        Args:
            message: Error description.
        """
        super().__init__(message, error_code='AUTHENTICATION_ERROR')


class ValidationError(AIServiceError):
    """Exception raised when request validation fails."""
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize validation error.
        
        Args:
            message: Error description.
            details: Validation error details by field.
        """
        super().__init__(message, error_code='VALIDATION_ERROR', details=details)


class ServiceUnavailableError(AIServiceError):
    """Exception raised when AI service is unavailable."""
    
    def __init__(
        self,
        message: str = "AI service is currently unavailable"
    ):
        """Initialize service unavailable error.
        
        Args:
            message: Error description.
        """
        super().__init__(message, error_code='SERVICE_UNAVAILABLE')


# =============================================================================
# Decorators
# =============================================================================

def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """Decorator to retry a function on failure with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
        exceptions: Tuple of exception types to catch and retry.
        
    Returns:
        Decorated function with retry logic.
        
    Example:
        >>> @retry_on_failure(max_retries=3, delay=1.0, exceptions=(ConnectionError,))
        >>> def fetch_data():
        >>>     return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception: Optional[Exception] = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            if last_exception is not None:
                raise last_exception
            return None
        
        return wrapper
    return decorator


# =============================================================================
# Input Validation
# =============================================================================

def validate_string(value: Any, field_name: str, max_length: int = 1000) -> str:
    """Validate and sanitize a string input.
    
    Args:
        value: Input value to validate.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed string length.
        
    Returns:
        Validated string value.
        
    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(value, str):
        raise ValidationError(
            f"{field_name} must be a string",
            details={field_name: "Invalid type"}
        )
    
    if not value.strip():
        raise ValidationError(
            f"{field_name} cannot be empty",
            details={field_name: "Empty value"}
        )
    
    if len(value) > max_length:
        raise ValidationError(
            f"{field_name} exceeds maximum length of {max_length}",
            details={field_name: f"Length {len(value)} > {max_length}"}
        )
    
    return value.strip()


def validate_positive_integer(value: Any, field_name: str) -> int:
    """Validate a positive integer input.
    
    Args:
        value: Input value to validate.
        field_name: Name of the field for error messages.
        
    Returns:
        Validated integer value.
        
    Raises:
        ValidationError: If validation fails.
    """
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(
            f"{field_name} must be an integer",
            details={field_name: "Invalid type"}
        )
    
    if value <= 0:
        raise ValidationError(
            f"{field_name} must be positive",
            details={field_name: f"Value {value} <= 0"}
        )
    
    return value


def validate_url(url: str, field_name: str = "url") -> str:
    """Validate a URL string.
    
    Args:
        url: URL to validate.
        field_name: Name of the field for error messages.
        
    Returns:
        Validated URL string.
        
    Raises:
        ValidationError: If validation fails.
    """
    import re
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        raise ValidationError(
            f"{field_name} must be a valid URL",
            details={field_name: f"Invalid URL format: {url}"}
        )
    
    return url


# =============================================================================
# Base AI Service
# =============================================================================

class BaseAIService:
    """Base class for AI services.
    
    Provides common functionality including:
    - Retry logic
    - Error handling
    - Caching
    - Rate limiting
    - Usage logging
    
    Attributes:
        CACHE_TIMEOUT: Default cache timeout in seconds (1 hour).
        RATE_LIMIT_REQUESTS: Default rate limit requests per window.
        RATE_LIMIT_WINDOW: Rate limit window in seconds (1 hour).
    """
    
    # Default cache timeout in seconds (1 hour)
    CACHE_TIMEOUT: int = 3600
    
    # Default rate limit settings
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Sensitive keys to sanitize from logs
    SENSITIVE_KEYS: frozenset = frozenset([
        'password', 'token', 'secret', 'api_key', 'credit_card',
        'apikey', 'api-key', 'auth_token', 'access_token', 'refresh_token'
    ])
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the AI service.
        
        Args:
            api_key: API key for the AI service (defaults to settings).
            model: Model to use for AI requests.
        """
        self.api_key = api_key or getattr(settings, 'AI_API_KEY', None)
        self.model = model or getattr(settings, 'AI_MODEL', 'default')
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_cache_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """Generate a cache key based on prefix and arguments.
        
        Args:
            prefix: Prefix for the cache key.
            *args: Positional arguments to include in key.
            **kwargs: Keyword arguments to include in key.
            
        Returns:
            Cache key string.
        """
        # Create a string representation of arguments
        args_str = str(args) + str(sorted(kwargs.items()))
        hash_str = hashlib.md5(args_str.encode()).hexdigest()
        return f"ai:{prefix}:{hash_str}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get a value from cache.
        
        Args:
            cache_key: Cache key to retrieve.
            
        Returns:
            Cached value or None if not found.
        """
        try:
            return cache.get(cache_key)
        except Exception as e:
            self.logger.warning(f"Cache get failed: {e}")
            return None
    
    def _set_cache(
        self,
        cache_key: str,
        value: Any,
        timeout: Optional[int] = None
    ) -> bool:
        """Set a value in cache.
        
        Args:
            cache_key: Cache key to set.
            value: Value to cache.
            timeout: Cache timeout in seconds (defaults to CACHE_TIMEOUT).
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            cache.set(cache_key, value, timeout or self.CACHE_TIMEOUT)
            return True
        except Exception as e:
            self.logger.warning(f"Cache set failed: {e}")
            return False
    
    def _invalidate_cache(self, cache_key: str) -> bool:
        """Invalidate a cache entry.
        
        Args:
            cache_key: Cache key to invalidate.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            cache.delete(cache_key)
            return True
        except Exception as e:
            self.logger.warning(f"Cache delete failed: {e}")
            return False
    
    def check_rate_limit(
        self,
        user: AbstractUser,
        feature_type: str
    ) -> bool:
        """Check if user has exceeded rate limit for a feature.
        
        Args:
            user: User to check.
            feature_type: Type of feature being used.
            
        Returns:
            True if within rate limit, False otherwise.
        """
        cache_key = f"ai:ratelimit:{user.id}:{feature_type}"
        
        try:
            # Get current count from cache
            current_count: int = cache.get(cache_key, 0)
            
            if current_count >= self.RATE_LIMIT_REQUESTS:
                self.logger.warning(
                    f"Rate limit exceeded for user {user.id}, feature {feature_type}"
                )
                return False
            
            # Increment count
            cache.set(cache_key, current_count + 1, self.RATE_LIMIT_WINDOW)
            return True
            
        except Exception as e:
            self.logger.warning(f"Rate limit check failed: {e}")
            # Fail open - allow request if we can't check rate limit
            return True
    
    def get_rate_limit_remaining(
        self,
        user: AbstractUser,
        feature_type: str
    ) -> int:
        """Get remaining rate limit for a user and feature.
        
        Args:
            user: User to check.
            feature_type: Type of feature.
            
        Returns:
            Number of remaining requests.
        """
        cache_key = f"ai:ratelimit:{user.id}:{feature_type}"
        
        try:
            current_count: int = cache.get(cache_key, 0)
            return max(0, self.RATE_LIMIT_REQUESTS - current_count)
        except Exception as e:
            self.logger.warning(f"Rate limit check failed: {e}")
            return self.RATE_LIMIT_REQUESTS
    
    def log_usage(
        self,
        user: AbstractUser,
        feature_type: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        tokens_used: int = 0,
        success: bool = True,
        error_message: str = "",
        processing_time_ms: Optional[int] = None
    ) -> Optional[Any]:
        """Log AI usage for analytics and rate limiting.
        
        Args:
            user: User who made the request.
            feature_type: Type of feature used.
            request_data: Data sent in the request.
            response_data: Data received in the response.
            tokens_used: Number of tokens consumed.
            success: Whether the request was successful.
            error_message: Error message if request failed.
            processing_time_ms: Processing time in milliseconds.
            
        Returns:
            Created AIUsageLog instance or None if logging failed.
            
        Raises:
            AIServiceError: Only if logging fails in strict mode.
        """
        # Lazy import to avoid AppRegistryNotReady
        from ..models import AIUsageLog
        
        try:
            log = AIUsageLog.objects.create(
                user=user,
                feature_type=feature_type,
                request_data=self._sanitize_for_log(request_data),
                response_data=self._sanitize_for_log(response_data) if success else {},
                tokens_used=tokens_used,
                success=success,
                error_message=error_message if not success else "",
                processing_time_ms=processing_time_ms
            )
            self.logger.debug(
                f"Logged AI usage: {feature_type} for user {user.id}, "
                f"tokens: {tokens_used}, success: {success}"
            )
            return log
        except Exception as e:
            self.logger.error(f"Failed to log AI usage: {e}")
            return None
    
    def _sanitize_for_log(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data before logging to remove sensitive information.
        
        Args:
            data: Data to sanitize.
            
        Returns:
            Sanitized data with sensitive fields redacted.
        """
        if not isinstance(data, dict):
            return data
        
        sanitized: Dict[str, Any] = {}
        
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = '***REDACTED***'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_for_log(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_for_log(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized
    
    @retry_on_failure(
        max_retries=3,
        delay=1.0,
        backoff=2.0,
        exceptions=(AIServiceError, ConnectionError, TimeoutError)
    )
    def make_request(
        self,
        endpoint: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make a request to the AI service with retry logic.
        
        Args:
            endpoint: API endpoint.
            data: Request data.
            headers: Optional headers.
            
        Returns:
            Response data.
            
        Raises:
            NotImplementedError: Subclasses must implement this method.
            AIServiceError: If the request fails.
        """
        raise NotImplementedError("Subclasses must implement make_request")
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ) -> AIServiceError:
        """Convert an exception to an AIServiceError.
        
        Args:
            error: Original exception.
            context: Additional context about where the error occurred.
            
        Returns:
            AIServiceError with appropriate error code.
        """
        context_str = f" in {context}" if context else ""
        
        # If already an AIServiceError, return as-is
        if isinstance(error, AIServiceError):
            return error
        
        error_message = str(error)
        error_lower = error_message.lower()
        
        # Classify common errors
        if any(term in error_lower for term in ['rate limit', 'too many requests', '429']):
            return RateLimitError(f"Rate limit exceeded{context_str}")
        elif any(term in error_lower for term in ['authentication', 'unauthorized', '401', '403']):
            return AuthenticationError(f"Authentication failed{context_str}")
        elif any(term in error_lower for term in ['validation', 'invalid', '400']):
            return ValidationError(
                f"Validation error{context_str}",
                {'original_error': error_message}
            )
        elif any(term in error_lower for term in ['timeout', 'connection', 'unavailable', '503']):
            return ServiceUnavailableError(f"Service unavailable{context_str}: {error_message}")
        else:
            return AIServiceError(
                f"AI service error{context_str}: {error_message}",
                details={'original_error': error_message}
            )
