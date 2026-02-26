"""
Message and hashtag generation views.

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

class MoodDetectionView(APIView):
    """POST /api/v1/ai/detect-mood/ - Detect mood from photo.
    
    Simple endpoint just for mood detection.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    parser_classes = [MultiPartParser, FormParser]
    feature_type = 'mood_detection'
    
    def post(self, request):
        """Handle mood detection request.
        
        Args:
            request: HTTP request with photo file or image_url.
            
        Returns:
            Response with detected mood.
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
                filename = f"ai_mood/{request.user.id}/{uuid.uuid4()}.{ext}"
                filepath = default_storage.save(filename, ContentFile(photo.read()))
                image_url = default_storage.url(filepath)
            
            mood = service.detect_mood(image_url)
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                feature_type=self.feature_type,
                request_data={'image_url': image_url},
                response_data={'primary_mood': mood.get('primary')},
                tokens_used=25,
                success=True
            )
            
            rate_limit_remaining = self._get_rate_limit_remaining(request.user)
            response = create_success_response(mood)
            return add_rate_limit_headers(response, 100, rate_limit_remaining)
            
        except AIServiceError as e:
            logger.error(f"Mood detection failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Unexpected error during mood detection: {e}")
            return create_error_response(
                "Mood detection failed",
                'DETECTION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_rate_limit_remaining(self, user: AbstractUser) -> int:
        """Get remaining rate limit for user."""
        service = PhotoAnalysisService()
        return service.get_rate_limit_remaining(user, self.feature_type)



class GenerateMessagesView(APIView):
    """POST /api/v1/ai/generate-messages/ - Generate invitation messages.
    
    JSON body with context (bride_name, groom_name, event_type, style, etc.)
    Returns 3 message options in different styles.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'message_generation'
    
    def post(self, request):
        """Handle message generation request.
        
        Args:
            request: HTTP request with generation context.
            
        Returns:
            Response with generated messages.
        """
        start_time = time.time()
        
        serializer = MessageGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                'VALIDATION_ERROR',
                status.HTTP_400_BAD_REQUEST,
                serializer.errors
            )
        
        data = serializer.validated_data
        
        # Build context for generation
        context = {
            'bride_name': data['bride_name'],
            'groom_name': data['groom_name'],
            'event_date': data.get('event_date', ''),
            'venue': data.get('venue', ''),
            'details': data.get('details', ''),
            'culture': data.get('culture', 'modern'),
        }
        
        try:
            service = MessageGenerationService()
            
            # Generate messages
            result = service.generate_messages(
                context=context,
                style=data['style'],
                num_options=3,
                user=request.user,
                event=None  # Can be linked to order if order_id provided
            )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Format response options
            options = []
            for opt in result.generated_options:
                options.append({
                    'id': opt.get('id', str(uuid.uuid4())),
                    'text': opt.get('text', ''),
                    'style': opt.get('style', data['style']),
                    'tone': opt.get('tone', data.get('tone', 'warm'))
                })
            
            response_data = {
                'options': options,
                'message_id': str(result.id) if hasattr(result, 'id') and result.id else None,
                'tokens_used': result.tokens_used,
                'generation_time_ms': processing_time_ms
            }
            
            rate_limit_remaining = self._get_rate_limit_remaining(request.user)
            response = create_success_response(
                response_data,
                status_code=status.HTTP_201_CREATED
            )
            return add_rate_limit_headers(response, 30, rate_limit_remaining)
            
        except RateLimitError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_429_TOO_MANY_REQUESTS,
                {'retry_after': e.retry_after} if e.retry_after else None
            )
        except ValidationError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_400_BAD_REQUEST,
                e.details
            )
        except AIServiceError as e:
            logger.error(f"Message generation failed: {e}")
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.details
            )
        except Exception as e:
            logger.exception(f"Unexpected error during message generation: {e}")
            return create_error_response(
                "Message generation failed",
                'GENERATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_rate_limit_remaining(self, user: AbstractUser) -> int:
        """Get remaining rate limit for user."""
        service = MessageGenerationService()
        return service.get_rate_limit_remaining(user, self.feature_type)



class GenerateHashtagsView(APIView):
    """POST /api/v1/ai/generate-hashtags/ - Generate wedding hashtags.
    
    Returns personalized hashtags based on couple names.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'hashtag_generation'
    
    def post(self, request):
        """Handle hashtag generation request.
        
        Args:
            request: HTTP request with bride/groom names.
            
        Returns:
            Response with generated hashtags.
        """
        from .serializers import HashtagGenerationSerializer
        
        serializer = HashtagGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                'VALIDATION_ERROR',
                status.HTTP_400_BAD_REQUEST,
                serializer.errors
            )
        
        data = serializer.validated_data
        bride_name = data['bride_name']
        groom_name = data['groom_name']
        style = data.get('style', 'romantic')
        count = data.get('count', 10)
        
        try:
            service = MessageGenerationService()
            result = service.generate_hashtags(
                bride_name=bride_name,
                groom_name=groom_name,
                style=style,
                count=count
            )
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                feature_type=self.feature_type,
                request_data={
                    'bride_name': bride_name,
                    'groom_name': groom_name,
                    'style': style
                },
                response_data={'hashtags_count': len(result.get('hashtags', []))},
                tokens_used=5,
                success=True
            )
            
            return create_success_response(result)
            
        except Exception as e:
            logger.exception(f"Hashtag generation failed: {e}")
            return create_error_response(
                "Hashtag generation failed",
                'GENERATION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class AnalyzePhotoView(APIView):
    """Legacy view to analyze a photo using URL.
    
    Use PhotoAnalysisView for new implementations with file upload.
    """
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'photo_analysis'
    
    def post(self, request):
        """Handle photo analysis request."""
        serializer = PhotoAnalysisCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return create_error_response(
                "Validation failed",
                'VALIDATION_ERROR',
                status.HTTP_400_BAD_REQUEST,
                serializer.errors
            )
        
        data = serializer.validated_data
        service = PhotoAnalysisService()
        
        # Get order if provided
        order = None
        if data.get('event_id'):
            from apps.invitations.models import Order
            order = get_object_or_404(Order, id=data['event_id'], user=request.user)
        
        try:
            result = service.analyze_photo(
                image_url=data['image_url'],
                user=request.user,
                order=order,
                extract_colors=data.get('extract_colors', True),
                detect_mood=data.get('detect_mood', True),
                generate_recommendations=data.get('generate_recommendations', True)
            )
            
            response_serializer = PhotoAnalysisSerializer(result)
            return create_success_response(
                response_serializer.data,
                status_code=status.HTTP_201_CREATED
            )
            
        except AIServiceError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                e.details
            )
        except Exception as e:
            logger.exception(f"Photo analysis failed: {e}")
            return create_error_response(
                "Photo analysis failed",
                'ANALYSIS_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class ExtractColorsView(APIView):
    """Legacy view to extract colors from a photo URL."""
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'color_extraction'
    
    def post(self, request):
        """Handle color extraction request."""
        image_url = request.data.get('image_url')
        if not image_url:
            return create_error_response(
                "image_url is required",
                'MISSING_INPUT',
                status.HTTP_400_BAD_REQUEST
            )
        
        service = PhotoAnalysisService()
        
        try:
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
            
            return create_success_response(colors)
            
        except AIServiceError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Color extraction failed: {e}")
            return create_error_response(
                "Color extraction failed",
                'EXTRACTION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class DetectMoodView(APIView):
    """Legacy view to detect mood from a photo URL."""
    
    permission_classes = [IsAuthenticated, CanUseAIFeature]
    feature_type = 'mood_detection'
    
    def post(self, request):
        """Handle mood detection request."""
        image_url = request.data.get('image_url')
        if not image_url:
            return create_error_response(
                "image_url is required",
                'MISSING_INPUT',
                status.HTTP_400_BAD_REQUEST
            )
        
        service = PhotoAnalysisService()
        
        try:
            mood = service.detect_mood(image_url)
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                feature_type=self.feature_type,
                request_data={'image_url': image_url},
                response_data={'primary_mood': mood.get('primary')},
                tokens_used=25,
                success=True
            )
            
            return create_success_response(mood)
            
        except AIServiceError as e:
            return create_error_response(
                e.message,
                e.error_code,
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.exception(f"Mood detection failed: {e}")
            return create_error_response(
                "Mood detection failed",
                'DETECTION_ERROR',
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )



class MessageStylesView(APIView):
    """View to get available message styles."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return available message styles."""
        styles = [
            {'code': 'romantic', 'name': 'Romantic', 'description': 'Soft, loving, and emotional tone'},
            {'code': 'formal', 'name': 'Formal', 'description': 'Professional and elegant tone'},
            {'code': 'casual', 'name': 'Casual', 'description': 'Relaxed and friendly tone'},
            {'code': 'funny', 'name': 'Funny', 'description': 'Humorous and light-hearted tone'},
            {'code': 'poetic', 'name': 'Poetic', 'description': 'Artistic and lyrical tone'},
            {'code': 'traditional', 'name': 'Traditional', 'description': 'Classic and timeless tone'},
            {'code': 'modern', 'name': 'Modern', 'description': 'Contemporary and trendy tone'},
        ]
        return create_success_response({'styles': styles})


