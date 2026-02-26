"""
AI app views package.

This package organizes AI-related views into focused modules:
- helpers: Response helpers and constants
- photo_analysis: Photo analysis and color extraction
- message_generation: Message and hashtag generation
- recommendations: Template and style recommendations
- usage: Usage tracking and limits

Generated automatically by refactor_ai_views_advanced.py
"""

from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
)

from .photo_analysis import (
    PhotoAnalysisViewSet,
    GeneratedMessageViewSet,
    PhotoAnalysisView,
    ColorExtractionView,
)

from .message_generation import (
    MoodDetectionView,
    GenerateMessagesView,
    GenerateHashtagsView,
    AnalyzePhotoView,
    ExtractColorsView,
    DetectMoodView,
    MessageStylesView,
)

from .recommendations import (
    StyleRecommendationsView,
    TemplateRecommendationsView,
    RecommendTemplatesView,
    RecommendStylesView,
)

from .usage import (
    AIUsageStatsView,
    AIUsageLimitsView,
    SmartSuggestionsView,
)

__all__ = [
    'AIUsageLimitsView',
    'AIUsageStatsView',
    'AnalyzePhotoView',
    'ColorExtractionView',
    'DetectMoodView',
    'ExtractColorsView',
    'GenerateHashtagsView',
    'GenerateMessagesView',
    'GeneratedMessageViewSet',
    'MessageStylesView',
    'MoodDetectionView',
    'PhotoAnalysisView',
    'PhotoAnalysisViewSet',
    'RecommendStylesView',
    'RecommendTemplatesView',
    'SmartSuggestionsView',
    'StyleRecommendationsView',
    'TemplateRecommendationsView',
    'add_rate_limit_headers',
    'create_error_response',
    'create_success_response',
]
