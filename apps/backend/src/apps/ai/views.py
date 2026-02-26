"""
Views for the AI app.

This module provides API endpoints for AI-powered features:
- Photo analysis (color extraction, mood detection)
- Message generation
- Template recommendations
- Style recommendations
- Usage tracking

All views return responses in a consistent format:
{
    "success": bool,
    "data": {...},  # Present when success=True
    "error": {...},  # Present when success=False
    "meta": {...}  # Optional metadata (pagination, rate limits, etc.)
}

Example:
    >>> response = {
    ...     "success": True,
    ...     "data": {"colors": [...]},
    ...     "meta": {"rate_limit_remaining": 95}
    ... }
"""

import time
import uuid
import logging
from typing import Dict, Any, Optional, List, Tuple

from rest_framework import viewsets, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from .serializers import (
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
from .permissions import CanUseAIFeature, IsOwnerOrReadOnly
from .services import PhotoAnalysisService, MessageGenerationService, RecommendationService
from .services.base_ai import AIServiceError, RateLimitError, ValidationError


# =============================================================================
# Constants
# =============================================================================

# File upload limits
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_IMAGE_TYPES = frozenset([
    'image/jpeg', 'image/png', 'image/webp', 'image/jpg'
])

# Rate limiting headers
RATE_LIMIT_HEADER = 'X-RateLimit-Limit'
RATE_LIMIT_REMAINING_HEADER = 'X-RateLimit-Remaining'
RATE_LIMIT_RESET_HEADER = 'X-RateLimit-Reset'

# Logger
logger = logging.getLogger(__name__)


# =============================================================================
# Response Helpers
# =============================================================================

def create_success_response(
    data: Any,
    status_code: int = status.HTTP_200_OK,
    meta: Optional[Dict[str, Any]] = None
) -> Response:
    """Create a standardized success response.
    
    Args:
        data: Response data payload.
        status_code: HTTP status code.
        meta: Optional metadata (pagination, rate limits, etc.).
        
    Returns:
        DRF Response object.
    """
    response_data: Dict[str, Any] = {
        'success': True,
        'data': data
    }
    
    if meta:
        response_data['meta'] = meta
    
    return Response(response_data, status=status_code)


def create_error_response(
    message: str,
    error_code: str = 'ERROR',
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: Optional[Dict[str, Any]] = None
) -> Response:
    """Create a standardized error response.
    
    Args:
        message: Human-readable error message.
        error_code: Machine-readable error code.
        status_code: HTTP status code.
        details: Additional error details.
        
    Returns:
        DRF Response object.
    """
    response_data: Dict[str, Any] = {
        'success': False,
        'error': {
            'code': error_code,
            'message': message
        }
    }
    
    if details:
        response_data['error']['details'] = details
    
    return Response(response_data, status=status_code)


def add_rate_limit_headers(
    response: Response,
    limit: int,
    remaining: int,
    reset_seconds: int = 3600
) -> Response:
    """Add rate limit headers to response.
    
    Args:
        response: DRF Response object.
        limit: Rate limit cap.
        remaining: Remaining requests.
        reset_seconds: Seconds until limit resets.
        
    Returns:
        Modified Response object.
    """
    response[RATE_LIMIT_HEADER] = limit
    response[RATE_LIMIT_REMAINING_HEADER] = remaining
    response[RATE_LIMIT_RESET_HEADER] = reset_seconds
    return response


# =============================================================================
# ViewSets for CRUD Operations
# =============================================================================

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


# =============================================================================
# Photo Analysis API Views
# =============================================================================

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


# =============================================================================
# Recommendation API Views
# =============================================================================

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


# =============================================================================
# Message Generation API Views
# =============================================================================

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


# =============================================================================
# Hashtag Generation API Views
# =============================================================================

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


# =============================================================================
# Legacy Views (for backwards compatibility)
# =============================================================================

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


# =============================================================================
# Usage and Limits API Views
# =============================================================================

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


# Legacy aliases for backwards compatibility
AIUsageView = AIUsageStatsView
AILimitsView = AIUsageLimitsView


# =============================================================================
# Smart Suggestions API Views
# =============================================================================

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
