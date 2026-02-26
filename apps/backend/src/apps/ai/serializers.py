"""
Serializers for the AI app.

This module provides serializers for:
- Photo analysis requests and responses
- Message generation requests and responses
- AI usage logs and statistics
- Template recommendations
"""

from rest_framework import serializers
from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog


# =============================================================================
# Photo Analysis Serializers
# =============================================================================

class PhotoAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer for PhotoAnalysis model.
    
    Includes computed fields for dominant color and mood tags.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    order_title = serializers.CharField(source='order.order_number', read_only=True, default=None)
    dominant_color = serializers.SerializerMethodField()
    mood_tags = serializers.SerializerMethodField()
    
    class Meta:
        model = PhotoAnalysis
        fields = [
            'id',
            'user',
            'user_email',
            'order',
            'order_title',
            'image_url',
            'primary_colors',
            'dominant_color',
            'mood',
            'mood_tags',
            'style_recommendations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'order_title',
            'primary_colors',
            'mood',
            'style_recommendations',
            'created_at',
            'updated_at',
        ]
    
    def get_dominant_color(self, obj):
        """Get the dominant color hex code."""
        return obj.get_primary_color_hex()
    
    def get_mood_tags(self, obj):
        """Get mood tags as a list."""
        return obj.get_mood_tags()
    
    def create(self, validated_data):
        """Set the user from the request context."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PhotoAnalysisCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a photo analysis request.
    
    Used for URL-based photo analysis (legacy).
    """
    
    image_url = serializers.URLField(required=True)
    order_id = serializers.UUIDField(required=False, allow_null=True)
    extract_colors = serializers.BooleanField(default=True)
    detect_mood = serializers.BooleanField(default=True)
    generate_recommendations = serializers.BooleanField(default=True)


class PhotoUploadSerializer(serializers.Serializer):
    """
    Serializer for photo upload analysis.
    
    Handles multipart form data with photo upload.
    """
    
    EVENT_TYPE_CHOICES = [
        ('WEDDING', 'Wedding'),
        ('BIRTHDAY', 'Birthday'),
        ('PARTY', 'Party'),
        ('FESTIVAL', 'Festival'),
        ('ANNIVERSARY', 'Anniversary'),
        ('CORPORATE', 'Corporate'),
        ('DESTINATION', 'Destination'),
    ]
    
    photo = serializers.ImageField(required=True)
    event_type = serializers.ChoiceField(
        choices=EVENT_TYPE_CHOICES,
        default='WEDDING',
        required=False
    )
    order_id = serializers.IntegerField(required=False, allow_null=True)


class ColorInfoSerializer(serializers.Serializer):
    """Serializer for color information."""
    
    hex = serializers.CharField(max_length=7)
    percentage = serializers.FloatField(min_value=0, max_value=100)
    name = serializers.CharField(max_length=50, required=False)


class PhotoAnalysisResponseSerializer(serializers.Serializer):
    """
    Serializer for photo analysis response.
    
    Returns comprehensive analysis results.
    """
    
    analysis_id = serializers.UUIDField()
    primary_colors = serializers.DictField()
    mood = serializers.DictField()
    style_recommendations = serializers.ListField()
    ai_suggestions = serializers.DictField()


class ColorExtractionResponseSerializer(serializers.Serializer):
    """
    Serializer for color extraction response.
    
    Returns extracted colors with details.
    """
    
    dominant = ColorInfoSerializer()
    palette = ColorInfoSerializer(many=True)
    palette_type = serializers.CharField()


class MoodDetectionResponseSerializer(serializers.Serializer):
    """
    Serializer for mood detection response.
    
    Returns detected mood attributes.
    """
    
    primary_mood = serializers.CharField()
    confidence = serializers.FloatField(min_value=0, max_value=1)
    tags = serializers.ListField(child=serializers.CharField())
    emotions = serializers.ListField(child=serializers.CharField())
    atmosphere = serializers.CharField()


# =============================================================================
# Message Generation Serializers
# =============================================================================

class GeneratedMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for GeneratedMessage model.
    
    Includes computed fields for couple names and first option.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    order_title = serializers.CharField(source='order.order_number', read_only=True, default=None)
    couple_names = serializers.SerializerMethodField()
    first_option = serializers.SerializerMethodField()
    
    class Meta:
        model = GeneratedMessage
        fields = [
            'id',
            'user',
            'user_email',
            'event',
            'order_title',
            'context',
            'couple_names',
            'generated_options',
            'first_option',
            'style_used',
            'tokens_used',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'user_email',
            'order_title',
            'generated_options',
            'tokens_used',
            'created_at',
        ]
    
    def get_couple_names(self, obj):
        """Get the couple names from context."""
        return obj.get_context_summary()
    
    def get_first_option(self, obj):
        """Get the first generated option."""
        return obj.get_first_option()
    
    def create(self, validated_data):
        """Set the user from the request context."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class GenerateMessageRequestSerializer(serializers.Serializer):
    """
    Legacy serializer for message generation request.
    
    Used for backwards compatibility.
    """
    
    STYLE_CHOICES = [
        ('romantic', 'Romantic'),
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('funny', 'Funny'),
        ('poetic', 'Poetic'),
        ('traditional', 'Traditional'),
        ('modern', 'Modern'),
    ]
    
    bride_name = serializers.CharField(max_length=100, required=True)
    groom_name = serializers.CharField(max_length=100, required=True)
    event_date = serializers.DateField(required=False, allow_null=True)
    venue = serializers.CharField(max_length=200, required=False, allow_blank=True)
    additional_context = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Additional context or special requests for the message"
    )
    style = serializers.ChoiceField(
        choices=STYLE_CHOICES,
        default='romantic'
    )
    num_options = serializers.IntegerField(
        min_value=1,
        max_value=5,
        default=3,
        help_text="Number of message options to generate"
    )
    event_id = serializers.UUIDField(required=False, allow_null=True)


class MessageGenerationRequestSerializer(serializers.Serializer):
    """
    Serializer for message generation request.
    
    Handles comprehensive message generation parameters.
    """
    
    STYLE_CHOICES = [
        ('romantic', 'Romantic'),
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('funny', 'Funny'),
        ('poetic', 'Poetic'),
        ('traditional', 'Traditional'),
        ('modern', 'Modern'),
    ]
    
    TONE_CHOICES = [
        ('warm', 'Warm'),
        ('formal', 'Formal'),
        ('casual', 'Casual'),
        ('funny', 'Funny'),
    ]
    
    bride_name = serializers.CharField(max_length=100, required=True)
    groom_name = serializers.CharField(max_length=100, required=True)
    event_type = serializers.ChoiceField(
        choices=[
            ('WEDDING', 'Wedding'),
            ('BIRTHDAY', 'Birthday'),
            ('PARTY', 'Party'),
            ('FESTIVAL', 'Festival'),
        ],
        default='WEDDING'
    )
    style = serializers.ChoiceField(
        choices=STYLE_CHOICES,
        default='romantic',
        required=False
    )
    culture = serializers.CharField(
        max_length=50,
        default='modern',
        required=False
    )
    tone = serializers.ChoiceField(
        choices=TONE_CHOICES,
        default='warm',
        required=False
    )
    event_date = serializers.DateField(required=False, allow_null=True)
    venue = serializers.CharField(max_length=200, required=False, allow_blank=True)
    details = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Additional details about the event"
    )


class MessageOptionSerializer(serializers.Serializer):
    """Serializer for a message option."""
    
    id = serializers.CharField()
    text = serializers.CharField()
    style = serializers.CharField()
    tone = serializers.CharField()


class MessageGenerationResponseSerializer(serializers.Serializer):
    """
    Serializer for message generation response.
    
    Returns generated message options.
    """
    
    options = MessageOptionSerializer(many=True)
    tokens_used = serializers.IntegerField()
    generation_time_ms = serializers.IntegerField()


# =============================================================================
# Hashtag Generation Serializers
# =============================================================================

class HashtagGenerationSerializer(serializers.Serializer):
    """
    Serializer for hashtag generation request.
    """
    
    STYLE_CHOICES = [
        ('romantic', 'Romantic'),
        ('funny', 'Funny'),
        ('modern', 'Modern'),
    ]
    
    bride_name = serializers.CharField(max_length=100, required=True)
    groom_name = serializers.CharField(max_length=100, required=True)
    style = serializers.ChoiceField(
        choices=STYLE_CHOICES,
        default='romantic',
        required=False
    )
    count = serializers.IntegerField(
        min_value=1,
        max_value=30,
        default=10,
        required=False
    )


# =============================================================================
# Template Recommendation Serializers
# =============================================================================

class TemplateRecommendationSerializer(serializers.Serializer):
    """
    Serializer for template recommendation.
    
    Includes match score and reasons.
    """
    
    template_id = serializers.CharField()
    name = serializers.CharField()
    match_score = serializers.FloatField(min_value=0, max_value=1)
    match_reasons = serializers.ListField(child=serializers.CharField())
    preview_url = serializers.URLField(required=False, allow_null=True)
    thumbnail = serializers.URLField(required=False, allow_null=True)


class StyleRecommendationSerializer(serializers.Serializer):
    """
    Serializer for style recommendation.
    
    Includes fonts and color recommendations.
    """
    
    style_name = serializers.CharField()
    match_score = serializers.FloatField(min_value=0, max_value=1)
    color_palette = serializers.ListField(
        child=serializers.CharField(),
        help_text="Recommended color palette hex codes"
    )
    font_recommendations = serializers.ListField(
        child=serializers.CharField(),
        help_text="Recommended font styles"
    )
    description = serializers.CharField(
        help_text="Description of the recommended style"
    )


class StyleRecommendationDetailSerializer(serializers.Serializer):
    """
    Detailed serializer for style recommendations.
    
    Includes additional details like suitable events and decor elements.
    """
    
    style = serializers.CharField()
    match_confidence = serializers.FloatField(min_value=0, max_value=1)
    details = serializers.DictField()


# =============================================================================
# Usage and Statistics Serializers
# =============================================================================

class AIUsageLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AIUsageLog model.
    
    Includes human-readable feature type display.
    """
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    feature_type_display = serializers.CharField(
        source='get_feature_type_display',
        read_only=True
    )
    
    class Meta:
        model = AIUsageLog
        fields = [
            'id',
            'user',
            'user_email',
            'feature_type',
            'feature_type_display',
            'tokens_used',
            'success',
            'processing_time_ms',
            'created_at',
        ]
        read_only_fields = fields


class AIUsageStatsSerializer(serializers.Serializer):
    """
    Serializer for AI usage statistics.
    
    Aggregated daily and monthly usage data.
    """
    
    total_requests_today = serializers.IntegerField()
    total_tokens_today = serializers.IntegerField()
    total_requests_this_month = serializers.IntegerField()
    total_tokens_this_month = serializers.IntegerField()
    requests_by_feature = serializers.DictField(
        child=serializers.IntegerField()
    )


class FeatureUsageSerializer(serializers.Serializer):
    """Serializer for feature-specific usage."""
    
    used_today = serializers.IntegerField()
    limit = serializers.IntegerField()
    remaining = serializers.IntegerField()


class AIUsageLimitsSerializer(serializers.Serializer):
    """
    Serializer for AI usage limits.
    
    Returns current limits and remaining quota.
    """
    
    daily_token_limit = serializers.IntegerField()
    monthly_token_limit = serializers.IntegerField()
    tokens_used_today = serializers.IntegerField()
    tokens_used_this_month = serializers.IntegerField()
    tokens_remaining_today = serializers.IntegerField()
    tokens_remaining_this_month = serializers.IntegerField()
    can_make_request = serializers.BooleanField()
    feature_usage = serializers.DictField(
        child=FeatureUsageSerializer()
    )


class AILimitsSerializer(serializers.Serializer):
    """
    Legacy serializer for AI usage limits.
    
    Simple version for backwards compatibility.
    """
    
    daily_token_limit = serializers.IntegerField()
    monthly_token_limit = serializers.IntegerField()
    tokens_used_today = serializers.IntegerField()
    tokens_used_this_month = serializers.IntegerField()
    tokens_remaining_today = serializers.IntegerField()
    tokens_remaining_this_month = serializers.IntegerField()
    can_make_request = serializers.BooleanField()


# =============================================================================
# Smart Suggestion Serializers
# =============================================================================

class SmartSuggestionRequestSerializer(serializers.Serializer):
    """
    Serializer for smart suggestion request.
    """
    
    CATEGORY_CHOICES = [
        ('venue', 'Venue'),
        ('timeline', 'Timeline'),
        ('budget', 'Budget'),
        ('decor', 'Decor'),
        ('photography', 'Photography'),
        ('invitation', 'Invitation'),
    ]
    
    category = serializers.ChoiceField(choices=CATEGORY_CHOICES)
    context = serializers.DictField(required=False, default=dict)


class SmartSuggestionResponseSerializer(serializers.Serializer):
    """
    Serializer for smart suggestion response.
    """
    
    category = serializers.CharField()
    suggestions = serializers.ListField(child=serializers.CharField())
    context_used = serializers.DictField()
