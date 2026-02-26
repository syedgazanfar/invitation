"""
Tests for the AI app.

This module contains comprehensive tests for:
- Models (PhotoAnalysis, GeneratedMessage, AIUsageLog)
- Views (API endpoints)
- Services (PhotoAnalysisService, MessageGenerationService, RecommendationService)
- Rate limiting and error handling
- Mock mode functionality
"""

import uuid
import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock
from io import BytesIO

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from .services.photo_analysis import PhotoAnalysisService, ColorInfo, MoodInfo
from .services.message_generator import MessageGenerationService
from .services.recommendation import RecommendationService, color_distance_hex, find_closest_color, hex_to_rgb, rgb_to_hex
from .services.base_ai import BaseAIService, AIServiceError, RateLimitError, retry_on_failure


User = get_user_model()


# =============================================================================
# Model Tests
# =============================================================================

class PhotoAnalysisModelTests(TestCase):
    """Tests for PhotoAnalysis model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_create_photo_analysis(self):
        """Test creating a photo analysis."""
        analysis = PhotoAnalysis.objects.create(
            user=self.user,
            image_url='https://example.com/photo.jpg',
            primary_colors={
                'dominant': {'hex': '#FF0000', 'percentage': 50},
                'colors': [
                    {'hex': '#FF0000', 'percentage': 50},
                    {'hex': '#00FF00', 'percentage': 30},
                    {'hex': '#0000FF', 'percentage': 20}
                ]
            },
            mood={'tags': ['romantic', 'elegant'], 'primary_mood': 'romantic'},
            style_recommendations=[
                {'name': 'Classic Romance', 'match_score': 0.9}
            ]
        )
        
        self.assertIsNotNone(analysis.id)
        self.assertEqual(analysis.user, self.user)
        self.assertEqual(analysis.image_url, 'https://example.com/photo.jpg')
        self.assertIsNotNone(analysis.created_at)
        self.assertIsNotNone(analysis.updated_at)
    
    def test_get_primary_color_hex(self):
        """Test getting dominant color hex."""
        analysis = PhotoAnalysis.objects.create(
            user=self.user,
            image_url='https://example.com/photo.jpg',
            primary_colors={'dominant': {'hex': '#FF5733'}}
        )
        
        self.assertEqual(analysis.get_primary_color_hex(), '#FF5733')
    
    def test_get_mood_tags(self):
        """Test getting mood tags."""
        analysis = PhotoAnalysis.objects.create(
            user=self.user,
            image_url='https://example.com/photo.jpg',
            mood={'tags': ['romantic', 'elegant', 'warm']}
        )
        
        tags = analysis.get_mood_tags()
        self.assertEqual(len(tags), 3)
        self.assertIn('romantic', tags)


class GeneratedMessageModelTests(TestCase):
    """Tests for GeneratedMessage model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_generated_message(self):
        """Test creating a generated message."""
        message = GeneratedMessage.objects.create(
            user=self.user,
            context={
                'bride_name': 'Alice',
                'groom_name': 'Bob',
                'event_date': '2024-06-15'
            },
            generated_options=[
                'Option 1: Join us for our special day!',
                'Option 2: We invite you to celebrate our love!'
            ],
            style_used='romantic',
            tokens_used=500
        )
        
        self.assertIsNotNone(message.id)
        self.assertEqual(message.style_used, 'romantic')
        self.assertEqual(message.tokens_used, 500)
        self.assertEqual(len(message.generated_options), 2)
    
    def test_get_first_option(self):
        """Test getting first generated option."""
        message = GeneratedMessage.objects.create(
            user=self.user,
            context={'bride_name': 'Alice', 'groom_name': 'Bob'},
            generated_options=['First option', 'Second option'],
            style_used='romantic'
        )
        
        self.assertEqual(message.get_first_option(), 'First option')
    
    def test_get_context_summary(self):
        """Test getting context summary."""
        message = GeneratedMessage.objects.create(
            user=self.user,
            context={'bride_name': 'Alice', 'groom_name': 'Bob'},
            generated_options=['Option 1'],
            style_used='romantic'
        )
        
        self.assertEqual(message.get_context_summary(), 'Alice & Bob')


class AIUsageLogModelTests(TestCase):
    """Tests for AIUsageLog model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_create_usage_log(self):
        """Test creating a usage log."""
        log = AIUsageLog.objects.create(
            user=self.user,
            feature_type='photo_analysis',
            request_data={'image_url': 'https://example.com/photo.jpg'},
            response_data={'analysis_id': str(uuid.uuid4())},
            tokens_used=1000,
            success=True
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.feature_type, 'photo_analysis')
        self.assertTrue(log.success)
        self.assertEqual(log.tokens_used, 1000)
    
    def test_get_user_usage_today(self):
        """Test getting today's usage for a user."""
        # Create some logs
        AIUsageLog.objects.create(
            user=self.user,
            feature_type='photo_analysis',
            tokens_used=500,
            success=True
        )
        AIUsageLog.objects.create(
            user=self.user,
            feature_type='message_generation',
            tokens_used=300,
            success=True
        )
        
        usage = AIUsageLog.get_user_usage_today(self.user)
        self.assertEqual(usage['count'], 2)
        self.assertEqual(usage['total_tokens'], 800)


# =============================================================================
# Base AI Service Tests
# =============================================================================

class BaseAIServiceTests(TestCase):
    """Tests for BaseAIService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = BaseAIService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_cache_key(self):
        """Test cache key generation."""
        key1 = self.service._get_cache_key('test', 'arg1', 'arg2')
        key2 = self.service._get_cache_key('test', 'arg1', 'arg2')
        
        # Same inputs should produce same key
        self.assertEqual(key1, key2)
        
        # Different inputs should produce different keys
        key3 = self.service._get_cache_key('test', 'arg1', 'arg3')
        self.assertNotEqual(key1, key3)
    
    def test_sanitize_for_log(self):
        """Test data sanitization for logging."""
        data = {
            'normal_field': 'value',
            'api_key': 'secret123',
            'password': 'mypassword',
            'nested': {
                'token': 'secrettoken',
                'public': 'data'
            }
        }
        
        sanitized = self.service._sanitize_for_log(data)
        
        self.assertEqual(sanitized['normal_field'], 'value')
        self.assertEqual(sanitized['api_key'], '***REDACTED***')
        self.assertEqual(sanitized['password'], '***REDACTED***')
        self.assertEqual(sanitized['nested']['token'], '***REDACTED***')
        self.assertEqual(sanitized['nested']['public'], 'data')
    
    def test_handle_error(self):
        """Test error handling."""
        error = Exception('Test error message')
        handled = self.service.handle_error(error, context='test_context')
        
        self.assertIsInstance(handled, AIServiceError)
        self.assertIn('Test error message', str(handled))
    
    def test_check_rate_limit_new_user(self):
        """Test rate limit check for new user."""
        result = self.service.check_rate_limit(self.user, 'photo_analysis')
        self.assertTrue(result)
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        # Create many logs to exceed limit
        for i in range(101):
            AIUsageLog.objects.create(
                user=self.user,
                feature_type='photo_analysis',
                tokens_used=100,
                success=True
            )
        
        result = self.service.check_rate_limit(self.user, 'photo_analysis')
        self.assertFalse(result)


class RetryOnFailureTests(TestCase):
    """Tests for retry_on_failure decorator."""
    
    def test_retry_success_after_failures(self):
        """Test that function retries and eventually succeeds."""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0.1)
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception('Temporary failure')
            return 'success'
        
        result = flaky_function()
        self.assertEqual(result, 'success')
        self.assertEqual(call_count, 3)
    
    def test_retry_exhausted(self):
        """Test that function raises error after max retries."""
        @retry_on_failure(max_retries=2, delay=0.1)
        def always_fails():
            raise Exception('Always fails')
        
        with self.assertRaises(AIServiceError):
            always_fails()


# =============================================================================
# Photo Analysis Service Tests
# =============================================================================

class PhotoAnalysisServiceTests(TestCase):
    """Tests for PhotoAnalysisService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = PhotoAnalysisService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        rgb = self.service.hex_to_rgb('#A61E2A')
        self.assertEqual(rgb, (166, 30, 42))
        
        # Test short form
        rgb = self.service.hex_to_rgb('#ABC')
        self.assertEqual(rgb, (170, 187, 204))
        
        # Test invalid hex
        rgb = self.service.hex_to_rgb('invalid')
        self.assertIsNone(rgb)
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        hex_color = self.service.rgb_to_hex((166, 30, 42))
        self.assertEqual(hex_color, '#A61E2A')
    
    def test_get_color_name(self):
        """Test getting color name."""
        # Test known color
        name = self.service.get_color_name('#A61E2A')
        self.assertEqual(name, 'Deep Red')
        
        # Test unknown color (should return closest match)
        name = self.service.get_color_name('#A61E2B')
        self.assertIn('Deep Red', name)
    
    def test_get_complementary_colors(self):
        """Test getting complementary colors."""
        colors = self.service.get_complementary_colors('#FF0000')
        self.assertEqual(len(colors), 3)
        # First color should be complementary (cyan for red)
        self.assertEqual(colors[0], '#00FFFF')
    
    def test_mock_extract_colors(self):
        """Test mock color extraction."""
        colors = self.service._mock_extract_colors('test_image.jpg')
        
        self.assertGreater(len(colors), 0)
        for color in colors:
            self.assertIn('color', color)
            self.assertIn('name', color)
            self.assertIn('percentage', color)
    
    def test_mock_detect_mood(self):
        """Test mock mood detection."""
        mood = self.service._mock_detect_mood('test_image.jpg')
        
        self.assertIn('primary', mood)
        self.assertIn('confidence', mood)
        self.assertIn('secondary', mood)
        self.assertIn('attributes', mood)
        self.assertGreater(mood['confidence'], 0)
        self.assertLess(mood['confidence'], 1)
    
    def test_generate_style_recommendations(self):
        """Test style recommendation generation."""
        colors = [
            {'color': '#A61E2A', 'name': 'Deep Red', 'percentage': 35},
            {'color': '#D4AF37', 'name': 'Gold', 'percentage': 25},
        ]
        mood = {
            'primary': 'romantic',
            'confidence': 0.92,
            'secondary': ['elegant'],
            'attributes': {'romantic': 0.92, 'elegant': 0.85}
        }
        
        recommendations = self.service.generate_style_recommendations(
            colors, mood, event_type='WEDDING'
        )
        
        self.assertGreater(len(recommendations), 0)
        for rec in recommendations:
            self.assertIn('style', rec)
            self.assertIn('confidence', rec)
            self.assertIn('description', rec)
            self.assertIn('color_palette', rec)
    
    def test_determine_color_temperature_warm(self):
        """Test warm color temperature detection."""
        hex_colors = ['#FF0000', '#FFA500', '#FFD700']
        temp = self.service._determine_color_temperature(hex_colors)
        self.assertEqual(temp, 'warm')
    
    def test_determine_color_temperature_cool(self):
        """Test cool color temperature detection."""
        hex_colors = ['#0000FF', '#00FFFF', '#4B0082']
        temp = self.service._determine_color_temperature(hex_colors)
        self.assertEqual(temp, 'cool')


# =============================================================================
# Message Generation Service Tests
# =============================================================================

class MessageGenerationServiceTests(TestCase):
    """Tests for MessageGenerationService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = MessageGenerationService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_mock_generate(self):
        """Test mock message generation."""
        context = {
            'bride_name': 'Priya',
            'groom_name': 'Rahul',
            'event_type': 'WEDDING',
            'culture': 'modern',
            'details': 'Childhood sweethearts'
        }
        
        result = self.service._mock_generate(context)
        
        self.assertIn('options', result)
        self.assertEqual(len(result['options']), 3)
        self.assertIn('tokens_used', result)
        self.assertIn('generation_time_ms', result)
        
        for opt in result['options']:
            self.assertIn('style', opt)
            self.assertIn('message', opt)
            self.assertIn('style_name', opt)
            self.assertIn('Priya', opt['message'])
            self.assertIn('Rahul', opt['message'])
    
    def test_mock_generate_indian_culture(self):
        """Test mock generation with Indian cultural context."""
        context = {
            'bride_name': 'Priya',
            'groom_name': 'Rahul',
            'event_type': 'WEDDING',
            'culture': 'north_indian',
        }
        
        result = self.service._mock_generate(context)
        
        # Check for Indian cultural elements in messages
        messages = ' '.join([opt['message'] for opt in result['options']])
        # Should contain culturally relevant terms
        self.assertIn('Priya', messages)
        self.assertIn('Rahul', messages)
    
    def test_generate_hashtags(self):
        """Test hashtag generation."""
        result = self.service.generate_hashtags(
            bride_name='Priya Sharma',
            groom_name='Rahul Verma',
            wedding_date='2024-12-25',
            style='all',
            count=9
        )
        
        self.assertIn('hashtags', result)
        self.assertIn('by_category', result)
        self.assertIn('top_pick', result)
        self.assertEqual(len(result['hashtags']), 9)
        self.assertIn('classic', result['by_category'])
        self.assertIn('fun', result['by_category'])
        self.assertIn('trending', result['by_category'])
    
    def test_generate_smart_suggestions(self):
        """Test smart suggestions generation."""
        event_data = {
            'event_type': 'WEDDING',
            'bride_name': 'Priya',
            'groom_name': 'Rahul',
            'event_date': '2024-12-25',
            'venue_type': 'outdoor',
            'guest_count': 150,
            'culture': 'indian'
        }
        
        suggestions = self.service.generate_smart_suggestions(event_data)
        
        self.assertIn('hashtags', suggestions)
        self.assertIn('music_suggestions', suggestions)
        self.assertIn('optimal_send_time', suggestions)
        self.assertIn('engagement_tips', suggestions)
        self.assertIn('cultural_notes', suggestions)
    
    def test_get_music_suggestions_indian(self):
        """Test Indian music suggestions."""
        suggestions = self.service._get_music_suggestions('WEDDING', 'north_indian', 'indoor')
        
        self.assertGreater(len(suggestions), 0)
        categories = [s['category'] for s in suggestions]
        self.assertIn('Entry', categories)
    
    def test_get_engagement_tips_large_guest_list(self):
        """Test engagement tips for large guest list."""
        tips = self.service._get_engagement_tips(200)
        
        # Should include tips specific to large events
        categories = [tip['category'] for tip in tips]
        self.assertIn('logistics', categories)


# =============================================================================
# Recommendation Service Tests
# =============================================================================

class RecommendationServiceTests(TestCase):
    """Tests for RecommendationService."""
    
    def setUp(self):
        """Set up test data."""
        self.service = RecommendationService()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_color_distance_hex_identical(self):
        """Test color distance for identical colors."""
        distance = color_distance_hex('#FF0000', '#FF0000')
        self.assertEqual(distance, 0)
    
    def test_color_distance_hex_different(self):
        """Test color distance for different colors."""
        distance = color_distance_hex('#FF0000', '#00FF00')
        self.assertGreater(distance, 0)
        self.assertLess(distance, 1)
    
    def test_find_closest_color(self):
        """Test finding closest color."""
        colors = ['#FF0000', '#00FF00', '#0000FF']
        closest, distance = find_closest_color('#FF1111', colors)
        
        self.assertEqual(closest, '#FF0000')
        self.assertGreater(distance, 0)
        self.assertLess(distance, 1)
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        rgb = hex_to_rgb('#A61E2A')
        self.assertEqual(rgb, (166, 30, 42))
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        hex_color = rgb_to_hex((166, 30, 42))
        self.assertEqual(hex_color, '#A61E2A')
    
    def test_recommend_styles(self):
        """Test style recommendations."""
        colors = ['#FFB6C1', '#FFC0CB', '#FF69B4']
        mood = {
            'primary': 'romantic',
            'confidence': 0.92,
            'attributes': {'romantic': 0.92, 'elegant': 0.85}
        }
        
        recommendations = self.service.recommend_styles(
            colors=colors,
            mood=mood,
            event_type='WEDDING'
        )
        
        self.assertGreater(len(recommendations), 0)
        for rec in recommendations:
            self.assertIn('name', rec)
            self.assertIn('confidence', rec)
            self.assertIn('color_palette', rec)
    
    def test_recommend_styles_no_colors(self):
        """Test style recommendations without colors."""
        mood = {
            'primary': 'modern',
            'confidence': 0.85,
            'attributes': {'modern': 0.85, 'minimalist': 0.75}
        }
        
        recommendations = self.service.recommend_styles(
            colors=[],
            mood=mood,
            event_type='WEDDING'
        )
        
        self.assertGreater(len(recommendations), 0)
    
    def test_get_mock_recommendations(self):
        """Test mock template recommendations."""
        result = self.service._get_mock_recommendations('WEDDING', limit=3)
        
        self.assertIn('recommendations', result)
        self.assertIn('personalization_factors', result)
        self.assertLessEqual(len(result['recommendations']), 3)
        
        for rec in result['recommendations']:
            self.assertIn('template_id', rec)
            self.assertIn('name', rec)
            self.assertIn('match_score', rec)
            self.assertIn('match_reasons', rec)


# =============================================================================
# API Endpoint Tests
# =============================================================================

class PhotoAnalysisAPITests(APITestCase):
    """Tests for photo analysis API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_analyze_photo_unauthenticated(self):
        """Test that unauthenticated users cannot analyze photos."""
        self.client.force_authenticate(user=None)
        response = self.client.post('/api/ai/analyze-photo/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_analyze_photo_no_file(self):
        """Test error when no photo is provided."""
        response = self.client.post('/api/ai/analyze-photo/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_get_analysis_result(self):
        """Test getting analysis result by ID."""
        # Create an analysis
        analysis = PhotoAnalysis.objects.create(
            user=self.user,
            image_url='https://example.com/photo.jpg',
            primary_colors={'dominant': {'hex': '#FF0000'}},
            mood={'primary_mood': 'romantic'}
        )
        
        response = self.client.get(f'/api/ai/analysis/{analysis.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], str(analysis.id))


class MessageGenerationAPITests(APITestCase):
    """Tests for message generation API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_generate_message_success(self):
        """Test successful message generation."""
        data = {
            'bride_name': 'Alice',
            'groom_name': 'Bob',
            'event_type': 'WEDDING',
            'tone': 'warm',
        }
        
        response = self.client.post('/api/ai/generate-message/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIn('options', response.data['data'])
    
    def test_generate_message_missing_names(self):
        """Test error when names are missing."""
        data = {
            'event_type': 'WEDDING',
        }
        
        response = self.client.post('/api/ai/generate-message/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_generate_hashtags(self):
        """Test hashtag generation endpoint."""
        response = self.client.get('/api/ai/generate-hashtags/', {
            'bride': 'Alice',
            'groom': 'Bob',
            'count': 6
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('hashtags', response.data['data'])


class AIUsageAPITests(APITestCase):
    """Tests for AI usage API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_usage_stats(self):
        """Test getting usage statistics."""
        # Create usage logs
        AIUsageLog.objects.create(
            user=self.user,
            feature_type='photo_analysis',
            tokens_used=500,
            success=True
        )
        
        response = self.client.get('/api/ai/usage/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats', response.data['data'])
    
    def test_get_usage_limits(self):
        """Test getting usage limits."""
        response = self.client.get('/api/ai/usage/limits/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('limits', response.data['data'])
    
    def test_check_feature_availability(self):
        """Test checking feature availability."""
        response = self.client.get('/api/ai/check-availability/', {
            'feature': 'photo_analysis'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('available', response.data['data'])


class TemplateRecommendationAPITests(APITestCase):
    """Tests for template recommendation API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_template_recommendations(self):
        """Test getting template recommendations."""
        response = self.client.get('/api/ai/template-recommendations/', {
            'event_type': 'WEDDING',
            'plan_code': 'BASIC',
            'limit': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data['data'])
    
    def test_get_style_recommendations(self):
        """Test getting style recommendations."""
        # First create a photo analysis
        analysis = PhotoAnalysis.objects.create(
            user=self.user,
            image_url='https://example.com/photo.jpg',
            primary_colors={'dominant': {'hex': '#FF0000'}},
            mood={'primary_mood': 'romantic'}
        )
        
        response = self.client.post('/api/ai/style-recommendations/', {
            'analysis_id': str(analysis.id),
            'event_type': 'WEDDING'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data['data'])


# =============================================================================
# Rate Limiting Tests
# =============================================================================

class RateLimitingTests(TestCase):
    """Tests for rate limiting functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.service = BaseAIService()
    
    def test_rate_limit_not_exceeded(self):
        """Test that user can make requests when under limit."""
        # Create a few logs
        for i in range(5):
            AIUsageLog.objects.create(
                user=self.user,
                feature_type='photo_analysis',
                tokens_used=100,
                success=True
            )
        
        result = self.service.check_rate_limit(self.user, 'photo_analysis')
        self.assertTrue(result)
    
    def test_rate_limit_exceeded(self):
        """Test that user is blocked when over limit."""
        # Create many logs to exceed hourly limit
        for i in range(101):
            AIUsageLog.objects.create(
                user=self.user,
                feature_type='photo_analysis',
                tokens_used=100,
                success=True
            )
        
        result = self.service.check_rate_limit(self.user, 'photo_analysis')
        self.assertFalse(result)
    
    def test_rate_limit_per_feature(self):
        """Test that rate limits are per-feature."""
        # Exhaust photo_analysis limit
        for i in range(101):
            AIUsageLog.objects.create(
                user=self.user,
                feature_type='photo_analysis',
                tokens_used=100,
                success=True
            )
        
        # Photo analysis should be blocked
        result = self.service.check_rate_limit(self.user, 'photo_analysis')
        self.assertFalse(result)


# =============================================================================
# Error Handling Tests
# =============================================================================

class ErrorHandlingTests(TestCase):
    """Tests for error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.service = BaseAIService()
    
    def test_aiservice_error_creation(self):
        """Test AIServiceError creation."""
        error = AIServiceError('Test error', error_code='TEST_ERROR')
        
        self.assertEqual(str(error), 'Test error')
        self.assertEqual(error.error_code, 'TEST_ERROR')
    
    def test_aiservice_error_with_details(self):
        """Test AIServiceError with details."""
        error = AIServiceError(
            'Test error',
            error_code='TEST_ERROR',
            details={'field': 'value'}
        )
        
        self.assertEqual(error.details['field'], 'value')


# =============================================================================
# Mock Mode Tests
# =============================================================================

class MockModeTests(TestCase):
    """Tests for mock mode functionality."""
    
    @override_settings(AI_MOCK_MODE=True)
    def test_photo_analysis_mock_mode(self):
        """Test photo analysis in mock mode."""
        service = PhotoAnalysisService()
        
        self.assertTrue(service.mock_mode)
        
        result = service.analyze('test_image.jpg', event_type='WEDDING')
        
        self.assertIn('colors', result)
        self.assertIn('mood', result)
        self.assertIn('recommendations', result)
    
    @override_settings(AI_MOCK_MODE=True)
    def test_message_generation_mock_mode(self):
        """Test message generation in mock mode."""
        service = MessageGenerationService()
        
        self.assertTrue(service.mock_mode)
        
        context = {
            'bride_name': 'Alice',
            'groom_name': 'Bob',
            'event_type': 'WEDDING',
        }
        
        result = service.generate_messages(context=context)
        
        self.assertEqual(len(result.generated_options), 3)


# =============================================================================
# Integration Tests
# =============================================================================

class AIIntegrationTests(TestCase):
    """Integration tests for AI features."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.photo_service = PhotoAnalysisService()
        self.message_service = MessageGenerationService()
        self.recommendation_service = RecommendationService()
    
    def test_end_to_end_photo_to_message(self):
        """Test complete flow from photo analysis to message generation."""
        # Step 1: Analyze photo
        photo_result = self.photo_service.analyze('test.jpg', event_type='WEDDING')
        
        self.assertIn('colors', photo_result)
        self.assertIn('mood', photo_result)
        
        # Step 2: Get style recommendations based on photo
        style_recs = self.recommendation_service.recommend_styles(
            colors=[c['color'] for c in photo_result['colors'][:3]],
            mood=photo_result['mood'],
            event_type='WEDDING'
        )
        
        self.assertGreater(len(style_recs), 0)
        
        # Step 3: Generate message based on the style
        context = {
            'bride_name': 'Alice',
            'groom_name': 'Bob',
            'event_type': 'WEDDING',
            'style': style_recs[0]['style_key'],
        }
        
        message = self.message_service.generate_messages(context=context)
        
        self.assertEqual(len(message.generated_options), 3)
    
    def test_photo_analysis_caching(self):
        """Test that photo analysis results are cached."""
        # First call
        result1 = self.photo_service.analyze('same_image.jpg', event_type='WEDDING')
        
        # Second call (should use cache)
        result2 = self.photo_service.analyze('same_image.jpg', event_type='WEDDING')
        
        # Results should be identical (from cache)
        self.assertEqual(result1['colors'], result2['colors'])
        self.assertEqual(result1['mood'], result2['mood'])
