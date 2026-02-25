#!/usr/bin/env python3
"""
AI Features Test Command

Django management command to test all AI services and features.
Useful for development, debugging, and CI/CD testing.

Usage:
    python manage.py test_ai
    python manage.py test_ai --photo /path/to/image.jpg
    python manage.py test_ai --service photo_analysis
    python manage.py test_ai --verbose
"""

import os
import sys
import time
import argparse
from typing import Dict, List, Optional, Any
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.ai.services.photo_analysis import PhotoAnalysisService
from apps.ai.services.message_generator import MessageGenerationService
from apps.ai.services.recommendation import RecommendationService
from apps.ai.models import PhotoAnalysis, GeneratedMessage
from apps.accounts.models import User


class Command(BaseCommand):
    """Test command for AI features."""
    
    help = 'Test AI services and features'
    
    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--photo',
            type=str,
            help='Path to a photo file for testing photo analysis'
        )
        parser.add_argument(
            '--service',
            type=str,
            choices=['photo_analysis', 'message_generation', 'recommendations', 'all'],
            default='all',
            help='Specific service to test (default: all)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--mock-mode',
            action='store_true',
            help='Force mock mode for testing'
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.mock_mode = options['mock_mode'] or getattr(settings, 'AI_MOCK_MODE', False)
        
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('AI FEATURES TEST SUITE'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write('')
        
        # Display configuration
        self.print_config()
        
        # Run tests based on service selection
        service = options['service']
        photo_path = options['photo']
        
        results = []
        
        if service in ['photo_analysis', 'all']:
            results.append(self.test_photo_analysis(photo_path))
        
        if service in ['message_generation', 'all']:
            results.append(self.test_message_generation())
        
        if service in ['recommendations', 'all']:
            results.append(self.test_recommendations())
        
        # Print summary
        self.print_summary(results)

    def print_config(self):
        """Print current AI configuration."""
        self.stdout.write(self.style.HTTP_INFO('Configuration:'))
        self.stdout.write(f"  Mock Mode: {'Yes' if self.mock_mode else 'No'}")
        self.stdout.write(f"  Google Vision API: {'Configured' if getattr(settings, 'GOOGLE_VISION_API_KEY', '') else 'Not Configured'}")
        self.stdout.write(f"  OpenAI API: {'Configured' if getattr(settings, 'OPENAI_API_KEY', '') else 'Not Configured'}")
        self.stdout.write('')

    def test_photo_analysis(self, photo_path: Optional[str]) -> Dict[str, Any]:
        """Test photo analysis service."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing Photo Analysis Service'))
        self.stdout.write('-' * 40)
        
        service = PhotoAnalysisService()
        results = {
            'service': 'Photo Analysis',
            'tests': [],
            'success': True
        }
        
        # Test 1: Color extraction
        self.stdout.write('Test 1: Color Extraction')
        try:
            if photo_path and os.path.exists(photo_path):
                colors = service.extract_colors(photo_path)
                self.stdout.write(self.style.SUCCESS(f'  ✓ Extracted {len(colors)} colors'))
                for color in colors[:3]:
                    self.stdout.write(f'    - {color.get("name", "Unknown")}: {color.get("color", "N/A")} ({color.get("percentage", 0):.1f}%)')
                results['tests'].append({'name': 'Color Extraction', 'status': 'PASS', 'colors': len(colors)})
            else:
                # Use mock test
                mock_colors = service._mock_extract_colors('test_image.jpg')
                self.stdout.write(self.style.SUCCESS(f'  ✓ Mock mode - Extracted {len(mock_colors)} colors'))
                for color in mock_colors[:3]:
                    self.stdout.write(f'    - {color.get("name", "Unknown")}: {color.get("color", "N/A")} ({color.get("percentage", 0):.1f}%)')
                results['tests'].append({'name': 'Color Extraction', 'status': 'PASS (Mock)', 'colors': len(mock_colors)})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Color Extraction', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 2: Mood detection
        self.stdout.write('')
        self.stdout.write('Test 2: Mood Detection')
        try:
            if photo_path and os.path.exists(photo_path):
                mood = service.detect_mood(photo_path)
            else:
                mood = service._mock_detect_mood('test_image.jpg')
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Detected mood: {mood["primary"]} (confidence: {mood["confidence"]:.2f})'))
            if mood.get('secondary'):
                self.stdout.write(f'    Secondary moods: {", ".join(mood["secondary"])}')
            results['tests'].append({'name': 'Mood Detection', 'status': 'PASS', 'mood': mood['primary']})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Mood Detection', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 3: Full analysis
        self.stdout.write('')
        self.stdout.write('Test 3: Full Photo Analysis')
        try:
            if photo_path and os.path.exists(photo_path):
                analysis = service.analyze(photo_path, event_type='WEDDING')
            else:
                analysis = service._mock_analyze('test_image.jpg', event_type='WEDDING')
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Analysis complete'))
            self.stdout.write(f'    Colors: {len(analysis["colors"])}')
            self.stdout.write(f'    Mood: {analysis["mood"]["primary"]}')
            self.stdout.write(f'    Recommendations: {len(analysis["recommendations"])}')
            results['tests'].append({'name': 'Full Analysis', 'status': 'PASS'})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Full Analysis', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 4: Color utilities
        self.stdout.write('')
        self.stdout.write('Test 4: Color Utilities')
        try:
            # Test hex to RGB
            rgb = service.hex_to_rgb('#A61E2A')
            assert rgb == (166, 30, 42), f"Expected (166, 30, 42), got {rgb}"
            
            # Test RGB to hex
            hex_color = service.rgb_to_hex((166, 30, 42))
            assert hex_color == '#A61E2A', f"Expected #A61E2A, got {hex_color}"
            
            # Test color name
            name = service.get_color_name('#A61E2A')
            self.stdout.write(self.style.SUCCESS(f'  ✓ Color utilities working'))
            self.stdout.write(f'    #A61E2A -> {name}')
            results['tests'].append({'name': 'Color Utilities', 'status': 'PASS'})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Color Utilities', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        self.stdout.write('')
        return results

    def test_message_generation(self) -> Dict[str, Any]:
        """Test message generation service."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing Message Generation Service'))
        self.stdout.write('-' * 40)
        
        service = MessageGenerationService()
        results = {
            'service': 'Message Generation',
            'tests': [],
            'success': True
        }
        
        # Test 1: Generate messages
        self.stdout.write('Test 1: Generate Wedding Messages')
        try:
            context = {
                'bride_name': 'Priya',
                'groom_name': 'Rahul',
                'event_type': 'WEDDING',
                'culture': 'modern',
                'tone': 'warm',
                'details': 'Childhood sweethearts, destination wedding in Goa'
            }
            
            start_time = time.time()
            generated = service.generate_messages(
                context=context,
                style='romantic',
                num_options=3
            )
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated {len(generated.generated_options)} messages'))
            self.stdout.write(f'    Time: {elapsed_ms}ms')
            self.stdout.write(f'    Tokens: {generated.tokens_used}')
            
            for i, opt in enumerate(generated.generated_options[:2], 1):
                preview = opt['text'][:80] + '...' if len(opt['text']) > 80 else opt['text']
                self.stdout.write(f'    Option {i} ({opt["style"]}): {preview}')
            
            results['tests'].append({
                'name': 'Generate Messages',
                'status': 'PASS',
                'time_ms': elapsed_ms,
                'tokens': generated.tokens_used
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Generate Messages', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 2: Generate hashtags
        self.stdout.write('')
        self.stdout.write('Test 2: Generate Hashtags')
        try:
            hashtags = service.generate_hashtags(
                bride_name='Priya',
                groom_name='Rahul',
                wedding_date='2024-12-25',
                style='all',
                count=9
            )
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated {len(hashtags["hashtags"])} hashtags'))
            self.stdout.write(f'    Top pick: {hashtags["top_pick"]}')
            self.stdout.write(f'    Classic: {", ".join(hashtags["by_category"]["classic"][:3])}')
            self.stdout.write(f'    Fun: {", ".join(hashtags["by_category"]["fun"][:3])}')
            
            results['tests'].append({
                'name': 'Generate Hashtags',
                'status': 'PASS',
                'count': len(hashtags['hashtags'])
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Generate Hashtags', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 3: Generate suggestions
        self.stdout.write('')
        self.stdout.write('Test 3: Generate Smart Suggestions')
        try:
            event_data = {
                'event_type': 'WEDDING',
                'bride_name': 'Priya',
                'groom_name': 'Rahul',
                'event_date': '2024-12-25',
                'venue_type': 'outdoor',
                'guest_count': 150,
                'culture': 'indian'
            }
            
            suggestions = service.generate_smart_suggestions(event_data)
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated suggestions'))
            self.stdout.write(f'    Music categories: {len(suggestions["music_suggestions"])}')
            self.stdout.write(f'    Engagement tips: {len(suggestions["engagement_tips"])}')
            self.stdout.write(f'    Cultural notes: {len(suggestions["cultural_notes"])}')
            
            results['tests'].append({
                'name': 'Smart Suggestions',
                'status': 'PASS'
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Smart Suggestions', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        self.stdout.write('')
        return results

    def test_recommendations(self) -> Dict[str, Any]:
        """Test recommendation service."""
        self.stdout.write(self.style.MIGRATE_HEADING('Testing Recommendation Service'))
        self.stdout.write('-' * 40)
        
        service = RecommendationService()
        results = {
            'service': 'Recommendations',
            'tests': [],
            'success': True
        }
        
        # Test 1: Style recommendations
        self.stdout.write('Test 1: Style Recommendations')
        try:
            colors = ['#A61E2A', '#D4AF37', '#FFFFF0']
            mood = {
                'primary': 'romantic',
                'confidence': 0.92,
                'attributes': {'romantic': 0.92, 'elegant': 0.85}
            }
            
            style_recs = service.recommend_styles(
                colors=colors,
                mood=mood,
                event_type='WEDDING'
            )
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated {len(style_recs)} style recommendations'))
            for rec in style_recs[:3]:
                self.stdout.write(f'    - {rec["name"]} (confidence: {rec["confidence"]:.2f})')
            
            results['tests'].append({
                'name': 'Style Recommendations',
                'status': 'PASS',
                'count': len(style_recs)
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Style Recommendations', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 2: Color utilities
        self.stdout.write('')
        self.stdout.write('Test 2: Color Distance Calculation')
        try:
            from apps.ai.services.recommendation import color_distance_hex, find_closest_color
            
            # Test color distance
            distance = color_distance_hex('#FF0000', '#FF0000')
            assert distance == 0, f"Same color should have distance 0, got {distance}"
            
            distance = color_distance_hex('#FF0000', '#00FF00')
            self.stdout.write(self.style.SUCCESS(f'  ✓ Color distance calculation working'))
            self.stdout.write(f'    Distance between red and green: {distance:.3f}')
            
            # Test closest color
            colors = ['#FF0000', '#00FF00', '#0000FF']
            closest, dist = find_closest_color('#FF1111', colors)
            self.stdout.write(f'    Closest to #FF1111: {closest} (distance: {dist:.3f})')
            
            results['tests'].append({'name': 'Color Distance', 'status': 'PASS'})
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Color Distance', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        # Test 3: Template recommendations (mock)
        self.stdout.write('')
        self.stdout.write('Test 3: Template Recommendations')
        try:
            user_data = {
                'plan': 'PREMIUM',
                'user_id': 'test_user'
            }
            photo_analysis = {
                'colors': [
                    {'color': '#A61E2A', 'percentage': 40},
                    {'color': '#D4AF37', 'percentage': 30},
                    {'color': '#FFFFF0', 'percentage': 20}
                ],
                'mood': {
                    'primary': 'romantic',
                    'confidence': 0.92
                }
            }
            
            template_recs = service.recommend_templates(
                user_data=user_data,
                photo_analysis=photo_analysis,
                event_type='WEDDING',
                limit=5
            )
            
            self.stdout.write(self.style.SUCCESS(f'  ✓ Generated recommendations'))
            self.stdout.write(f'    Recommendations: {len(template_recs.get("recommendations", []))}')
            self.stdout.write(f'    Photo-based: {template_recs.get("personalization_factors", {}).get("photo_based", False)}')
            
            results['tests'].append({
                'name': 'Template Recommendations',
                'status': 'PASS',
                'count': len(template_recs.get('recommendations', []))
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ✗ Failed: {e}'))
            results['tests'].append({'name': 'Template Recommendations', 'status': 'FAIL', 'error': str(e)})
            results['success'] = False
        
        self.stdout.write('')
        return results

    def print_summary(self, results: List[Dict[str, Any]]):
        """Print test summary."""
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('TEST SUMMARY'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        for service_result in results:
            service_name = service_result['service']
            success = service_result['success']
            
            self.stdout.write('')
            if success:
                self.stdout.write(self.style.SUCCESS(f'✓ {service_name}'))
            else:
                self.stdout.write(self.style.ERROR(f'✗ {service_name}'))
            
            for test in service_result['tests']:
                total_tests += 1
                status = test['status']
                
                if 'PASS' in status:
                    passed_tests += 1
                    self.stdout.write(self.style.SUCCESS(f'    ✓ {test["name"]} ({status})'))
                else:
                    failed_tests += 1
                    self.stdout.write(self.style.ERROR(f'    ✗ {test["name"]}: {test.get("error", "Failed")}'))
        
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('-' * 60))
        self.stdout.write(f'Total Tests: {total_tests}')
        self.stdout.write(self.style.SUCCESS(f'Passed: {passed_tests}'))
        self.stdout.write(self.style.ERROR(f'Failed: {failed_tests}'))
        
        if failed_tests > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING('Some tests failed. Check the output above for details.'))
            sys.exit(1)
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('All tests passed!'))
            sys.exit(0)
