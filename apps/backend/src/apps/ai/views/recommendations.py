"""
Template and style recommendation views.

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

class StyleRecommendationsView(APIView):
    """GET /api/v1/ai/style-recommendations/ - Get style recommendations.
    
    Query params: colors[], mood, event_type
    Returns style recommendations without needing photo upload.
    """
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get style recommendations based on query parameters.
        
        Args:
            request: HTTP request with query params.
            
        Returns:
            Response with style recommendations.
        """
        colors = request.query_params.getlist('colors[]')
        mood = request.query_params.get('mood', 'romantic')
        event_type = request.query_params.get('event_type', 'WEDDING')
        
        # Generate recommendations based on inputs
        service = RecommendationService()
        
        try:
            style_recommendations = service.recommend_styles(
                colors=colors,
                mood={'primary': mood, 'confidence': 0.8},
                event_type=event_type
            )
            
            return create_success_response({
                'recommendations': style_recommendations,
                'based_on': {
                    'colors': colors,
                    'mood': mood,
                    'event_type': event_type
                }
            })
            
        except Exception as e:
            logger.exception(f"Style recommendations failed: {e}")
            return create_error_response(
                "Failed to generate style recommendations",
                'RECOMMENDATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class TemplateRecommendationsView(APIView):
    """GET /api/v1/ai/recommend-templates/ - Get template recommendations.
    
    Query params: event_type, style, colors[], page, page_size
    Queries templates from database and ranks by match score.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'template_recommendation'
    
    def get(self, request):
        """Get template recommendations based on query parameters.
        
        Args:
            request: HTTP request with query params.
            
        Returns:
            Response with template recommendations.
        """
        event_type = request.query_params.get('event_type', 'WEDDING')
        style = request.query_params.get('style', 'romantic')
        colors = request.query_params.getlist('colors[]')
        
        # Pagination
        try:
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 10)), MAX_PAGE_SIZE)
        except ValueError:
            return create_error_response(
                "Invalid pagination parameters",
                'INVALID_PAGINATION',
                status.HTTP_400_BAD_REQUEST
            )
        
        # Get user's plan
        user_plan = self._get_user_plan(request.user)
        
        # Build photo analysis from params
        photo_analysis = None
        if colors:
            photo_analysis = {
                'colors': [{'color': c} for c in colors],
                'mood': {'primary': style, 'confidence': 0.8}
            }
        
        service = RecommendationService()
        
        try:
            result = service.recommend_templates(
                user_data={'plan': user_plan or 'BASIC', 'user_id': str(request.user.id)},
                photo_analysis=photo_analysis,
                event_type=event_type,
                limit=page_size,
                page=page,
                page_size=page_size
            )
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                feature_type=self.feature_type,
                request_data={
                    'event_type': event_type,
                    'style': style,
                    'colors': colors
                },
                response_data={'recommendations_count': len(result.get('recommendations', []))},
                tokens_used=10,
                success=True
            )
            
            return create_success_response(
                result,
                meta={'filters_applied': {
                    'event_type': event_type,
                    'style': style,
                    'colors': colors,
                    'user_plan': user_plan
                }}
            )
            
        except Exception as e:
            logger.exception(f"Template recommendations failed: {e}")
            return create_error_response(
                "Failed to generate template recommendations",
                'RECOMMENDATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_plan(self, user: AbstractUser) -> Optional[str]:
        """Get user's current plan code.
        
        Args:
            user: Current user.
            
        Returns:
            Plan code or None.
        """
        try:
            from apps.invitations.models import Order
            order = Order.objects.filter(
                user=user,
                status='APPROVED'
            ).select_related('plan').first()
            if order and order.plan:
                return order.plan.code
        except Exception:
            pass
        return None



class RecommendTemplatesView(APIView):
    """Legacy view for template recommendations with POST method."""
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'template_recommendation'
    
    def post(self, request):
        """Handle template recommendation request."""
        event_id = request.data.get('event_id')
        photo_analysis_id = request.data.get('photo_analysis_id')
        preferences = request.data.get('preferences', {})
        
        service = RecommendationService()
        
        try:
            # Get order if provided
            order = None
            if event_id:
                from apps.invitations.models import Order
                order = get_object_or_404(Order, id=event_id, user=request.user)
            
            # Get photo analysis if provided
            photo_analysis = None
            if photo_analysis_id:
                photo_analysis = get_object_or_404(
                    PhotoAnalysis,
                    id=photo_analysis_id,
                    user=request.user
                )
            
            # Get user plan
            user_plan = self._get_user_plan(request.user)
            
            recommendations = service.recommend_templates(
                user_data={'plan': user_plan or 'BASIC', 'user_id': str(request.user.id)},
                photo_analysis={'colors': photo_analysis.primary_colors.get('colors', [])} if photo_analysis else None,
                event_type=preferences.get('event_type', 'WEDDING'),
                limit=preferences.get('limit', 5)
            )
            
            return create_success_response({'recommendations': recommendations.get('recommendations', [])})
            
        except Exception as e:
            logger.exception(f"Template recommendation failed: {e}")
            return create_error_response(
                "Template recommendation failed",
                'RECOMMENDATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_user_plan(self, user: AbstractUser) -> Optional[str]:
        """Get user's current plan code."""
        try:
            from apps.invitations.models import Order
            order = Order.objects.filter(
                user=user,
                status='APPROVED'
            ).select_related('plan').first()
            if order and order.plan:
                return order.plan.code
        except Exception:
            pass
        return None



class RecommendStylesView(APIView):
    """View to get style recommendations based on photo analysis."""
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'template_recommendation'
    
    def post(self, request):
        """Handle style recommendation request."""
        photo_analysis_id = request.data.get('photo_analysis_id')
        
        if not photo_analysis_id:
            return create_error_response(
                "photo_analysis_id is required",
                'MISSING_INPUT',
                status.HTTP_400_BAD_REQUEST
            )
        
        photo_analysis = get_object_or_404(
            PhotoAnalysis,
            id=photo_analysis_id,
            user=request.user
        )
        
        service = RecommendationService()
        
        try:
            recommendations = service.recommend_styles(
                colors=[c.get('color') for c in photo_analysis.primary_colors.get('colors', [])],
                mood=photo_analysis.mood
            )
            return create_success_response({'recommendations': recommendations})
            
        except Exception as e:
            logger.exception(f"Style recommendations failed: {e}")
            return create_error_response(
                "Style recommendation failed",
                'RECOMMENDATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


