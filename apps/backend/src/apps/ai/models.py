"""
Models for the AI app.

This module defines models for:
- Photo analysis results
- AI-generated messages
- API usage logging for rate limiting

All models include proper database indexes for query optimization,
field-level validation, and comprehensive string representations.

Example:
    >>> from apps.ai.models import PhotoAnalysis, GeneratedMessage
    >>> analysis = PhotoAnalysis.objects.create(
    ...     user=user,
    ...     image_url='https://example.com/photo.jpg',
    ...     primary_colors={'dominant': {'hex': '#A61E2A', 'name': 'Deep Red'}}
    ... )
"""

import uuid
from typing import Any, Dict, List, Optional

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


# =============================================================================
# Constants
# =============================================================================

# Maximum lengths for fields
MAX_URL_LENGTH = 500
MAX_STYLE_LENGTH = 20
MAX_FEATURE_TYPE_LENGTH = 30
MAX_ERROR_MESSAGE_LENGTH = 1000

# Default empty values for JSON fields
DEFAULT_DICT: Dict[str, Any] = {}
DEFAULT_LIST: List[Any] = []


# =============================================================================
# Validators
# =============================================================================

def validate_hex_color(value: str) -> None:
    """Validate a hex color code.
    
    Args:
        value: Color code to validate.
        
    Raises:
        ValidationError: If color code is invalid.
    """
    if not value:
        return
    
    # Remove # if present
    color = value.lstrip('#')
    
    # Check length
    if len(color) not in (3, 6):
        raise ValidationError(
            _('Color code must be 3 or 6 characters (e.g., "FFF" or "FFFFFF")'),
            params={'value': value}
        )
    
    # Check valid hex characters
    try:
        int(color, 16)
    except ValueError:
        raise ValidationError(
            _('Color code must contain only valid hex characters (0-9, A-F)'),
            params={'value': value}
        )


def validate_positive_integer(value: int) -> None:
    """Validate a positive integer.
    
    Args:
        value: Integer to validate.
        
    Raises:
        ValidationError: If value is not positive.
    """
    if value is not None and value < 0:
        raise ValidationError(
            _('Value must be a positive integer'),
            params={'value': value}
        )


# =============================================================================
# Photo Analysis Model
# =============================================================================

class PhotoAnalysis(models.Model):
    """Stores photo analysis results including color extraction,
    mood detection, and style recommendations.
    
    Attributes:
        id: Unique identifier (UUID).
        user: User who uploaded the photo.
        order: Associated order (optional).
        image_url: URL of the analyzed image.
        primary_colors: Extracted primary colors with hex codes and percentages.
        mood: Detected mood attributes (romantic, elegant, modern, etc.).
        style_recommendations: AI-generated style recommendations.
        created_at: When the analysis was created.
        updated_at: When the analysis was last updated.
    
    Example:
        >>> analysis = PhotoAnalysis.objects.create(
        ...     user=request.user,
        ...     image_url='https://example.com/photo.jpg',
        ...     primary_colors={
        ...         'dominant': {'hex': '#A61E2A', 'name': 'Deep Red', 'percentage': 35.5},
        ...         'palette': [{'hex': '#D4AF37', 'name': 'Gold', 'percentage': 25.2}]
        ...     }
        ... )
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the photo analysis")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='photo_analyses',
        help_text=_("User who uploaded the photo"),
        db_index=True
    )
    order = models.ForeignKey(
        'invitations.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photo_analyses',
        help_text=_("Associated order (optional)"),
        db_index=True
    )
    image_url = models.URLField(
        max_length=MAX_URL_LENGTH,
        validators=[URLValidator(schemes=['http', 'https'])],
        help_text=_("URL of the analyzed image")
    )
    primary_colors = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Extracted primary colors with hex codes and percentages"),
        encoder=None,
        decoder=None
    )
    mood = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Detected mood attributes (romantic, elegant, modern, etc.)"),
        encoder=None,
        decoder=None
    )
    style_recommendations = models.JSONField(
        default=list,
        blank=True,
        help_text=_("AI-generated style recommendations based on photo analysis"),
        encoder=None,
        decoder=None
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the analysis was created"),
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the analysis was last updated")
    )

    class Meta:
        """Meta options for PhotoAnalysis model."""
        app_label = 'ai'
        db_table = 'ai_photo_analysis'
        verbose_name = _('Photo Analysis')
        verbose_name_plural = _('Photo Analyses')
        ordering = ['-created_at']
        indexes = [
            # Composite index for common query pattern
            models.Index(fields=['user', '-created_at'], name='ai_photo_user_created_idx'),
            models.Index(fields=['order', '-created_at'], name='ai_photo_order_created_idx'),
            # Index for date-based filtering
            models.Index(fields=['created_at'], name='ai_photo_created_idx'),
        ]
        constraints = [
            # Ensure image_url is not empty
            models.CheckConstraint(
                check=~models.Q(image_url=''),
                name='ai_photo_nonempty_url'
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable string representation."""
        order_info = f" for order {self.order_id}" if self.order_id else ""
        return f"PhotoAnalysis({self.id.hex[:8]}) by User({self.user_id}){order_info}"
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"PhotoAnalysis("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"order_id={self.order_id}, "
            f"created_at={self.created_at.isoformat()}"
            f")"
        )

    def clean(self) -> None:
        """Validate model data before saving."""
        super().clean()
        
        # Validate primary_colors structure
        if self.primary_colors and not isinstance(self.primary_colors, dict):
            raise ValidationError({
                'primary_colors': _('Primary colors must be a dictionary')
            })
        
        # Validate mood structure
        if self.mood and not isinstance(self.mood, dict):
            raise ValidationError({
                'mood': _('Mood must be a dictionary')
            })
        
        # Validate style_recommendations structure
        if self.style_recommendations and not isinstance(self.style_recommendations, list):
            raise ValidationError({
                'style_recommendations': _('Style recommendations must be a list')
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the model after validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_primary_color_hex(self) -> Optional[str]:
        """Get the dominant primary color hex code.
        
        Returns:
            Hex color code or None if not found.
        """
        if not self.primary_colors:
            return None
        
        # Try different possible structures
        if 'dominant' in self.primary_colors:
            return self.primary_colors['dominant'].get('hex')
        
        if 'colors' in self.primary_colors and self.primary_colors['colors']:
            return self.primary_colors['colors'][0].get('color')
        
        return None

    def get_mood_tags(self) -> List[str]:
        """Get list of detected mood tags.
        
        Returns:
            List of mood tag strings.
        """
        if not self.mood:
            return []
        
        tags: List[str] = []
        
        # Primary mood
        if 'primary' in self.mood:
            tags.append(self.mood['primary'])
        
        # Secondary moods
        if 'secondary' in self.mood:
            secondary = self.mood['secondary']
            if isinstance(secondary, list):
                tags.extend(secondary)
            elif isinstance(secondary, str):
                tags.append(secondary)
        
        # Tags field (legacy)
        if 'tags' in self.mood and isinstance(self.mood['tags'], list):
            tags.extend(self.mood['tags'])
        
        return list(dict.fromkeys(tags))  # Remove duplicates while preserving order

    def get_recommendation_count(self) -> int:
        """Get the number of style recommendations.
        
        Returns:
            Number of recommendations.
        """
        return len(self.style_recommendations) if self.style_recommendations else 0


# =============================================================================
# Generated Message Model
# =============================================================================

class GeneratedMessage(models.Model):
    """Stores AI-generated messages for wedding invitations.
    
    Attributes:
        id: Unique identifier (UUID).
        user: User who generated the message.
        order: Associated order (optional).
        context: Context data (bride_name, groom_name, date, venue, etc.).
        generated_options: Array of generated message options.
        style_used: Style used for message generation.
        tokens_used: Number of tokens consumed for generation.
        created_at: When the message was generated.
    
    Example:
        >>> message = GeneratedMessage.objects.create(
        ...     user=request.user,
        ...     context={'bride_name': 'Jane', 'groom_name': 'John'},
        ...     generated_options=[
        ...         {'id': 'opt_1', 'text': '...', 'style': 'traditional'},
        ...         {'id': 'opt_2', 'text': '...', 'style': 'modern'}
        ...     ],
        ...     style_used='romantic'
        ... )
    """
    
    # Style choices
    STYLE_CHOICES = [
        ('romantic', _('Romantic')),
        ('formal', _('Formal')),
        ('casual', _('Casual')),
        ('funny', _('Funny')),
        ('poetic', _('Poetic')),
        ('traditional', _('Traditional')),
        ('modern', _('Modern')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the generated message")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_messages',
        help_text=_("User who generated the message"),
        db_index=True
    )
    order = models.ForeignKey(
        'invitations.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generated_messages',
        help_text=_("Associated order (optional)"),
        db_index=True
    )
    context = models.JSONField(
        default=dict,
        help_text=_("Context data: bride_name, groom_name, date, venue, etc."),
        encoder=None,
        decoder=None
    )
    generated_options = models.JSONField(
        default=list,
        help_text=_("Array of generated message options"),
        encoder=None,
        decoder=None
    )
    style_used = models.CharField(
        max_length=MAX_STYLE_LENGTH,
        choices=STYLE_CHOICES,
        default='romantic',
        help_text=_("Style used for message generation"),
        db_index=True
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of tokens consumed for generation")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the message was generated"),
        db_index=True
    )

    class Meta:
        """Meta options for GeneratedMessage model."""
        app_label = 'ai'
        db_table = 'ai_generated_message'
        verbose_name = _('Generated Message')
        verbose_name_plural = _('Generated Messages')
        ordering = ['-created_at']
        indexes = [
            # Composite indexes for common query patterns
            models.Index(fields=['user', '-created_at'], name='ai_msg_user_created_idx'),
            models.Index(fields=['order', '-created_at'], name='ai_msg_order_created_idx'),
            # Index for style-based filtering
            models.Index(fields=['style_used'], name='ai_msg_style_idx'),
            # Index for date-based filtering
            models.Index(fields=['created_at'], name='ai_msg_created_idx'),
        ]

    def __str__(self) -> str:
        """Return human-readable string representation."""
        order_info = f" for order {self.order_id}" if self.order_id else ""
        summary = self.get_context_summary()
        return f"GeneratedMessage({self.id.hex[:8]}) - {summary}{order_info}"
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"GeneratedMessage("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"style={self.style_used}, "
            f"options_count={self.get_options_count()}, "
            f"created_at={self.created_at.isoformat()}"
            f")"
        )

    def clean(self) -> None:
        """Validate model data before saving."""
        super().clean()
        
        # Validate context has required fields
        if self.context:
            if not isinstance(self.context, dict):
                raise ValidationError({
                    'context': _('Context must be a dictionary')
                })
            
            # Check for required fields
            required_fields = ['bride_name', 'groom_name']
            missing = [f for f in required_fields if f not in self.context or not self.context[f]]
            if missing:
                raise ValidationError({
                    'context': _('Missing required fields: {}').format(', '.join(missing))
                })
        
        # Validate generated_options structure
        if self.generated_options:
            if not isinstance(self.generated_options, list):
                raise ValidationError({
                    'generated_options': _('Generated options must be a list')
                })
            
            for i, opt in enumerate(self.generated_options):
                if not isinstance(opt, dict):
                    raise ValidationError({
                        'generated_options': _('Option {} must be a dictionary').format(i)
                    })
                if 'text' not in opt:
                    raise ValidationError({
                        'generated_options': _('Option {} missing required "text" field').format(i)
                    })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the model after validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_first_option(self) -> Optional[Dict[str, Any]]:
        """Get the first generated message option.
        
        Returns:
            First option dictionary or None.
        """
        if self.generated_options and isinstance(self.generated_options, list):
            return self.generated_options[0]
        return None

    def get_options_count(self) -> int:
        """Get the number of generated options.
        
        Returns:
            Number of options.
        """
        return len(self.generated_options) if isinstance(self.generated_options, list) else 0

    def get_context_summary(self) -> str:
        """Get a summary of the context.
        
        Returns:
            Summary string with couple names.
        """
        if not self.context or not isinstance(self.context, dict):
            return "Unknown"
        
        bride = self.context.get('bride_name', 'Unknown')
        groom = self.context.get('groom_name', 'Unknown')
        return f"{bride} & {groom}"


# =============================================================================
# AI Usage Log Model
# =============================================================================

class AIUsageLog(models.Model):
    """Tracks API usage for rate limiting, billing, and analytics.
    
    Attributes:
        id: Unique identifier (UUID).
        user: User who made the AI request.
        feature_type: Type of AI feature used.
        request_data: Request data sent to AI service.
        response_data: Response data from AI service.
        tokens_used: Number of tokens consumed.
        success: Whether the AI request was successful.
        error_message: Error message if the request failed.
        processing_time_ms: Processing time in milliseconds.
        created_at: When the request was made.
    
    Example:
        >>> log = AIUsageLog.objects.create(
        ...     user=request.user,
        ...     feature_type='message_generation',
        ...     tokens_used=500,
        ...     success=True
        ... )
    """
    
    # Feature type choices
    FEATURE_CHOICES = [
        ('photo_analysis', _('Photo Analysis')),
        ('message_generation', _('Message Generation')),
        ('template_recommendation', _('Template Recommendation')),
        ('color_extraction', _('Color Extraction')),
        ('mood_detection', _('Mood Detection')),
        ('smart_suggestions', _('Smart Suggestions')),
        ('hashtag_generation', _('Hashtag Generation')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_("Unique identifier for the usage log")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_usage_logs',
        help_text=_("User who made the AI request"),
        db_index=True
    )
    feature_type = models.CharField(
        max_length=MAX_FEATURE_TYPE_LENGTH,
        choices=FEATURE_CHOICES,
        help_text=_("Type of AI feature used"),
        db_index=True
    )
    request_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Request data sent to AI service"),
        encoder=None,
        decoder=None
    )
    response_data = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Response data from AI service"),
        encoder=None,
        decoder=None
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        help_text=_("Number of tokens consumed")
    )
    success = models.BooleanField(
        default=True,
        help_text=_("Whether the AI request was successful"),
        db_index=True
    )
    error_message = models.TextField(
        blank=True,
        help_text=_("Error message if the request failed")
    )
    processing_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=_("Processing time in milliseconds")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the request was made"),
        db_index=True
    )

    class Meta:
        """Meta options for AIUsageLog model."""
        app_label = 'ai'
        db_table = 'ai_usage_log'
        verbose_name = _('AI Usage Log')
        verbose_name_plural = _('AI Usage Logs')
        ordering = ['-created_at']
        indexes = [
            # Composite indexes for analytics queries
            models.Index(fields=['user', '-created_at'], name='ai_log_user_created_idx'),
            models.Index(fields=['feature_type', '-created_at'], name='ai_log_feature_created_idx'),
            # Index for filtering by success status
            models.Index(fields=['success'], name='ai_log_success_idx'),
            # Index for date-based analytics
            models.Index(fields=['created_at'], name='ai_log_created_idx'),
            # Composite index for today's usage queries
            models.Index(fields=['user', 'success', '-created_at'], name='ai_log_user_success_idx'),
        ]
        constraints = [
            # Ensure tokens_used is non-negative
            models.CheckConstraint(
                check=models.Q(tokens_used__gte=0),
                name='ai_log_nonnegative_tokens'
            ),
        ]

    def __str__(self) -> str:
        """Return human-readable string representation."""
        status = "✓" if self.success else "✗"
        return f"AIUsageLog({self.id.hex[:8]}) [{status}] {self.feature_type} - User({self.user_id})"
    
    def __repr__(self) -> str:
        """Return detailed string representation."""
        return (
            f"AIUsageLog("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"feature={self.feature_type}, "
            f"success={self.success}, "
            f"tokens={self.tokens_used}, "
            f"created_at={self.created_at.isoformat()}"
            f")"
        )

    def clean(self) -> None:
        """Validate model data before saving."""
        super().clean()
        
        # Validate feature_type is valid
        valid_features = [f[0] for f in self.FEATURE_CHOICES]
        if self.feature_type not in valid_features:
            raise ValidationError({
                'feature_type': _('Invalid feature type. Must be one of: {}').format(', '.join(valid_features))
            })
        
        # Validate error_message is provided if success=False
        if not self.success and not self.error_message:
            raise ValidationError({
                'error_message': _('Error message is required when success=False')
            })
        
        # Validate processing_time_ms is reasonable
        if self.processing_time_ms is not None and self.processing_time_ms > 300000:  # 5 minutes
            raise ValidationError({
                'processing_time_ms': _('Processing time seems too high (> 5 minutes)')
            })

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Save the model after validation."""
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_user_usage_today(cls, user: Any) -> Dict[str, Any]:
        """Get total tokens used by a user today.
        
        Args:
            user: User to check.
            
        Returns:
            Dictionary with total_tokens and count.
        """
        from django.utils import timezone
        today = timezone.now().date()
        logs = cls.objects.filter(
            user=user,
            created_at__date=today,
            success=True
        )
        
        result = logs.aggregate(
            total_tokens=models.Sum('tokens_used'),
            count=models.Count('id')
        )
        
        return {
            'total_tokens': result.get('total_tokens') or 0,
            'count': result.get('count') or 0
        }

    @classmethod
    def get_user_usage_this_month(cls, user: Any) -> Dict[str, Any]:
        """Get total tokens used by a user this month.
        
        Args:
            user: User to check.
            
        Returns:
            Dictionary with total_tokens and count.
        """
        from django.utils import timezone
        now = timezone.now()
        logs = cls.objects.filter(
            user=user,
            created_at__year=now.year,
            created_at__month=now.month,
            success=True
        )
        
        result = logs.aggregate(
            total_tokens=models.Sum('tokens_used'),
            count=models.Count('id')
        )
        
        return {
            'total_tokens': result.get('total_tokens') or 0,
            'count': result.get('count') or 0
        }

    @classmethod
    def get_feature_usage_summary(
        cls,
        user: Any,
        days: int = 30
    ) -> Dict[str, Dict[str, Any]]:
        """Get usage summary by feature type.
        
        Args:
            user: User to check.
            days: Number of days to look back.
            
        Returns:
            Dictionary with usage stats by feature.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        since = timezone.now() - timedelta(days=days)
        
        logs = cls.objects.filter(
            user=user,
            created_at__gte=since,
            success=True
        ).values('feature_type').annotate(
            total_tokens=models.Sum('tokens_used'),
            count=models.Count('id'),
            avg_processing_time=models.Avg('processing_time_ms')
        )
        
        return {
            item['feature_type']: {
                'total_tokens': item['total_tokens'] or 0,
                'count': item['count'],
                'avg_processing_time_ms': round(item['avg_processing_time'] or 0, 2)
            }
            for item in logs
        }

    def get_short_error(self, max_length: int = 100) -> str:
        """Get truncated error message.
        
        Args:
            max_length: Maximum length of error message.
            
        Returns:
            Truncated error message.
        """
        if not self.error_message:
            return ""
        
        if len(self.error_message) <= max_length:
            return self.error_message
        
        return self.error_message[:max_length - 3] + "..."


# =============================================================================
# Model Utilities
# =============================================================================

def get_default_json_dict() -> Dict[str, Any]:
    """Return empty dict for JSONField defaults.
    
    Returns:
        Empty dictionary.
    """
    return {}


def get_default_json_list() -> List[Any]:
    """Return empty list for JSONField defaults.
    
    Returns:
        Empty list.
    """
    return []
