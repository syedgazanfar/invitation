"""
AI App for the Wedding Invitation Platform.

This app provides AI-powered features:
- Photo analysis (color extraction, mood detection)
- Message generation for invitations
- Template recommendations
- Smart suggestions for event planning

Usage:
    from apps.ai.services import PhotoAnalysisService, MessageGenerationService
    
    # Analyze a photo
    service = PhotoAnalysisService()
    analysis = service.analyze_photo(image_url, user)
    
    # Generate messages
    service = MessageGenerationService()
    messages = service.generate_messages(context, style, user)
    
    # Import models when needed (after Django apps are ready)
    from apps.ai.models import PhotoAnalysis, GeneratedMessage, AIUsageLog
"""

default_app_config = 'apps.ai.apps.AIConfig'

# Version info
__version__ = '1.0.0'

# Services are imported lazily to avoid AppRegistryNotReady errors
def _get_services():
    """Lazy import of services."""
    from .services import (
        PhotoAnalysisService,
        MessageGenerationService,
        RecommendationService,
        BaseAIService,
    )
    return {
        'PhotoAnalysisService': PhotoAnalysisService,
        'MessageGenerationService': MessageGenerationService,
        'RecommendationService': RecommendationService,
        'BaseAIService': BaseAIService,
    }

# Keep __all__ for documentation purposes
__all__ = [
    'PhotoAnalysisService',
    'MessageGenerationService', 
    'RecommendationService',
    'BaseAIService',
    'PhotoAnalysis',
    'GeneratedMessage',
    'AIUsageLog',
]
