"""
URL configuration for the AI app.

This module defines URL patterns for AI-powered features:
- Photo analysis (upload, color extraction, mood detection)
- Message generation
- Template recommendations
- Style recommendations
- Hashtag generation
- Usage tracking and limits
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


app_name = 'ai'

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'photo-analysis', views.PhotoAnalysisViewSet, basename='photo-analysis')
router.register(r'generated-messages', views.GeneratedMessageViewSet, basename='generated-messages')

# URL patterns
urlpatterns = [
    # Include router URLs (for CRUD operations)
    path('', include(router.urls)),
    
    # =========================================================================
    # Photo Analysis Endpoints
    # =========================================================================
    
    # Main photo analysis with file upload (new recommended endpoint)
    path('analyze-photo/', views.PhotoAnalysisView.as_view(), name='analyze-photo'),
    
    # Color extraction (file upload or URL)
    path('extract-colors/', views.ColorExtractionView.as_view(), name='extract-colors'),
    
    # Mood detection (file upload or URL)
    path('detect-mood/', views.MoodDetectionView.as_view(), name='detect-mood'),
    
    # Legacy photo analysis with URL (backwards compatibility)
    path('analyze-photo-url/', views.AnalyzePhotoView.as_view(), name='analyze-photo-url'),
    
    # =========================================================================
    # Message Generation Endpoints
    # =========================================================================
    
    # Generate invitation messages
    path('generate-messages/', views.GenerateMessagesView.as_view(), name='generate-messages'),
    
    # Get available message styles
    path('message-styles/', views.MessageStylesView.as_view(), name='message-styles'),
    
    # =========================================================================
    # Hashtag Generation Endpoints
    # =========================================================================
    
    # Generate wedding hashtags
    path('generate-hashtags/', views.GenerateHashtagsView.as_view(), name='generate-hashtags'),
    
    # =========================================================================
    # Recommendation Endpoints
    # =========================================================================
    
    # Template recommendations (GET with query params)
    path('recommend-templates/', views.TemplateRecommendationsView.as_view(), name='recommend-templates'),
    
    # Style recommendations based on query params
    path('style-recommendations/', views.StyleRecommendationsView.as_view(), name='style-recommendations'),
    
    # Legacy template recommendations (POST with body)
    path('recommend-templates-post/', views.RecommendTemplatesView.as_view(), name='recommend-templates-post'),
    
    # Style recommendations based on photo analysis
    path('recommend-styles/', views.RecommendStylesView.as_view(), name='recommend-styles'),
    
    # =========================================================================
    # Usage and Limits Endpoints
    # =========================================================================
    
    # Get AI usage statistics
    path('usage/', views.AIUsageStatsView.as_view(), name='usage-stats'),
    
    # Get AI usage limits
    path('limits/', views.AIUsageLimitsView.as_view(), name='usage-limits'),
    
    # Legacy usage endpoints (backwards compatibility)
    path('ai-usage/', views.AIUsageView.as_view(), name='ai-usage'),
    path('ai-limits/', views.AILimitsView.as_view(), name='ai-limits'),
    
    # =========================================================================
    # Smart Suggestions Endpoints
    # =========================================================================
    
    # Get smart suggestions for event planning
    path('smart-suggestions/', views.SmartSuggestionsView.as_view(), name='smart-suggestions'),
]
