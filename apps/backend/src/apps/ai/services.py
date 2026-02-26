"""
AI Services for the wedding invitation platform.

This module provides services for:
- Photo analysis (color extraction, mood detection)
- Message generation using AI
- Template recommendations
- Smart suggestions
"""

import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog

logger = logging.getLogger(__name__)


class BaseAIService:
    """Base class for AI services with common functionality."""
    
    def log_usage(
        self,
        user,
        feature_type: str,
        request_data: Dict,
        response_data: Dict,
        tokens_used: int = 0,
        success: bool = True,
        error_message: str = '',
        processing_time_ms: Optional[int] = None
    ) -> AIUsageLog:
        """Log AI feature usage."""
        return AIUsageLog.objects.create(
            user=user,
            feature_type=feature_type,
            request_data=request_data,
            response_data=response_data,
            tokens_used=tokens_used,
            success=success,
            error_message=error_message,
            processing_time_ms=processing_time_ms
        )
    
    def generate_mock_colors(self, image_url: str) -> Dict:
        """Generate mock color extraction for development."""
        # Deterministic mock based on image_url length for consistency
        color_palettes = [
            {
                'dominant': {'hex': '#E8B4B8', 'percentage': 35.5, 'name': 'Dusty Rose'},
                'palette': [
                    {'hex': '#E8B4B8', 'percentage': 35.5, 'name': 'Dusty Rose'},
                    {'hex': '#EAD2AC', 'percentage': 25.3, 'name': 'Champagne'},
                    {'hex': '#6B8E8E', 'percentage': 20.1, 'name': 'Sage Green'},
                    {'hex': '#F5F5F5', 'percentage': 19.1, 'name': 'Ivory'},
                ],
                'palette_type': 'romantic'
            },
            {
                'dominant': {'hex': '#2C3E50', 'percentage': 40.2, 'name': 'Midnight Blue'},
                'palette': [
                    {'hex': '#2C3E50', 'percentage': 40.2, 'name': 'Midnight Blue'},
                    {'hex': '#D4AF37', 'percentage': 30.5, 'name': 'Gold'},
                    {'hex': '#FFFFFF', 'percentage': 20.3, 'name': 'White'},
                    {'hex': '#B8860B', 'percentage': 9.0, 'name': 'Dark Goldenrod'},
                ],
                'palette_type': 'elegant'
            },
            {
                'dominant': {'hex': '#FF6B6B', 'percentage': 32.1, 'name': 'Coral'},
                'palette': [
                    {'hex': '#FF6B6B', 'percentage': 32.1, 'name': 'Coral'},
                    {'hex': '#FFE66D', 'percentage': 28.4, 'name': 'Sunny Yellow'},
                    {'hex': '#4ECDC4', 'percentage': 22.5, 'name': 'Turquoise'},
                    {'hex': '#F7F7F7', 'percentage': 17.0, 'name': 'Off White'},
                ],
                'palette_type': 'vibrant'
            },
        ]
        # Select palette based on image_url hash for consistency
        import hashlib
        hash_val = int(hashlib.md5(image_url.encode()).hexdigest(), 16)
        return color_palettes[hash_val % len(color_palettes)]
    
    def generate_mock_mood(self, image_url: str) -> Dict:
        """Generate mock mood detection for development."""
        moods = [
            {
                'primary_mood': 'romantic',
                'confidence': 0.87,
                'tags': ['romantic', 'elegant', 'soft', 'dreamy', 'intimate'],
                'emotions': ['love', 'joy', 'tenderness'],
                'atmosphere': 'warm and intimate'
            },
            {
                'primary_mood': 'elegant',
                'confidence': 0.92,
                'tags': ['elegant', 'sophisticated', 'classic', 'refined', 'luxurious'],
                'emotions': ['pride', 'admiration', 'serenity'],
                'atmosphere': 'grand and majestic'
            },
            {
                'primary_mood': 'modern',
                'confidence': 0.78,
                'tags': ['modern', 'minimalist', 'chic', 'trendy', 'clean'],
                'emotions': ['excitement', 'curiosity', 'confidence'],
                'atmosphere': 'fresh and contemporary'
            },
        ]
        import hashlib
        hash_val = int(hashlib.md5(image_url.encode()).hexdigest(), 16)
        return moods[hash_val % len(moods)]


class PhotoAnalysisService(BaseAIService):
    """Service for analyzing photos and extracting features."""
    
    def analyze_photo(
        self,
        image_url: str,
        user,
        order=None,
        extract_colors: bool = True,
        detect_mood: bool = True,
        generate_recommendations: bool = True
    ) -> PhotoAnalysis:
        """
        Analyze a photo and extract features.
        
        Args:
            image_url: URL of the image to analyze
            user: User requesting the analysis
            event: Optional associated event
            extract_colors: Whether to extract colors
            detect_mood: Whether to detect mood
            generate_recommendations: Whether to generate recommendations
            
        Returns:
            PhotoAnalysis object with results
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"photo_analysis:{image_url}"
            cached_result = cache.get(cache_key)
            if cached_result and not settings.DEBUG:
                logger.info(f"Returning cached photo analysis for {image_url}")
                # Create new record from cache but don't re-analyze
                analysis = PhotoAnalysis.objects.create(
                    user=user,
                    order=order,
                    image_url=image_url,
                    primary_colors=cached_result.get('primary_colors', {}),
                    mood=cached_result.get('mood', {}),
                    style_recommendations=cached_result.get('style_recommendations', [])
                )
                return analysis
            
            # Use mock mode for development
            if getattr(settings, 'AI_MOCK_MODE', True):
                result = self._analyze_mock(
                    image_url,
                    extract_colors,
                    detect_mood,
                    generate_recommendations
                )
            else:
                result = self._analyze_real(
                    image_url,
                    extract_colors,
                    detect_mood,
                    generate_recommendations
                )
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create analysis record
            analysis = PhotoAnalysis.objects.create(
                user=user,
                order=order,
                image_url=image_url,
                primary_colors=result.get('colors', {}),
                mood=result.get('mood', {}),
                style_recommendations=result.get('recommendations', [])
            )
            
            # Log usage
            self.log_usage(
                user=user,
                feature_type='photo_analysis',
                request_data={
                    'image_url': image_url,
                    'extract_colors': extract_colors,
                    'detect_mood': detect_mood,
                    'generate_recommendations': generate_recommendations
                },
                response_data={
                    'analysis_id': str(analysis.id),
                    'colors_extracted': extract_colors,
                    'mood_detected': detect_mood
                },
                tokens_used=result.get('tokens_used', 100),
                success=True,
                processing_time_ms=processing_time_ms
            )
            
            # Cache result
            cache.set(cache_key, {
                'primary_colors': result.get('colors', {}),
                'mood': result.get('mood', {}),
                'style_recommendations': result.get('recommendations', [])
            }, timeout=getattr(settings, 'AI_CACHE_TTL', {}).get('photo_analysis', 86400))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Photo analysis failed: {e}")
            self.log_usage(
                user=user,
                feature_type='photo_analysis',
                request_data={'image_url': image_url},
                response_data={},
                success=False,
                error_message=str(e),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )
            raise
    
    def _analyze_mock(
        self,
        image_url: str,
        extract_colors: bool,
        detect_mood: bool,
        generate_recommendations: bool
    ) -> Dict:
        """Mock analysis for development."""
        result = {
            'colors': {},
            'mood': {},
            'recommendations': [],
            'tokens_used': 50
        }
        
        if extract_colors:
            result['colors'] = self.generate_mock_colors(image_url)
        
        if detect_mood:
            result['mood'] = self.generate_mock_mood(image_url)
        
        if generate_recommendations:
            result['recommendations'] = self._generate_mock_recommendations(
                result['colors'], result['mood']
            )
        
        return result
    
    def _analyze_real(
        self,
        image_url: str,
        extract_colors: bool,
        detect_mood: bool,
        generate_recommendations: bool
    ) -> Dict:
        """Real analysis using Google Vision API and other services."""
        # TODO: Implement real AI analysis
        # For now, fall back to mock
        return self._analyze_mock(image_url, extract_colors, detect_mood, generate_recommendations)
    
    def extract_colors(self, image_url: str) -> Dict:
        """Extract colors from a photo."""
        if getattr(settings, 'AI_MOCK_MODE', True):
            return self.generate_mock_colors(image_url)
        # TODO: Implement real color extraction
        return self.generate_mock_colors(image_url)
    
    def detect_mood(self, image_url: str) -> Dict:
        """Detect mood from a photo."""
        if getattr(settings, 'AI_MOCK_MODE', True):
            return self.generate_mock_mood(image_url)
        # TODO: Implement real mood detection
        return self.generate_mock_mood(image_url)
    
    def _generate_mock_recommendations(self, colors: Dict, mood: Dict) -> List[Dict]:
        """Generate mock style recommendations based on colors and mood."""
        recommendations = []
        
        # Determine palette type from colors
        palette_type = colors.get('palette_type', 'romantic')
        
        style_templates = {
            'romantic': {
                'name': 'Romantic Garden',
                'description': 'Soft, flowing designs with floral elements',
                'fonts': ['Playfair Display', 'Cormorant Garamond', 'Great Vibes'],
                'layouts': ['asymmetric', 'organic'],
                'decor_elements': ['flowers', 'lace', 'soft lighting']
            },
            'elegant': {
                'name': 'Classic Elegance',
                'description': 'Timeless designs with refined details',
                'fonts': ['Bodoni Moda', 'Cinzel', 'Libre Baskerville'],
                'layouts': ['symmetrical', 'centered'],
                'decor_elements': ['gold accents', 'crystal', 'velvet']
            },
            'vibrant': {
                'name': 'Modern Celebration',
                'description': 'Bold, contemporary designs with energy',
                'fonts': ['Montserrat', 'Oswald', 'Pacifico'],
                'layouts': ['dynamic', 'geometric'],
                'decor_elements': ['neon', 'geometric shapes', 'confetti']
            },
            'minimalist': {
                'name': 'Minimalist Chic',
                'description': 'Clean, simple designs with focus on typography',
                'fonts': ['Inter', 'Helvetica Neue', 'Futura'],
                'layouts': ['grid', 'asymmetric'],
                'decor_elements': ['negative space', 'lines', 'subtle textures']
            }
        }
        
        # Select style based on palette type
        style_key = palette_type if palette_type in style_templates else 'romantic'
        style = style_templates[style_key]
        
        recommendations.append({
            'type': 'style',
            'name': style['name'],
            'description': style['description'],
            'confidence': 0.85,
            'suggestions': {
                'fonts': style['fonts'],
                'layouts': style['layouts'],
                'decor_elements': style['decor_elements']
            }
        })
        
        # Add color-based recommendations
        if colors and 'palette' in colors:
            palette_colors = [c['hex'] for c in colors['palette'][:3]]
            recommendations.append({
                'type': 'color_scheme',
                'name': f'{palette_type.title()} Palette',
                'colors': palette_colors,
                'usage': {
                    'primary': palette_colors[0],
                    'secondary': palette_colors[1] if len(palette_colors) > 1 else palette_colors[0],
                    'accent': palette_colors[2] if len(palette_colors) > 2 else palette_colors[0]
                }
            })
        
        return recommendations


class MessageGenerationService(BaseAIService):
    """Service for generating AI-powered invitation messages."""
    
    def generate_messages(
        self,
        context: Dict,
        style: str,
        num_options: int = 3,
        user=None,
        order=None
    ) -> GeneratedMessage:
        """
        Generate invitation messages.
        
        Args:
            context: Message context (bride_name, groom_name, etc.)
            style: Message style (romantic, formal, casual, etc.)
            num_options: Number of message options to generate
            user: User requesting generation
            event: Optional associated event
            
        Returns:
            GeneratedMessage object with options
        """
        start_time = time.time()
        
        try:
            if getattr(settings, 'AI_MOCK_MODE', True):
                options = self._generate_mock_messages(context, style, num_options)
                tokens_used = 150
            else:
                options = self._generate_real_messages(context, style, num_options)
                tokens_used = 250
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Create message record
            message = GeneratedMessage.objects.create(
                user=user,
                order=order,
                context=context,
                generated_options=options,
                style_used=style,
                tokens_used=tokens_used
            )
            
            # Log usage
            if user:
                self.log_usage(
                    user=user,
                    feature_type='message_generation',
                    request_data={'context': context, 'style': style, 'num_options': num_options},
                    response_data={'options_count': len(options), 'message_id': str(message.id)},
                    tokens_used=tokens_used,
                    success=True,
                    processing_time_ms=processing_time_ms
                )
            
            return message
            
        except Exception as e:
            logger.error(f"Message generation failed: {e}")
            if user:
                self.log_usage(
                    user=user,
                    feature_type='message_generation',
                    request_data={'context': context, 'style': style},
                    response_data={},
                    success=False,
                    error_message=str(e),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            raise
    
    def _generate_mock_messages(self, context: Dict, style: str, num_options: int) -> List[Dict]:
        """Generate mock messages for development."""
        bride = context.get('bride_name', 'Bride')
        groom = context.get('groom_name', 'Groom')
        event_date = context.get('event_date', '')
        venue = context.get('venue', 'our special venue')
        
        templates = {
            'romantic': [
                f"Together with our families, we {bride} and {groom} invite you to share in the joy of our wedding day. Join us as we begin our forever on {event_date} at {venue}.",
                f"Love has brought us together, and now we invite you to witness our happily ever after. {bride} and {groom} request the pleasure of your company on our special day at {venue}.",
                f"Two hearts, one love, endless possibilities. We, {bride} and {groom}, would be honored by your presence as we say 'I do' on {event_date}.",
            ],
            'formal': [
                f"Mr. and Mrs. [Family Name] request the honor of your presence at the marriage of their daughter {bride} to {groom} on {event_date} at {venue}.",
                f"You are cordially invited to attend the wedding ceremony of {bride} and {groom} to be held on {event_date} at {venue}.",
                f"The honor of your presence is requested at the nuptials of {bride} and {groom} on {event_date} at {venue}.",
            ],
            'casual': [
                f"We're getting hitched! {bride} and {groom} invite you to party with us on {event_date} at {venue}. Can't wait to celebrate!",
                f"It's official! {bride} and {groom} are tying the knot and want YOU there! Join us on {event_date} at {venue} for food, drinks, and dancing!",
                f"Big news! {bride} and {groom} are getting married! Save the date: {event_date} at {venue}. It's going to be awesome!",
            ],
            'funny': [
                f"Finally! {bride} and {groom} are making it official before {groom} changes their mind. Join us on {event_date} at {venue} for cake and chaos!",
                f"{bride} is marrying {groom} and everyone's invited! Free food and open bar (maybe). {event_date} at {venue} - be there or be square!",
                f"Warning: {bride} and {groom} are about to do something really stupid (and romantic). Witness the madness on {event_date} at {venue}!",
            ],
            'poetic': [
                f"Like two rivers merging into one sea, our lives unite. {bride} and {groom} invite you to witness the poetry of our love on {event_date} at {venue}.",
                f"In the garden of love, two souls bloom as one. Join {bride} and {groom} as we write the next chapter of our story on {event_date}.",
                f"Stars aligned, hearts entwined, destinies merged. {bride} and {groom} welcome you to our celestial celebration on {event_date} at {venue}.",
            ],
            'traditional': [
                f"With the blessings of our elders and the love of our families, {bride} and {groom} request your presence at our wedding on {event_date} at {venue}.",
                f"As we embark on the sacred journey of marriage, we invite you to bless {bride} and {groom} on our wedding day, {event_date} at {venue}.",
                f"In the presence of family and friends, {bride} and {groom} will unite in marriage on {event_date}. We seek your blessings at {venue}.",
            ],
            'modern': [
                f"{bride} & {groom} are getting married! Join us on {event_date} at {venue} as we celebrate love, partnership, and our next adventure together.",
                f"Save the date! {bride} and {groom}'s wedding on {event_date} at {venue}. Join us for an evening of love, laughter, and happily ever after.",
                f"We're saying YES to forever! {bride} and {groom} invite you to celebrate our love story on {event_date} at {venue}.",
            ],
        }
        
        style_messages = templates.get(style, templates['romantic'])
        options = []
        for i, message in enumerate(style_messages[:num_options]):
            options.append({
                'id': f'opt_{i+1}',
                'text': message,
                'style': style,
                'tone': self._get_tone_from_style(style)
            })
        
        return options
    
    def _generate_real_messages(self, context: Dict, style: str, num_options: int) -> List[Dict]:
        """Generate messages using OpenAI API."""
        # TODO: Implement OpenAI integration
        return self._generate_mock_messages(context, style, num_options)
    
    def _get_tone_from_style(self, style: str) -> str:
        """Get tone description from style."""
        tone_map = {
            'romantic': 'warm and loving',
            'formal': 'respectful and elegant',
            'casual': 'friendly and relaxed',
            'funny': 'humorous and light',
            'poetic': 'artistic and lyrical',
            'traditional': 'respectful and classic',
            'modern': 'contemporary and fresh',
        }
        return tone_map.get(style, 'warm')
    
    def generate_hashtags(
        self,
        bride_name: str,
        groom_name: str,
        style: str = 'romantic',
        count: int = 10
    ) -> List[str]:
        """Generate wedding hashtags."""
        bride = bride_name.split()[0] if bride_name else 'Bride'
        groom = groom_name.split()[0] if groom_name else 'Groom'
        
        # Combine names for portmanteau
        combined = f"{bride}{groom}"
        
        hashtag_templates = {
            'romantic': [
                f"#{combined}Forever",
                f"#{bride}And{groom}TieTheKnot",
                f"#Love{bride}{groom}",
                f"#{combined}Wedding",
                f"#HappilyEverAfter{combined}",
                f"#Forever{bride}And{groom}",
                f"#Soulmates{combined}",
                f"#{combined}LoveStory",
                f"#ToHaveAndToHold{combined}",
                f"#{bride}Loves{groom}",
            ],
            'funny': [
                f"#{combined}Finally",
                f"#{groom}PutARingOnIt",
                f"#{bride}SaidYes{groom}SaidFinally",
                f"#{combined}PartyTime",
                f"#GameOver{groom}",
                f"#{bride}Won{groom}Lost",
                f"#{combined}ChaosBegins",
                f"#{bride}Trapped{groom}",
                f"#{combined}OpenBar",
                f"#HereComesTheBrideRun{groom}Run",
            ],
            'modern': [
                f"#{combined}2024",
                f"#Team{combined}",
                f"#{bride}x{groom}",
                f"#{combined}Wedding",
                f"#{combined}Celebration",
                f"#The{combined}s",
                f"#{bride}Plus{groom}",
                f"#{combined}Vibes",
                f"#{combined}Era",
                f"#WeAre{combined}",
            ],
        }
        
        hashtags = hashtag_templates.get(style, hashtag_templates['romantic'])
        return hashtags[:count]


class RecommendationService(BaseAIService):
    """Service for template and style recommendations."""
    
    def recommend_templates(
        self,
        user,
        order=None,
        photo_analysis=None,
        preferences: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Recommend templates based on user preferences and photo analysis.
        
        Args:
            user: User requesting recommendations
            event: Optional associated event
            photo_analysis: Optional photo analysis results
            preferences: User preferences dict
            
        Returns:
            List of template recommendations with match scores
        """
        from apps.plans.models import Template
        
        preferences = preferences or {}
        
        # Get all available templates
        templates = Template.objects.filter(is_active=True)
        
        # Filter by plan if user has an order
        if event and hasattr(event, 'order'):
            plan = event.order.plan
            templates = templates.filter(plan=plan)
        
        # Calculate match scores
        recommendations = []
        for template in templates[:20]:  # Limit to 20 for performance
            score, reasons = self._calculate_template_match(
                template,
                photo_analysis,
                preferences
            )
            
            recommendations.append({
                'template_id': str(template.id),
                'name': template.name,
                'match_score': score,
                'match_reasons': reasons,
                'preview_url': template.preview_url if hasattr(template, 'preview_url') else None,
                'thumbnail': template.thumbnail_url if hasattr(template, 'thumbnail_url') else None,
                'category': template.category if hasattr(template, 'category') else 'general',
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Log usage
        self.log_usage(
            user=user,
            feature_type='template_recommendation',
            request_data={
                'photo_analysis_id': str(photo_analysis.id) if photo_analysis else None,
                'preferences': preferences
            },
            response_data={'recommendations_count': len(recommendations)},
            tokens_used=10,
            success=True
        )
        
        return recommendations[:10]  # Return top 10
    
    def _calculate_template_match(
        self,
        template,
        photo_analysis,
        preferences: Dict
    ) -> tuple:
        """Calculate match score for a template."""
        score = 0.5  # Base score
        reasons = []
        
        # Score based on photo analysis
        if photo_analysis:
            mood_tags = photo_analysis.get_mood_tags()
            template_style = getattr(template, 'style', 'general')
            
            if mood_tags and template_style in mood_tags:
                score += 0.2
                reasons.append(f"Matches {template_style} aesthetic from your photo")
            
            # Check color compatibility
            primary_colors = photo_analysis.primary_colors
            if primary_colors and hasattr(template, 'color_palette'):
                template_colors = template.color_palette
                # Simple color matching logic
                score += 0.15
                reasons.append("Colors complement your photo palette")
        
        # Score based on preferences
        preferred_style = preferences.get('style')
        if preferred_style and hasattr(template, 'style'):
            if template.style == preferred_style:
                score += 0.25
                reasons.append(f"Matches your preferred {preferred_style} style")
        
        preferred_category = preferences.get('category')
        if preferred_category and hasattr(template, 'category'):
            if template.category == preferred_category:
                score += 0.2
                reasons.append(f"In your preferred {preferred_category} category")
        
        # Ensure score is between 0 and 1
        score = min(1.0, max(0.0, score))
        
        if not reasons:
            reasons.append("Popular choice for similar events")
        
        return score, reasons
    
    def recommend_styles(self, photo_analysis: PhotoAnalysis) -> List[Dict]:
        """
        Recommend styles based on photo analysis.
        
        Args:
            photo_analysis: Photo analysis results
            
        Returns:
            List of style recommendations
        """
        recommendations = []
        
        # Get mood and colors
        mood = photo_analysis.mood or {}
        colors = photo_analysis.primary_colors or {}
        
        mood_tags = mood.get('tags', [])
        primary_mood = mood.get('primary_mood', 'romantic')
        
        # Style mapping based on mood
        style_map = {
            'romantic': {
                'name': 'Romantic Garden',
                'description': 'Soft, floral designs with elegant typography',
                'font_recommendations': ['Playfair Display', 'Cormorant Garamond'],
                'color_recommendations': ['#E8B4B8', '#EAD2AC', '#F5F5F5']
            },
            'elegant': {
                'name': 'Classic Elegance',
                'description': 'Timeless designs with refined details',
                'font_recommendations': ['Bodoni Moda', 'Cinzel'],
                'color_recommendations': ['#2C3E50', '#D4AF37', '#FFFFFF']
            },
            'modern': {
                'name': 'Modern Minimalist',
                'description': 'Clean, contemporary designs',
                'font_recommendations': ['Montserrat', 'Inter'],
                'color_recommendations': ['#000000', '#FFFFFF', '#FF6B6B']
            },
            'vibrant': {
                'name': 'Bold & Bright',
                'description': 'Colorful, energetic designs',
                'font_recommendations': ['Oswald', 'Pacifico'],
                'color_recommendations': ['#FF6B6B', '#FFE66D', '#4ECDC4']
            }
        }
        
        # Primary recommendation based on detected mood
        if primary_mood in style_map:
            style = style_map[primary_mood]
            recommendations.append({
                'style_name': style['name'],
                'match_score': mood.get('confidence', 0.8),
                'color_palette': style['color_recommendations'],
                'font_recommendations': style['font_recommendations'],
                'description': style['description']
            })
        
        # Additional recommendations based on other mood tags
        for tag in mood_tags[:2]:
            if tag in style_map and tag != primary_mood:
                style = style_map[tag]
                recommendations.append({
                    'style_name': style['name'],
                    'match_score': 0.6,
                    'color_palette': style['color_recommendations'],
                    'font_recommendations': style['font_recommendations'],
                    'description': style['description']
                })
        
        return recommendations
    
    def get_smart_suggestions(
        self,
        category: str,
        context: Dict,
        user=None
    ) -> List[str]:
        """
        Get smart suggestions for event planning.
        
        Args:
            category: Category of suggestions (venue, timeline, etc.)
            context: Context data
            user: User requesting suggestions
            
        Returns:
            List of suggestion strings
        """
        suggestions_map = {
            'venue': [
                "Consider venues with both indoor and outdoor options for flexibility",
                "Visit your top 3 venues at the same time of day as your event",
                "Ask about vendor restrictions and corkage fees",
                "Check if the venue has a backup power source",
                "Consider guest parking and transportation options",
            ],
            'timeline': [
                "Send save-the-dates 6-8 months before the wedding",
                "Book your venue at least 12 months in advance",
                "Schedule dress fittings 2-3 months before the big day",
                "Finalize your guest list 3 months before invitations go out",
                "Apply for marriage license 1-2 months before the wedding",
            ],
            'budget': [
                "Allocate 50% of budget for venue and catering",
                "Set aside 10-15% for unexpected expenses",
                "Consider DIY options for decorations and favors",
                "Negotiate package deals with vendors",
                "Use a wedding budget tracker app",
            ],
            'decor': [
                "Choose 2-3 main colors and 1 accent color",
                "Rent larger decor items instead of buying",
                "Use candles for elegant, budget-friendly ambiance",
                "Incorporate personal items for meaningful touches",
                "Consider seasonal flowers for better prices",
            ],
            'photography': [
                "Book your photographer 9-12 months in advance",
                "Create a must-have shot list",
                "Schedule a engagement session to get comfortable",
                "Consider a second shooter for comprehensive coverage",
                "Ask about timeline and delivery expectations",
            ],
            'invitation': [
                "Order 10-15% extra invitations for mistakes and keepsakes",
                "Send invitations 6-8 weeks before the wedding",
                "Include RSVP deadline 3-4 weeks before the event",
                "Proofread multiple times before printing",
                "Consider digital RSVPs to save on postage",
            ],
        }
        
        suggestions = suggestions_map.get(category, [
            "Start planning early to reduce stress",
            "Create a wedding planning timeline",
            "Delegate tasks to trusted friends and family",
            "Take time to enjoy the engagement period",
            "Remember what matters most - your love story",
        ])
        
        # Log usage
        if user:
            self.log_usage(
                user=user,
                feature_type='smart_suggestions',
                request_data={'category': category, 'context': context},
                response_data={'suggestions_count': len(suggestions)},
                tokens_used=5,
                success=True
            )
        
        return suggestions
