"""
Template Recommendation Engine.

This module provides intelligent template and style recommendations based on:
- Photo analysis results (colors, mood)
- User preferences and history
- Template popularity and usage stats
- Event type matching

Usage:
    >>> service = RecommendationService()
    >>> recommendations = service.recommend_templates(
    ...     user_data={'plan': 'PREMIUM'},
    ...     photo_analysis={'colors': [...], 'mood': {...}},
    ...     event_type='WEDDING',
    ...     limit=5
    ... )

Performance Notes:
    - Template queries use select_related and prefetch_related for efficiency
    - Expensive calculations are cached with 1-hour TTL
    - Division by zero is protected in all scoring calculations
"""

import logging
import random
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import lru_cache

from django.conf import settings
from django.db.models import Count, Q, F, QuerySet, Avg
from django.core.cache import cache
from django.utils import timezone

from .base_ai import BaseAIService, AIServiceError, retry_on_failure

# Import models lazily to avoid AppRegistryNotReady
Plan = None
Template = None


def get_plan_model():
    """Lazy import of Plan model."""
    global Plan
    if Plan is None:
        from apps.plans.models import Plan as PlanModel
        Plan = PlanModel
    return Plan


def get_template_model():
    """Lazy import of Template model."""
    global Template
    if Template is None:
        from apps.plans.models import Template as TemplateModel
        Template = TemplateModel
    return Template


# =============================================================================
# Constants
# =============================================================================

# Cache timeouts (in seconds)
CACHE_TIMEOUT_TEMPLATES = 3600  # 1 hour
CACHE_TIMEOUT_TRENDING = 1800   # 30 minutes
CACHE_TIMEOUT_STYLES = 3600     # 1 hour

# Scoring weights (must sum to 1.0)
WEIGHT_COLOR_MATCH = 0.40
WEIGHT_MOOD_MATCH = 0.30
WEIGHT_EVENT_MATCH = 0.15
WEIGHT_POPULARITY = 0.15

# Scoring limits
MIN_SCORE = 0.0
MAX_SCORE = 1.0
DEFAULT_NEUTRAL_SCORE = 0.5

# Color distance weights for perceptual matching
COLOR_DISTANCE_HUE_WEIGHT = 0.5
COLOR_DISTANCE_SAT_WEIGHT = 0.25
COLOR_DISTANCE_LIGHT_WEIGHT = 0.25

# Plan hierarchy (for access control)
PLAN_HIERARCHY: Dict[str, List[str]] = {
    'BASIC': ['BASIC'],
    'PREMIUM': ['BASIC', 'PREMIUM'],
    'LUXURY': ['BASIC', 'PREMIUM', 'LUXURY']
}

# Default pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Logger
logger = logging.getLogger(__name__)


# =============================================================================
# Style Profile Definitions
# =============================================================================

STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
    'romantic_elegance': {
        'name': 'Romantic Elegance',
        'description': 'Soft, flowing designs with heart motifs and pastel colors',
        'primary_colors': ['#FFB6C1', '#FFC0CB', '#FF69B4', '#FFFFFF'],
        'moods': ['romantic', 'elegant', 'soft'],
        'keywords': ['love', 'heart', 'flowers', 'soft', 'elegant'],
        'suitable_events': ['WEDDING', 'ANNIVERSARY'],
        'font_style': 'script',
        'decoration_elements': ['hearts', 'flowers', 'ribbons']
    },
    'modern_minimalist': {
        'name': 'Modern Minimalist',
        'description': 'Clean lines, ample white space, contemporary typography',
        'primary_colors': ['#000000', '#FFFFFF', '#808080', '#2C3E50'],
        'moods': ['modern', 'minimalist', 'clean'],
        'keywords': ['modern', 'clean', 'minimal', 'contemporary'],
        'suitable_events': ['WEDDING', 'PARTY', 'CORPORATE'],
        'font_style': 'sans-serif',
        'decoration_elements': ['geometric', 'lines']
    },
    'traditional_royal': {
        'name': 'Traditional Royal',
        'description': 'Rich colors, ornate patterns, gold accents',
        'primary_colors': ['#8B0000', '#D4AF37', '#4B0082', '#FFD700'],
        'moods': ['traditional', 'royal', 'grand'],
        'keywords': ['traditional', 'royal', 'gold', 'ornate', 'classic'],
        'suitable_events': ['WEDDING', 'FESTIVAL'],
        'font_style': 'serif',
        'decoration_elements': ['gold', 'ornate', 'patterns', 'mandala']
    },
    'fun_vibrant': {
        'name': 'Fun & Vibrant',
        'description': 'Bold colors, playful elements, energetic feel',
        'primary_colors': ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3'],
        'moods': ['fun', 'energetic', 'playful'],
        'keywords': ['fun', 'colorful', 'playful', 'party'],
        'suitable_events': ['BIRTHDAY', 'PARTY', 'FESTIVAL'],
        'font_style': 'display',
        'decoration_elements': ['confetti', 'balloons', 'patterns']
    },
    'classic_timeless': {
        'name': 'Classic Timeless',
        'description': 'Elegant simplicity that never goes out of style',
        'primary_colors': ['#000000', '#FFFFFF', '#C0C0C0', '#F5F5DC'],
        'moods': ['classic', 'elegant', 'timeless'],
        'keywords': ['classic', 'elegant', 'timeless', 'sophisticated'],
        'suitable_events': ['WEDDING', 'ANNIVERSARY', 'FORMAL'],
        'font_style': 'serif',
        'decoration_elements': ['simple', 'elegant', 'monogram']
    },
    'rustic_charm': {
        'name': 'Rustic Charm',
        'description': 'Natural, earthy tones with vintage elements',
        'primary_colors': ['#8B4513', '#D2691E', '#F4A460', '#556B2F'],
        'moods': ['rustic', 'natural', 'warm'],
        'keywords': ['rustic', 'vintage', 'natural', 'earthy'],
        'suitable_events': ['WEDDING', 'PARTY'],
        'font_style': 'handwritten',
        'decoration_elements': ['wood', 'flowers', 'burlap', 'vintage']
    }
}


# =============================================================================
# Mock Data for Development
# =============================================================================

MOCK_RECOMMENDATIONS: List[Dict[str, Any]] = [
    {
        'template_id': 'tpl_romantic_001',
        'name': 'Rose Petal Dreams',
        'match_score': 0.94,
        'match_reasons': [
            "Matches your photo's warm color scheme",
            "Popular for romantic weddings",
            "Trending this season"
        ],
        'preview_url': '/templates/romantic_001/preview',
        'thumbnail': '/templates/romantic_001/thumb.jpg',
        'style': 'romantic_elegance',
        'plan_required': 'BASIC'
    },
    {
        'template_id': 'tpl_royal_002',
        'name': 'Royal Red Affair',
        'match_score': 0.91,
        'match_reasons': [
            "Complements traditional wedding themes",
            "High user satisfaction rating",
            "Matches your elegant style preference"
        ],
        'preview_url': '/templates/royal_002/preview',
        'thumbnail': '/templates/royal_002/thumb.jpg',
        'style': 'traditional_royal',
        'plan_required': 'PREMIUM'
    },
    {
        'template_id': 'tpl_modern_003',
        'name': 'Minimalist Love',
        'match_score': 0.87,
        'match_reasons': [
            "Clean design matches modern aesthetic",
            "Optimized for mobile viewing",
            "Fast loading speed"
        ],
        'preview_url': '/templates/modern_003/preview',
        'thumbnail': '/templates/modern_003/thumb.jpg',
        'style': 'modern_minimalist',
        'plan_required': 'BASIC'
    },
    {
        'template_id': 'tpl_classic_004',
        'name': 'Timeless Romance',
        'match_score': 0.85,
        'match_reasons': [
            "Classic design suits any wedding",
            "Highly customizable",
            "Elegant typography"
        ],
        'preview_url': '/templates/classic_004/preview',
        'thumbnail': '/templates/classic_004/thumb.jpg',
        'style': 'classic_timeless',
        'plan_required': 'PREMIUM'
    },
    {
        'template_id': 'tpl_rustic_005',
        'name': 'Garden Party',
        'match_score': 0.82,
        'match_reasons': [
            "Natural elements match outdoor venues",
            "Warm, inviting atmosphere",
            "Floral accents throughout"
        ],
        'preview_url': '/templates/rustic_005/preview',
        'thumbnail': '/templates/rustic_005/thumb.jpg',
        'style': 'rustic_charm',
        'plan_required': 'LUXURY'
    }
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class TemplateRecommendation:
    """Template recommendation with match details.
    
    Attributes:
        template_id: Unique template identifier.
        name: Template display name.
        match_score: Overall match score (0-1).
        match_reasons: Human-readable reasons for the match.
        match_details: Detailed scoring breakdown.
        preview_url: URL to template preview.
        thumbnail: URL to template thumbnail.
        style: Style category.
        plan_required: Required plan code.
    """
    template_id: str
    name: str
    match_score: float
    match_reasons: List[str]
    match_details: Dict[str, float]
    preview_url: Optional[str] = None
    thumbnail: Optional[str] = None
    style: Optional[str] = None
    plan_required: str = 'BASIC'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'template_id': self.template_id,
            'name': self.name,
            'match_score': self.match_score,
            'match_reasons': self.match_reasons,
            'match_details': self.match_details,
            'preview_url': self.preview_url,
            'thumbnail': self.thumbnail,
            'style': self.style,
            'plan_required': self.plan_required
        }


@dataclass(frozen=True)
class StyleRecommendation:
    """Style recommendation with confidence score.
    
    Attributes:
        style_key: Style identifier.
        name: Style display name.
        confidence: Confidence score (0-1).
        description: Style description.
        color_palette: Recommended color palette.
        font_recommendations: Recommended fonts.
        elements: Decorative elements.
        suitable_events: Compatible event types.
    """
    style_key: str
    name: str
    confidence: float
    description: str
    color_palette: List[str]
    font_recommendations: List[str]
    elements: List[str]
    suitable_events: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'style_key': self.style_key,
            'name': self.name,
            'confidence': self.confidence,
            'description': self.description,
            'color_palette': self.color_palette,
            'font_recommendations': self.font_recommendations,
            'elements': self.elements,
            'suitable_events': self.suitable_events
        }


# =============================================================================
# Color Utilities
# =============================================================================

def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """Convert hex color to RGB tuple.
    
    Args:
        hex_color: Hex color code (e.g., "#A61E2A" or "A61E2A").
        
    Returns:
        RGB tuple (r, g, b) or None if invalid.
    """
    hex_clean = hex_color.lstrip('#')
    
    if len(hex_clean) == 3:
        # Short form (e.g., "ABC" -> "AABBCC")
        hex_clean = ''.join(c * 2 for c in hex_clean)
    
    if len(hex_clean) != 6:
        return None
    
    try:
        r = int(hex_clean[0:2], 16)
        g = int(hex_clean[2:4], 16)
        b = int(hex_clean[4:6], 16)
        return (r, g, b)
    except ValueError:
        return None


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color code.
    
    Args:
        rgb: RGB tuple (r, g, b).
        
    Returns:
        Hex color code (e.g., "#A61E2A").
    """
    return '#{:02x}{:02x}{:02x}'.format(
        max(0, min(255, rgb[0])),
        max(0, min(255, rgb[1])),
        max(0, min(255, rgb[2]))
    ).upper()


def rgb_to_hsl(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL color space.
    
    Args:
        rgb: RGB tuple (r, g, b).
        
    Returns:
        HSL tuple (hue: 0-360, saturation: 0-100, lightness: 0-100).
    """
    r_norm, g_norm, b_norm = rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0
    
    max_val = max(r_norm, g_norm, b_norm)
    min_val = min(r_norm, g_norm, b_norm)
    diff = max_val - min_val
    
    # Lightness
    l = (max_val + min_val) / 2
    
    # Saturation
    if diff == 0:
        s = 0
    else:
        s = diff / (2 - max_val - min_val) if l > 0.5 else diff / (max_val + min_val)
    
    # Hue
    if diff == 0:
        h = 0
    elif max_val == r_norm:
        h = (60 * ((g_norm - b_norm) / diff) + 360) % 360
    elif max_val == g_norm:
        h = (60 * ((b_norm - r_norm) / diff) + 120) % 360
    else:
        h = (60 * ((r_norm - g_norm) / diff) + 240) % 360
    
    return (h, s * 100, l * 100)


def color_distance_hex(hex1: str, hex2: str) -> float:
    """Calculate distance between two colors (0-1, lower is closer).
    
    Uses HSL color space for perceptually uniform distance calculation,
    with hue weighted more heavily than saturation/lightness.
    
    Args:
        hex1: First hex color.
        hex2: Second hex color.
        
    Returns:
        Distance value between 0 (identical) and 1 (maximally different).
    """
    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)
    
    if not rgb1 or not rgb2:
        return 1.0  # Maximum distance for invalid colors
    
    # Convert to HSL for better perceptual distance
    hsl1 = rgb_to_hsl(rgb1)
    hsl2 = rgb_to_hsl(rgb2)
    
    # Weight hue more than saturation/lightness
    hue_diff = min(abs(hsl1[0] - hsl2[0]), 360 - abs(hsl1[0] - hsl2[0])) / 360
    sat_diff = abs(hsl1[1] - hsl2[1]) / 100
    light_diff = abs(hsl1[2] - hsl2[2]) / 100
    
    return (
        COLOR_DISTANCE_HUE_WEIGHT * hue_diff +
        COLOR_DISTANCE_SAT_WEIGHT * sat_diff +
        COLOR_DISTANCE_LIGHT_WEIGHT * light_diff
    )


def find_closest_color(target_hex: str, color_list: List[str]) -> Tuple[str, float]:
    """Find the closest color in a list to the target color.
    
    Args:
        target_hex: Target hex color.
        color_list: List of hex colors to search.
        
    Returns:
        Tuple of (closest_color, distance).
    """
    if not color_list:
        return target_hex, 0.0
    
    min_distance = float('inf')
    closest = color_list[0]
    
    for color in color_list:
        distance = color_distance_hex(target_hex, color)
        if distance < min_distance:
            min_distance = distance
            closest = color
    
    return closest, min_distance


# =============================================================================
# Recommendation Service
# =============================================================================

class RecommendationService(BaseAIService):
    """Service for providing intelligent template and style recommendations.
    
    This service uses a multi-factor scoring algorithm to recommend templates:
    - Color match: 40% weight
    - Mood match: 30% weight
    - Event match: 15% weight
    - Popularity: 15% weight
    
    Features:
    - Content-based filtering using photo analysis
    - Popularity-based recommendations
    - Plan-based filtering for access control
    - Similar template discovery
    - Trending templates tracking
    
    Example:
        >>> service = RecommendationService()
        >>> recommendations = service.recommend_templates(
        ...     user_data={'plan': 'PREMIUM', 'user_id': '123'},
        ...     photo_analysis={
        ...         'colors': [{'color': '#FF6B6B', 'percentage': 40}],
        ...         'mood': {'primary': 'romantic', 'confidence': 0.9}
        ...     },
        ...     event_type='WEDDING',
        ...     limit=5
        ... )
    """
    
    CACHE_TIMEOUT = CACHE_TIMEOUT_TEMPLATES
    
    # Scoring weights
    WEIGHT_COLOR_MATCH = WEIGHT_COLOR_MATCH
    WEIGHT_MOOD_MATCH = WEIGHT_MOOD_MATCH
    WEIGHT_EVENT_MATCH = WEIGHT_EVENT_MATCH
    WEIGHT_POPULARITY = WEIGHT_POPULARITY
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Recommendation Service.
        
        Args:
            api_key: Optional API key for external recommendation services.
        """
        super().__init__(api_key=api_key, model='recommendation')
        self.logger = logging.getLogger(__name__)
        self.mock_mode = getattr(settings, 'AI_MOCK_MODE', False)
        
        if self.mock_mode:
            self.logger.info("RecommendationService running in MOCK mode")
    
    def recommend_templates(
        self,
        user_data: Dict[str, Any],
        photo_analysis: Optional[Dict[str, Any]] = None,
        event_type: str = 'WEDDING',
        limit: int = 5,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE
    ) -> Dict[str, Any]:
        """Recommend templates based on multiple factors.
        
        Algorithm:
        1. Content-based filtering (photo colors, mood) - 50% weight
        2. Popularity score - 20% weight
        3. Plan-based filtering (user's plan determines available templates)
        4. Return top N with explanations
        
        Args:
            user_data: User preferences and history containing:
                - plan: User's plan code (BASIC, PREMIUM, LUXURY)
                - user_id: Optional user ID for personalization
                - preferences: Optional style preferences
            photo_analysis: Results from photo analysis with:
                - colors: List of extracted colors with hex values
                - mood: Detected mood with primary and confidence
            event_type: Type of event (WEDDING, BIRTHDAY, etc.).
            limit: Number of recommendations to return.
            page: Page number for pagination (1-indexed).
            page_size: Number of results per page.
            
        Returns:
            Dictionary containing:
                - recommendations: List of template recommendations
                - personalization_factors: Dict of which factors were used
                - total_available: Total templates available for user
                - page: Current page number
                - total_pages: Total number of pages
                
        Raises:
            AIServiceError: If recommendation generation fails.
        """
        try:
            # Validate pagination
            page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
            page = max(page, 1)
            
            # Check cache
            user_id = user_data.get('user_id', 'anonymous')
            cache_key = self._get_cache_key(
                'template_recommendations',
                user_id,
                event_type,
                str(photo_analysis) if photo_analysis else 'no_photo',
                limit,
                page,
                page_size
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                self.logger.info(f"Returning cached recommendations for user {user_id}")
                return cached
            
            # Return mock data if in mock mode
            if self.mock_mode:
                result = self._get_mock_recommendations(event_type, limit)
                self._set_cache(cache_key, result)
                return result
            
            # Get user's plan for filtering
            user_plan = user_data.get('plan', 'BASIC')
            
            # Get available templates based on plan (optimized query)
            templates = self._get_available_templates(user_plan, event_type)
            total_available = templates.count() if isinstance(templates, QuerySet) else len(templates)
            
            if not templates:
                self.logger.warning(f"No templates available for plan {user_plan}")
                return {
                    'recommendations': [],
                    'personalization_factors': {
                        'photo_based': False,
                        'color_analysis': False,
                        'mood_detection': False
                    },
                    'total_available': 0,
                    'page': page,
                    'total_pages': 0
                }
            
            # Calculate scores for each template
            scored_templates = []
            for template in templates:
                score, details = self.calculate_match_score(
                    template, photo_analysis, event_type
                )
                scored_templates.append({
                    'template': template,
                    'score': score,
                    'details': details
                })
            
            # Sort by score descending
            scored_templates.sort(key=lambda x: x['score'], reverse=True)
            
            # Apply pagination
            total_results = len(scored_templates)
            total_pages = max(1, (total_results + page_size - 1) // page_size)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + limit
            
            paged_templates = scored_templates[start_idx:end_idx]
            
            # Build recommendations
            recommendations = []
            for item in paged_templates:
                template = item['template']
                details = item['details']
                
                # Generate match reasons
                reasons = self._generate_match_reasons(details, photo_analysis)
                
                rec = TemplateRecommendation(
                    template_id=str(template.id),
                    name=template.name,
                    match_score=round(item['score'], 2),
                    match_reasons=reasons,
                    match_details={
                        'color_match': round(details['color_match'], 2),
                        'mood_match': round(details['mood_match'], 2),
                        'event_match': round(details['event_match'], 2),
                        'popularity': round(details['popularity'], 2)
                    },
                    preview_url=getattr(template, 'preview_url', None) or f"/templates/{template.id}/preview",
                    thumbnail=template.thumbnail.url if getattr(template, 'thumbnail', None) else f"/templates/{template.id}/thumb.jpg",
                    style=self._map_animation_to_style(template.animation_type),
                    plan_required=template.plan.code
                )
                recommendations.append(rec.to_dict())
            
            result = {
                'recommendations': recommendations,
                'personalization_factors': {
                    'photo_based': photo_analysis is not None,
                    'color_analysis': photo_analysis is not None and 'colors' in photo_analysis,
                    'mood_detection': photo_analysis is not None and 'mood' in photo_analysis
                },
                'total_available': total_available,
                'page': page,
                'total_pages': total_pages
            }
            
            # Cache and return
            self._set_cache(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f"Template recommendation failed: {e}")
            if self.mock_mode:
                return self._get_mock_recommendations(event_type, limit)
            raise self.handle_error(e, "template recommendation")
    
    def recommend_styles(
        self,
        colors: Optional[List[str]] = None,
        mood: Optional[Dict[str, Any]] = None,
        event_type: str = 'WEDDING'
    ) -> List[Dict[str, Any]]:
        """Recommend design styles based on photo analysis.
        
        Args:
            colors: List of hex color codes from photo analysis.
            mood: Detected mood dictionary with 'primary' and 'attributes'.
            event_type: Type of event for suitability checking.
            
        Returns:
            List of style recommendations with confidence scores.
        """
        try:
            # Check cache
            cache_key = self._get_cache_key(
                'style_recommendations',
                str(colors) if colors else 'no_colors',
                str(mood) if mood else 'no_mood',
                event_type
            )
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            recommendations = []
            
            for style_key, profile in STYLE_PROFILES.items():
                score = self._calculate_style_score(
                    style_key, profile, colors, mood, event_type
                )
                
                # Generate reason
                reasons = self._generate_style_reasons(
                    style_key, profile, colors, mood, event_type, score
                )
                
                recommendations.append(StyleRecommendation(
                    style_key=style_key,
                    name=profile['name'],
                    confidence=round(score, 2),
                    description=profile['description'],
                    color_palette=profile['primary_colors'],
                    font_recommendations=self._get_fonts_for_style(profile['font_style']),
                    elements=profile['decoration_elements'],
                    suitable_events=profile['suitable_events']
                ).to_dict())
            
            # Sort by confidence
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Cache results
            self._set_cache(cache_key, recommendations, CACHE_TIMEOUT_STYLES)
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Style recommendation failed: {e}")
            return []
    
    def _calculate_style_score(
        self,
        style_key: str,
        profile: Dict[str, Any],
        colors: Optional[List[str]],
        mood: Optional[Dict[str, Any]],
        event_type: str
    ) -> float:
        """Calculate match score for a style profile.
        
        Args:
            style_key: Style identifier.
            profile: Style profile dictionary.
            colors: List of hex colors.
            mood: Mood dictionary.
            event_type: Event type.
            
        Returns:
            Style match score (0-1).
        """
        score = 0.0
        
        # Color matching (40% of score)
        color_score = 0.0
        if colors:
            for color in colors[:5]:  # Top 5 colors
                closest, distance = find_closest_color(color, profile['primary_colors'])
                color_score += (1 - distance) * 0.2
            color_score = min(color_score, 1.0)
        else:
            color_score = DEFAULT_NEUTRAL_SCORE
        
        # Mood matching (40% of score)
        mood_score = 0.0
        if mood and 'primary' in mood:
            primary_mood = mood['primary'].lower()
            if primary_mood in profile['moods']:
                mood_score = 0.8 + (0.2 * mood.get('confidence', 0.5))
            elif mood.get('attributes'):
                # Check secondary moods
                for attr, conf in mood.get('attributes', {}).items():
                    if attr.lower() in profile['moods']:
                        mood_score = max(mood_score, conf * 0.6)
        
        if mood_score == 0:
            mood_score = DEFAULT_NEUTRAL_SCORE
        
        # Event type matching (20% of score)
        event_score = 1.0 if event_type in profile['suitable_events'] else 0.3
        
        # Calculate final score
        final_score = (
            0.40 * color_score +
            0.40 * mood_score +
            0.20 * event_score
        )
        
        return min(final_score, MAX_SCORE)
    
    def _generate_style_reasons(
        self,
        style_key: str,
        profile: Dict[str, Any],
        colors: Optional[List[str]],
        mood: Optional[Dict[str, Any]],
        event_type: str,
        score: float
    ) -> List[str]:
        """Generate human-readable reasons for style recommendation.
        
        Args:
            style_key: Style identifier.
            profile: Style profile.
            colors: List of colors.
            mood: Mood dictionary.
            event_type: Event type.
            score: Match score.
            
        Returns:
            List of reason strings.
        """
        reasons = []
        
        if mood and 'primary' in mood:
            primary_mood = mood['primary'].lower()
            if primary_mood in profile['moods']:
                reasons.append(f"Matches your {primary_mood} aesthetic")
        
        if event_type in profile['suitable_events']:
            reasons.append(f"Perfect for {event_type.lower()} celebrations")
        
        if not reasons:
            reasons.append(profile['description'])
        
        return reasons
    
    def get_similar_templates(
        self,
        template_id: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """Get similar templates based on attributes.
        
        Finds templates with similar:
        - Animation type/style
        - Plan level
        - Color scheme
        
        Args:
            template_id: ID of the reference template.
            limit: Maximum number of similar templates to return.
            
        Returns:
            List of similar template dictionaries.
        """
        try:
            Template = get_template_model()
            
            # Get the reference template (optimized query)
            try:
                reference = Template.objects.select_related('plan', 'category').get(id=template_id)
            except Template.DoesNotExist:
                self.logger.warning(f"Template {template_id} not found")
                return []
            
            # Find similar templates (optimized query)
            similar = Template.objects.filter(
                is_active=True
            ).exclude(
                id=template_id
            ).filter(
                Q(animation_type=reference.animation_type) |
                Q(plan=reference.plan)
            ).select_related('plan', 'category').order_by('-use_count')[:limit * 2]
            
            results = []
            for template in similar:
                # Calculate actual similarity
                score = self._calculate_similarity(reference, template)
                results.append({
                    'template_id': str(template.id),
                    'name': template.name,
                    'thumbnail': template.thumbnail.url if getattr(template, 'thumbnail', None) else None,
                    'similarity_score': round(score, 2),
                    'animation_type': template.animation_type,
                    'plan': template.plan.code
                })
            
            # Sort by similarity score and limit
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Get similar templates failed: {e}")
            return []
    
    def get_trending_templates(
        self,
        event_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get currently trending templates.
        
        Trending is determined by:
        - Use count (number of invitations created)
        - Recent activity (within last 30 days)
        - Overall popularity
        
        Args:
            event_type: Optional filter by event type.
            limit: Maximum number of templates to return.
            
        Returns:
            List of trending template dictionaries.
        """
        # Check cache
        cache_key = self._get_cache_key('trending', event_type or 'all', limit)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            Template = get_template_model()
            
            # Get templates with highest use count (optimized query)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            templates = Template.objects.filter(
                is_active=True
            ).select_related('plan').annotate(
                recent_count=Count('id', filter=Q(updated_at__gte=thirty_days_ago))
            )
            
            if event_type:
                templates = templates.filter(category__code=event_type.upper())
            
            # Order by use count and recent activity
            templates = templates.order_by('-use_count', '-updated_at')[:limit * 2]
            
            results = []
            for template in templates:
                # Calculate trend score
                trend_score = self.calculate_popularity_score(template)
                results.append({
                    'template_id': str(template.id),
                    'name': template.name,
                    'thumbnail': template.thumbnail.url if getattr(template, 'thumbnail', None) else None,
                    'preview_url': getattr(template, 'preview_url', None),
                    'trend_score': round(trend_score, 2),
                    'use_count': template.use_count or 0,
                    'plan': template.plan.code,
                    'style': self._map_animation_to_style(template.animation_type)
                })
            
            # Sort by trend score and limit
            results.sort(key=lambda x: x['trend_score'], reverse=True)
            final_results = results[:limit]
            
            # Cache results
            self._set_cache(cache_key, final_results, CACHE_TIMEOUT_TRENDING)
            return final_results
            
        except Exception as e:
            self.logger.error(f"Get trending templates failed: {e}")
            return []
    
    def calculate_content_score(
        self,
        template: Any,
        photo_analysis: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate content match score between template and photo analysis.
        
        Compares template colors to photo colors and template mood to photo mood.
        
        Args:
            template: Template model instance.
            photo_analysis: Photo analysis results with colors and mood.
            
        Returns:
            Score between 0.0 and 1.0.
        """
        if not photo_analysis:
            return DEFAULT_NEUTRAL_SCORE
        
        score = 0.0
        
        # Color comparison
        template_colors = getattr(template, 'theme_colors', None) or {}
        photo_colors = photo_analysis.get('colors', [])
        
        if template_colors and photo_colors:
            # Extract hex values from template theme colors
            template_hexes = [
                template_colors.get('primary', '#FFFFFF'),
                template_colors.get('secondary', '#FFFFFF'),
                template_colors.get('accent', '#FFFFFF')
            ]
            
            # Compare with photo colors
            color_matches = []
            for photo_color in photo_colors[:3]:  # Top 3 photo colors
                photo_hex = photo_color.get('color', photo_color.get('hex', '#FFFFFF'))
                closest, distance = find_closest_color(photo_hex, template_hexes)
                color_matches.append(1 - distance)
            
            color_score = sum(color_matches) / len(color_matches) if color_matches else DEFAULT_NEUTRAL_SCORE
        else:
            color_score = DEFAULT_NEUTRAL_SCORE
        
        # Mood comparison
        template_style = self._map_animation_to_style(template.animation_type)
        photo_mood = photo_analysis.get('mood', {})
        
        if photo_mood and template_style:
            primary_mood = photo_mood.get('primary', '').lower()
            style_profile = STYLE_PROFILES.get(template_style, {})
            
            if primary_mood in style_profile.get('moods', []):
                mood_score = 0.7 + (0.3 * photo_mood.get('confidence', 0.5))
            else:
                mood_score = 0.3
        else:
            mood_score = DEFAULT_NEUTRAL_SCORE
        
        # Combined content score (60% color, 40% mood)
        score = 0.6 * color_score + 0.4 * mood_score
        
        return min(max(score, MIN_SCORE), MAX_SCORE)
    
    def calculate_popularity_score(self, template: Any) -> float:
        """Calculate popularity score based on usage stats.
        
        Factors:
        - Use count (normalized)
        - Recent usage (recency bonus)
        - Overall engagement
        
        Args:
            template: Template model instance.
            
        Returns:
            Popularity score between 0.0 and 1.0.
        """
        # Base score from use count (logarithmic scale to prevent dominance)
        use_count = getattr(template, 'use_count', None) or 0
        use_score = min(use_count / 100.0, 1.0)  # Cap at 100 uses
        
        # Recency bonus (if recently updated/used)
        recency_bonus = 0.0
        updated_at = getattr(template, 'updated_at', None)
        if updated_at:
            days_since_update = (timezone.now() - updated_at).days
            if days_since_update < 7:
                recency_bonus = 0.2
            elif days_since_update < 30:
                recency_bonus = 0.1
        
        # Combine scores
        score = use_score * 0.8 + recency_bonus
        
        return min(max(score, MIN_SCORE), MAX_SCORE)
    
    def calculate_match_score(
        self,
        template: Any,
        photo_analysis: Optional[Dict[str, Any]],
        event_type: str
    ) -> Tuple[float, Dict[str, float]]:
        """Calculate comprehensive match score for a template.
        
        Args:
            template: Template model instance.
            photo_analysis: Photo analysis results.
            event_type: Event type to match against.
            
        Returns:
            Tuple of (final_score, score_breakdown).
        """
        scores = {
            'color_match': 0.0,
            'mood_match': 0.0,
            'event_match': 0.0,
            'popularity': 0.0,
        }
        
        # Color match: Compare template colors to photo colors
        if photo_analysis and 'colors' in photo_analysis:
            template_colors = getattr(template, 'theme_colors', None) or {}
            photo_colors = photo_analysis.get('colors', [])
            
            if template_colors and photo_colors:
                template_hexes = [
                    template_colors.get('primary', '#FFFFFF'),
                    template_colors.get('secondary', '#FFFFFF'),
                    template_colors.get('accent', '#FFFFFF'),
                    template_colors.get('background', '#FFFFFF')
                ]
                
                # Calculate average color similarity
                similarities = []
                for photo_color in photo_colors[:3]:
                    photo_hex = photo_color.get('color', photo_color.get('hex', '#FFFFFF'))
                    _, distance = find_closest_color(photo_hex, template_hexes)
                    similarities.append(1 - distance)
                
                scores['color_match'] = sum(similarities) / len(similarities) if similarities else DEFAULT_NEUTRAL_SCORE
            else:
                scores['color_match'] = DEFAULT_NEUTRAL_SCORE
        else:
            scores['color_match'] = DEFAULT_NEUTRAL_SCORE
        
        # Mood match: Check if template mood matches photo mood
        if photo_analysis and 'mood' in photo_analysis:
            template_style = self._map_animation_to_style(template.animation_type)
            photo_mood = photo_analysis.get('mood', {})
            primary_mood = photo_mood.get('primary', '').lower()
            
            style_profile = STYLE_PROFILES.get(template_style, {})
            style_moods = [m.lower() for m in style_profile.get('moods', [])]
            
            if primary_mood in style_moods:
                scores['mood_match'] = 0.7 + (0.3 * photo_mood.get('confidence', 0.5))
            elif photo_mood.get('attributes'):
                # Check for partial matches
                for attr, conf in photo_mood.get('attributes', {}).items():
                    if attr.lower() in style_moods:
                        scores['mood_match'] = max(scores['mood_match'], conf * 0.7)
            
            if scores['mood_match'] == 0:
                scores['mood_match'] = 0.3  # Low but not zero
        else:
            scores['mood_match'] = DEFAULT_NEUTRAL_SCORE
        
        # Event match: Check if template supports the event type
        template_style = self._map_animation_to_style(template.animation_type)
        style_profile = STYLE_PROFILES.get(template_style, {})
        
        if event_type.upper() in style_profile.get('suitable_events', []):
            scores['event_match'] = 1.0
        else:
            # Partial match if WEDDING (most templates support weddings)
            scores['event_match'] = 0.7 if event_type.upper() == 'WEDDING' else 0.4
        
        # Popularity: Based on historical usage
        scores['popularity'] = self.calculate_popularity_score(template)
        
        # Calculate final weighted score
        final_score = (
            self.WEIGHT_COLOR_MATCH * scores['color_match'] +
            self.WEIGHT_MOOD_MATCH * scores['mood_match'] +
            self.WEIGHT_EVENT_MATCH * scores['event_match'] +
            self.WEIGHT_POPULARITY * scores['popularity']
        )
        
        return final_score, scores
    
    def _get_available_templates(
        self,
        user_plan: str,
        event_type: Optional[str] = None
    ) -> QuerySet:
        """Get templates available to a user based on their plan.
        
        Uses optimized database queries with select_related and prefetch_related.
        
        Args:
            user_plan: User's plan code (BASIC, PREMIUM, LUXURY).
            event_type: Optional event type filter.
            
        Returns:
            QuerySet of Template model instances.
        """
        Template = get_template_model()
        
        allowed_plans = PLAN_HIERARCHY.get(user_plan.upper(), ['BASIC'])
        
        queryset = Template.objects.filter(
            plan__code__in=allowed_plans,
            is_active=True
        ).select_related('plan', 'category').prefetch_related(
            # Add any many-to-many relations that might be needed
        )
        
        if event_type:
            queryset = queryset.filter(
                category__code=event_type.upper()
            )
        
        return queryset
    
    def _generate_match_reasons(
        self,
        scores: Dict[str, float],
        photo_analysis: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate human-readable match reasons based on scores.
        
        Args:
            scores: Score breakdown dictionary.
            photo_analysis: Photo analysis results.
            
        Returns:
            List of match reason strings.
        """
        reasons = []
        
        if photo_analysis:
            if scores['color_match'] > 0.8:
                reasons.append("Matches your photo's color scheme beautifully")
            elif scores['color_match'] > 0.6:
                reasons.append("Complements your photo colors")
            
            if scores['mood_match'] > 0.8:
                mood = photo_analysis.get('mood', {}).get('primary', 'detected')
                reasons.append(f"Perfect for your {mood} aesthetic")
            elif scores['mood_match'] > 0.6:
                reasons.append("Aligns with your photo's mood")
        
        if scores['popularity'] > 0.8:
            reasons.append("Most popular choice this season")
        elif scores['popularity'] > 0.6:
            reasons.append("Highly rated by other couples")
        
        if scores['event_match'] > 0.9:
            reasons.append("Designed specifically for your event type")
        
        # Ensure at least one reason
        if not reasons:
            reasons.append("Elegant design for your special day")
        
        return reasons[:3]  # Limit to 3 reasons
    
    def _map_animation_to_style(self, animation_type: str) -> str:
        """Map template animation type to style profile key.
        
        Args:
            animation_type: Template animation type.
            
        Returns:
            Style profile key.
        """
        mapping = {
            'elegant': 'romantic_elegance',
            'fun': 'fun_vibrant',
            'traditional': 'traditional_royal',
            'modern': 'modern_minimalist',
            'minimal': 'modern_minimalist',
            'bollywood': 'traditional_royal',
            'floral': 'romantic_elegance',
            'royal': 'traditional_royal'
        }
        return mapping.get(animation_type, 'classic_timeless')
    
    def _get_fonts_for_style(self, font_style: str) -> List[str]:
        """Get font recommendations for a font style category.
        
        Args:
            font_style: Font style category.
            
        Returns:
            List of font names.
        """
        fonts = {
            'script': ['Great Vibes', 'Dancing Script', 'Parisienne', 'Allura'],
            'sans-serif': ['Montserrat', 'Open Sans', 'Roboto', 'Lato'],
            'serif': ['Playfair Display', 'Cormorant Garamond', 'Libre Baskerville', 'Bodoni Moda'],
            'display': ['Pacifico', 'Lobster', 'Righteous', 'Bebas Neue'],
            'handwritten': ['Amatic SC', 'Caveat', 'Satisfy', 'Kalam']
        }
        return fonts.get(font_style, ['Open Sans', 'Roboto'])
    
    def _calculate_similarity(
        self,
        template1: Any,
        template2: Any
    ) -> float:
        """Calculate similarity score between two templates.
        
        Args:
            template1: First template.
            template2: Second template.
            
        Returns:
            Similarity score between 0.0 and 1.0.
        """
        score = 0.0
        
        # Same animation type
        if template1.animation_type == template2.animation_type:
            score += 0.4
        
        # Same plan level
        if template1.plan.code == template2.plan.code:
            score += 0.3
        
        # Same category
        if template1.category_id == template2.category_id:
            score += 0.3
        
        return score
    
    def _get_mock_recommendations(
        self,
        event_type: str,
        limit: int
    ) -> Dict[str, Any]:
        """Return mock recommendations for development.
        
        Args:
            event_type: Event type for filtering.
            limit: Number of recommendations.
            
        Returns:
            Mock recommendation response.
        """
        # Adjust scores slightly based on event type
        recommendations = []
        for i, rec in enumerate(MOCK_RECOMMENDATIONS[:limit]):
            rec_copy = rec.copy()
            rec_copy['match_details'] = {
                'color_match': round(rec_copy['match_score'] * 0.95, 2),
                'mood_match': round(rec_copy['match_score'] * 0.88, 2),
                'event_match': 1.0 if i < 3 else 0.7,
                'popularity': round(0.8 + (i * 0.04), 2)
            }
            recommendations.append(rec_copy)
        
        return {
            'recommendations': recommendations,
            'personalization_factors': {
                'photo_based': True,
                'color_analysis': True,
                'mood_detection': True
            },
            'total_available': 20,
            'page': 1,
            'total_pages': 1
        }


# =============================================================================
# Legacy Compatibility
# =============================================================================

def get_recommendation_service() -> RecommendationService:
    """Factory function to get a RecommendationService instance.
    
    Returns:
        RecommendationService instance.
    """
    return RecommendationService()
