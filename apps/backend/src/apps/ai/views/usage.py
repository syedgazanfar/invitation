"""
Usage tracking and limits views.

This module is part of the refactored AI views structure.
Generated automatically by refactor_ai_views_advanced.py
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

from ..models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from ..serializers import (
    PhotoAnalysisSerializer,
    PhotoAnalysisCreateSerializer,
    PhotoUploadSerializer,
    PhotoAnalysisResponseSerializer,
    GeneratedMessageSerializer,
    GenerateMessageRequestSerializer,
    MessageGenerationRequestSerializer,
    AIUsageLogSerializer,
    AIUsageStatsSerializer,
    AILimitsSerializer,
)
from ..permissions import CanUseAIFeature, IsOwnerOrReadOnly
from ..services import PhotoAnalysisService, MessageGenerationService, RecommendationService
from ..services.base_ai import AIServiceError, RateLimitError, ValidationError
from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_IMAGE_TYPES,
)

class AIUsageStatsView(APIView):
    """GET /api/v1/ai/usage/ - Get user's AI usage statistics.
    
    Returns counts of each feature used.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return AI usage statistics for the user."""
        # Get today's usage
        today_usage = AIUsageLog.get_user_usage_today(request.user)
        
        # Get this month's usage
        month_usage = AIUsageLog.get_user_usage_this_month(request.user)
        
        # Get requests by feature type
        today = timezone.now().date()
        feature_counts = AIUsageLog.objects.filter(
            user=request.user,
            created_at__date=today,
            success=True
        ).values('feature_type').annotate(
            count=models.Count('id')
        )
        
        requests_by_feature = {
            item['feature_type']: item['count']
            for item in feature_counts
        }
        
        # Get feature display names
        feature_display_names = dict(AIUsageLog.FEATURE_CHOICES)
        
        data = {
            'total_requests_today': today_usage.get('count') or 0,
            'total_tokens_today': today_usage.get('total_tokens') or 0,
            'total_requests_this_month': month_usage.get('count') or 0,
            'total_tokens_this_month': month_usage.get('total_tokens') or 0,
            'requests_by_feature': requests_by_feature,
            'feature_display_names': feature_display_names,
        }
        
        return create_success_response(data)



class AIUsageLimitsView(APIView):
    """GET /api/v1/ai/limits/ - Get user's current rate limits.
    
    Returns remaining quota for each feature.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return AI usage limits for the user."""
        # Get permission class to check limits
        from .permissions import CanUseAIFeature
        permission = CanUseAIFeature()
        limits = permission.get_plan_limits(request.user)
        
        # Get current usage
        today_usage = AIUsageLog.get_user_usage_today(request.user)
        month_usage = AIUsageLog.get_user_usage_this_month(request.user)
        
        tokens_used_today = today_usage.get('total_tokens') or 0
        tokens_used_this_month = month_usage.get('total_tokens') or 0
        
        # Get feature-specific usage
        today = timezone.now().date()
        feature_usage = {}
        for feature_type, _ in AIUsageLog.FEATURE_CHOICES:
            count = AIUsageLog.objects.filter(
                user=request.user,
                feature_type=feature_type,
                created_at__date=today,
                success=True
            ).count()
            
            max_requests = limits.get('feature_limits', {}).get(
                f'{feature_type}_max_requests', 100
            )
            
            feature_usage[feature_type] = {
                'used_today': count,
                'limit': max_requests,
                'remaining': max(0, max_requests - count)
            }
        
        data = {
            'daily_token_limit': limits['daily_token_limit'],
            'monthly_token_limit': limits['monthly_token_limit'],
            'tokens_used_today': tokens_used_today,
            'tokens_used_this_month': tokens_used_this_month,
            'tokens_remaining_today': max(0, limits['daily_token_limit'] - tokens_used_today),
            'tokens_remaining_this_month': max(0, limits['monthly_token_limit'] - tokens_used_this_month),
            'can_make_request': permission.has_permission(request, self),
            'feature_usage': feature_usage,
        }
        
        return create_success_response(data)



class SmartSuggestionsView(APIView):
    """View to get smart suggestions for event planning."""
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'smart_suggestions'
    
    def post(self, request):
        """Handle smart suggestions request."""
        category = request.data.get('category')
        context = request.data.get('context', {})
        
        if not category:
            return create_error_response(
                "category is required",
                'MISSING_INPUT',
                status.HTTP_400_BAD_REQUEST
            )
        
        service = MessageGenerationService()
        
        try:
            suggestions = service.generate_smart_suggestions(
                event_data=context
            )
            
            return create_success_response({
                'category': category,
                'suggestions': suggestions,
                'context_used': context
            })
            
        except Exception as e:
            logger.exception(f"Smart suggestions failed: {e}")
            return create_error_response(
                "Failed to generate suggestions",
                'SUGGESTIONS_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


