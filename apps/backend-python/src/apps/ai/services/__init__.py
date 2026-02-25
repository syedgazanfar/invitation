"""
AI Services module.

This module provides various AI-powered services for the wedding invitation platform.

Available Services:
    - BaseAIService: Base class with common functionality
    - PhotoAnalysisService: Photo color extraction and mood detection
    - MessageGenerationService: AI-powered message generation
    - RecommendationService: Template and style recommendations

Available Exceptions:
    - AIServiceError: Base exception for AI service errors
    - RateLimitError: Rate limit exceeded
    - AuthenticationError: Authentication failed
    - ValidationError: Input validation failed
    - ServiceUnavailableError: Service temporarily unavailable

Available Decorators:
    - retry_on_failure: Retry decorator with exponential backoff

Available Utilities:
    - validate_string: String input validation
    - validate_positive_integer: Positive integer validation
    - validate_url: URL validation

Example:
    >>> from apps.ai.services import (
    ...     MessageGenerationService,
    ...     AIServiceError,
    ...     RateLimitError
    ... )
    >>> service = MessageGenerationService()
    >>> try:
    ...     result = service.generate_messages(context)
    ... except RateLimitError as e:
    ...     print(f"Rate limited. Retry after {e.retry_after} seconds")
"""

from .base_ai import (
    BaseAIService,
    AIServiceError,
    RateLimitError,
    AuthenticationError,
    ValidationError,
    ServiceUnavailableError,
    retry_on_failure,
    validate_string,
    validate_positive_integer,
    validate_url,
)
from .photo_analysis import PhotoAnalysisService
from .message_generator import MessageGenerationService
from .recommendation import RecommendationService

__all__ = [
    # Services
    'BaseAIService',
    'PhotoAnalysisService',
    'MessageGenerationService',
    'RecommendationService',
    # Exceptions
    'AIServiceError',
    'RateLimitError',
    'AuthenticationError',
    'ValidationError',
    'ServiceUnavailableError',
    # Decorators
    'retry_on_failure',
    # Utilities
    'validate_string',
    'validate_positive_integer',
    'validate_url',
]
