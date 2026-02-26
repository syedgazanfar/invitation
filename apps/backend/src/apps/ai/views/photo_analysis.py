"""
Photo analysis and color extraction views.

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

class PhotoAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for PhotoAnalysis model.
    
    Provides CRUD operations for photo analyses.
    
    Endpoints:
        GET /api/v1/ai/photo-analyses/ - List user's photo analyses
        POST /api/v1/ai/photo-analyses/ - Create new photo analysis
        GET /api/v1/ai/photo-analyses/{id}/ - Retrieve specific analysis
        PUT /api/v1/ai/photo-analyses/{id}/ - Update analysis
        DELETE /api/v1/ai/photo-analyses/{id}/ - Delete analysis
        POST /api/v1/ai/photo-analyses/{id}/reanalyze/ - Reanalyze photo
    """
    
    serializer_class = PhotoAnalysisSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Return photo analyses for the current user."""
        return PhotoAnalysis.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def reanalyze(self, request, pk=None):
        """Reanalyze a photo.
        
        Args:
            request: HTTP request.
            pk: PhotoAnalysis ID.
            
        Returns:
            Response with reanalyzed data.
        """
        photo_analysis = self.get_object()
        service = PhotoAnalysisService()
        
        try:
            result = service.analyze_photo(
                image_url=photo_analysis.image_url,
                user=request.user,
                event=photo_analysis.event
            )
            serializer = self.get_serializer(result)
            return create_success_response(
                serializer.data,
                status_code=status.HTTP_200_OK
            )
        except AIServiceError as e:
            logger.error(f"Reanalysis failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.details
            )
        except Exception as e:
            logger.exception(f"Unexpected error during reanalysis: {e}")
            return create_error_response(
                "An unexpected error occurred",
                'INTERNAL_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class GeneratedMessageViewSet(viewsets.ModelViewSet):
    """ViewSet for GeneratedMessage model.
    
    Provides CRUD operations for generated messages.
    
    Endpoints:
        GET /api/v1/ai/generated-messages/ - List user's generated messages
        POST /api/v1/ai/generated-messages/ - Create new message
        GET /api/v1/ai/generated-messages/{id}/ - Retrieve specific message
        PUT /api/v1/ai/generated-messages/{id}/ - Update message
        DELETE /api/v1/ai/generated-messages/{id}/ - Delete message
        POST /api/v1/ai/generated-messages/{id}/regenerate/ - Regenerate messages
    """
    
    serializer_class = GeneratedMessageSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Return generated messages for the current user."""
        return GeneratedMessage.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def regenerate(self, request, pk=None):
        """Regenerate messages with the same context.
        
        Args:
            request: HTTP request.
            pk: GeneratedMessage ID.
            
        Returns:
            Response with regenerated messages.
        """
        generated_message = self.get_object()
        service = MessageGenerationService()
        
        try:
            result = service.generate_messages(
                context=generated_message.context,
                style=generated_message.style_used,
                user=request.user,
                event=generated_message.event
            )
            serializer = self.get_serializer(result)
            return create_success_response(
                serializer.data,
                status_code=status.HTTP_201_CREATED
            )
        except RateLimitError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
                {'retry_after': e.retry_after} if e.retry_after else None
            )
        except AIServiceError as e:
            logger.error(f"Regeneration failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.details
            )
        except Exception as e:
            logger.exception(f"Unexpected error during regeneration: {e}")
            return create_error_response(
                "An unexpected error occurred",
                'INTERNAL_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class PhotoAnalysisView(APIView):
    """POST /api/v1/ai/analyze-photo/ - Analyze uploaded photo.
    
    Handles multipart form data with photo upload.
    Supports event_type parameter (WEDDING, BIRTHDAY, etc.)
    Returns analysis results with colors, mood, recommendations.
    Logs usage to AIUsageLog.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    feature_type = 'photo_analysis'
    
    def post(self, request):
        """Handle photo analysis request with file upload.
        
        Args:
            request: HTTP request with uploaded file.
            
        Returns:
            Response with analysis results.
        """
        start_time = time.time()
        
        # Validate input
        serializer = PhotoUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                'VALIDATION_ERROR',
                status.HTTP_400_BAD_REQUEST,
                serializer.errors
            )
        
        data = serializer.validated_data
        photo = data['photo']
        event_type = data.get('event_type', 'WEDDING')
        order_id = data.get('event_id')
        
        # Validate file size
        if photo.size > MAX_FILE_SIZE_BYTES:
            return create_error_response(
                f"File size exceeds {MAX_FILE_SIZE_MB}MB limit",
                'FILE_TOO_LARGE',
                status.HTTP_400_BAD_REQUEST,
                {'max_size_mb': MAX_FILE_SIZE_MB, 'actual_size_mb': round(photo.size / 1024 / 1024, 2)}
            )
        
        # Validate file type
        if photo.content_type not in ALLOWED_IMAGE_TYPES:
            return create_error_response(
                f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}",
                'INVALID_FILE_TYPE',
                status.HTTP_400_BAD_REQUEST,
                {'allowed_types': list(ALLOWED_IMAGE_TYPES)}
            )
        
        try:
            # Save uploaded file
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            
            # Generate unique filename
            ext = photo.name.split('.')[-1].lower()
            filename = f"ai_analysis/{request.user.id}/{uuid.uuid4()}.{ext}"
            filepath = default_storage.save(filename, ContentFile(photo.read()))
            image_url = default_storage.url(filepath)
            
            # Get order if provided
            order = None
            if order_id:
                try:
                    from apps.invitations.models import Order
                    order = Order.objects.get(id=order_id, user=request.user)
                except Order.DoesNotExist:
                    return create_error_response(
                        "Order not found",
                        'ORDER_NOT_FOUND',
                        status.HTTP_404_NOT_FOUND
                    )
            
            # Analyze photo
            service = PhotoAnalysisService()
            result = service.analyze_photo(
                image_url=image_url,
                user=request.user,
                order=order,
                extract_colors=True,
                detect_mood=True,
                generate_recommendations=True
            )
            
            # Build response
            response_data = {
                'analysis_id': str(result.id),
                'primary_colors': result.primary_colors,
                'mood': result.mood,
                'style_recommendations': result.style_recommendations,
                'ai_suggestions': {
                    'event_type': event_type,
                    'suggested_templates': self._get_suggested_templates(result),
                    'suggested_styles': self._get_suggested_styles(result)
                }
            }
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Add rate limit info
            rate_limit_remaining = self._get_rate_limit_remaining(request.user)
            
            response = create_success_response(
                response_data,
                status_code=status.HTTP_201_CREATED,
                meta={'processing_time_ms': processing_time_ms}
            )
            
            return add_rate_limit_headers(
                response,
                limit=100,  # From CanUseAIFeature
                remaining=rate_limit_remaining
            )
            
        except AIServiceError as e:
            logger.error(f"Photo analysis failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.details
            )
        except Exception as e:
            logger.exception(f"Unexpected error during photo analysis: {e}")
            return create_error_response(
                "An unexpected error occurred during analysis",
                'INTERNAL_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_suggested_templates(self, analysis: PhotoAnalysis) -> Dict[str, Any]:
        """Get suggested templates based on analysis.
        
        Args:
            analysis: PhotoAnalysis instance.
            
        Returns:
            Dictionary with suggestion categories.
        """
        mood_tags = analysis.get_mood_tags()
        colors = analysis.primary_colors.get('palette', [])
        
        return {
            'based_on_mood': mood_tags[:3] if mood_tags else ['romantic', 'elegant'],
            'based_on_colors': [c.get('name', 'Unknown') for c in colors[:3]] if colors else [],
            'recommended_categories': self._get_categories_from_mood(mood_tags)
        }
    
    def _get_suggested_styles(self, analysis: PhotoAnalysis) -> List[str]:
        """Get suggested styles based on analysis.
        
        Args:
            analysis: PhotoAnalysis instance.
            
        Returns:
            List of style suggestions.
        """
        mood = analysis.mood or {}
        primary_mood = mood.get('primary_mood', 'romantic')
        
        style_suggestions = {
            'romantic': ['Floral', 'Soft Lighting', 'Pastel Colors'],
            'elegant': ['Classic', 'Gold Accents', 'Symmetrical Layout'],
            'modern': ['Minimalist', 'Bold Typography', 'Geometric Shapes'],
            'vibrant': ['Colorful', 'Energetic', 'Playful Elements']
        }
        
        return style_suggestions.get(primary_mood, style_suggestions['romantic'])
    
    def _get_categories_from_mood(self, mood_tags: List[str]) -> List[str]:
        """Get template categories from mood tags.
        
        Args:
            mood_tags: List of mood tags.
            
        Returns:
            List of category codes.
        """
        category_map = {
            'romantic': 'classic',
            'elegant': 'luxury',
            'modern': 'modern',
            'vibrant': 'colorful',
            'traditional': 'cultural',
            'casual': 'simple'
        }
        
        categories = []
        for tag in mood_tags:
            if tag in category_map:
                categories.append(category_map[tag])
        
        return categories if categories else ['classic', 'modern']
    
    def _get_rate_limit_remaining(self, user: AbstractUser) -> int:
        """Get remaining rate limit for user.
        
        Args:
            user: Current user.
            
        Returns:
            Number of remaining requests.
        """
        service = PhotoAnalysisService()
        return service.get_rate_limit_remaining(user, self.feature_type)



class ColorExtractionView(APIView):
    """POST /api/v1/ai/extract-colors/ - Extract colors from photo.
    
    Simple endpoint just for color extraction.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    parser_classes = [MultiPartParser, FormParser]
    feature_type = 'color_extraction'
    
    def post(self, request):
        """Handle color extraction request.
        
        Args:
            request: HTTP request with photo file or image_url.
            
        Returns:
            Response with extracted colors.
        """
        photo = request.FILES.get('photo')
        image_url = request.data.get('image_url')
        
        if not photo and not image_url:
            return create_error_response(
                "Either photo file or image_url is required",
                'MISSING_INPUT',
                status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = PhotoAnalysisService()
            
            if photo:
                # Validate file size
                if photo.size > MAX_FILE_SIZE_BYTES:
                    return create_error_response(
                        f"File size exceeds {MAX_FILE_SIZE_MB}MB limit",
                        'FILE_TOO_LARGE',
                        status.HTTP_400_BAD_REQUEST
                    )
                
                # Save and get URL
                from django.core.files.storage import default_storage
                from django.core.files.base import ContentFile
                
                ext = photo.name.split('.')[-1].lower()
                filename = f"ai_colors/{request.user.id}/{uuid.uuid4()}.{ext}"
                filepath = default_storage.save(filename, ContentFile(photo.read()))
                image_url = default_storage.url(filepath)
            
            colors = service.extract_colors(image_url)
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                feature_type=self.feature_type,
                request_data={'image_url': image_url},
                response_data={'colors_count': len(colors.get('palette', []))},
                tokens_used=25,
                success=True
            )
            
            rate_limit_remaining = self._get_rate_limit_remaining(request.user)
            response = create_success_response(colors)
            return add_rate_limit_headers(response, 100, rate_limit_remaining)
            
        except AIServiceError as e:
            logger.error(f"Color extraction failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Unexpected error during color extraction: {e}")
            return create_error_response(
                "Color extraction failed",
                'EXTRACTION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_rate_limit_remaining(self, user: AbstractUser) -> int:
        """Get remaining rate limit for user."""
        service = PhotoAnalysisService()
        return service.get_rate_limit_remaining(user, self.feature_type)


