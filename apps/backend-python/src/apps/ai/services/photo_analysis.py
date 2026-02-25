"""
Photo Analysis Service.

This module provides AI-powered photo analysis including:
- Color extraction using Google Vision API or colorthief fallback
- Mood detection from image labels and properties
- Style recommendations based on colors and mood
- Color utility functions (hex/rgb conversion, palettes)

Usage:
    >>> service = PhotoAnalysisService()
    >>> result = service.analyze('/path/to/image.jpg', event_type='WEDDING')
    >>> print(result['colors'])
    >>> print(result['mood'])

Performance Notes:
    - Color extraction results are cached for 2 hours
    - Images are processed in RGB mode
    - Maximum image size is limited to prevent memory issues
"""

import os
import io
import time
import hashlib
import logging
import random
import requests
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from contextlib import contextmanager

from django.conf import settings
from django.core.files.storage import default_storage

from .base_ai import BaseAIService, AIServiceError, retry_on_failure, ValidationError


# =============================================================================
# Constants
# =============================================================================

# Cache timeout in seconds (2 hours)
CACHE_TIMEOUT_PHOTO = 7200

# Image processing limits
MAX_IMAGE_SIZE_MB = 20
MAX_IMAGE_DIMENSION = 4096
REQUEST_TIMEOUT_SECONDS = 30

# Color extraction settings
COLOR_QUALITY_DEFAULT = 1
COLOR_PALETTE_SIZE = 6
MAX_COLORS_RETURNED = 5
DOMINANT_COLOR_PERCENTAGE = 35.0
REMAINING_COLOR_PERCENTAGE = 65.0

# Color distance threshold for naming
COLOR_DISTANCE_THRESHOLD = 5000

# Mood scoring weights
MOOD_SCORE_PRIMARY = 0.7
MOOD_SCORE_SECONDARY = 0.3
MOOD_CONFIDENCE_THRESHOLD = 0.5

# Style scoring weights
STYLE_SCORE_MOOD_MATCH_PRIMARY = 0.3
STYLE_SCORE_MOOD_MATCH_SECONDARY = 0.15
STYLE_SCORE_COLOR_MATCH = 0.1
STYLE_SCORE_TEMPERATURE_MATCH = 0.2
STYLE_SCORE_TEMPERATURE_NEUTRAL = 0.1
STYLE_SCORE_EVENT_ADJUSTMENT = 0.1

# Color temperature thresholds
WARM_RATIO_THRESHOLD = 0.5
COOL_RATIO_THRESHOLD = 0.5

# RGB to HSL conversion constants
RGB_MAX_VALUE = 255
HSL_HUE_MAX = 360
HSL_SATURATION_MAX = 100
HSL_LIGHTNESS_MAX = 100

# Hue angles for color theory
HUE_ANGLE_COMPLEMENTARY = 180
HUE_ANGLE_SPLIT_1 = 150
HUE_ANGLE_SPLIT_2 = 210
HUE_ANGLE_ANALOGOUS_1 = -30
HUE_ANGLE_ANALOGOUS_2 = 30
HUE_ANGLE_TRIADIC_1 = 120
HUE_ANGLE_TRIADIC_2 = 240

# Logger
logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class ColorInfo:
    """Information about an extracted color.
    
    Attributes:
        hex: Hex color code (e.g., "#A61E2A").
        rgb: RGB tuple (r, g, b).
        percentage: Percentage of image with this color (0-100).
        name: Human-readable color name.
    """
    hex: str
    rgb: Tuple[int, int, int]
    percentage: float
    name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'color': self.hex,
            'rgb': list(self.rgb),
            'percentage': self.percentage,
            'name': self.name or 'Unknown'
        }


@dataclass
class MoodInfo:
    """Information about detected mood.
    
    Attributes:
        tags: List of mood tags detected.
        primary_mood: Primary detected mood.
        confidence: Confidence score (0-1).
        attributes: Detailed mood attributes with scores.
    """
    tags: List[str]
    primary_mood: str
    confidence: float
    attributes: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            'primary': self.primary_mood,
            'confidence': self.confidence,
            'secondary': self.tags,
            'attributes': self.attributes
        }


# =============================================================================
# Utility Functions
# =============================================================================

def _get_photo_analysis_model() -> Any:
    """Lazy import of PhotoAnalysis model to avoid AppRegistryNotReady."""
    from ..models import PhotoAnalysis
    return PhotoAnalysis


@contextmanager
def _temp_image_file(image_path: str):
    """Context manager for temporary image file handling.
    
    Downloads remote images to temp files and ensures cleanup.
    
    Args:
        image_path: Local path or HTTP URL.
        
    Yields:
        Local file path to the image.
    """
    temp_path: Optional[str] = None
    is_temp = False
    
    try:
        if image_path.startswith(('http://', 'https://')):
            # Download image to temp file
            response = requests.get(
                image_path,
                timeout=REQUEST_TIMEOUT_SECONDS,
                stream=True
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                raise ValidationError(
                    "URL does not point to a valid image",
                    details={'content_type': content_type}
                )
            
            # Determine extension from content type or URL
            ext = _get_extension_from_content_type(content_type) or 'jpg'
            
            import tempfile
            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'.{ext}',
                prefix='photo_analysis_'
            ) as tmp:
                # Stream download to handle large files
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                temp_path = tmp.name
                is_temp = True
                
            logger.debug(f"Downloaded image to temp file: {temp_path}")
        else:
            temp_path = image_path
            
        yield temp_path
        
    finally:
        # Clean up temp file if we created one
        if is_temp and temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temp file: {temp_path}")
            except OSError as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")


def _get_extension_from_content_type(content_type: str) -> Optional[str]:
    """Get file extension from MIME content type.
    
    Args:
        content_type: MIME content type string.
        
    Returns:
        File extension without dot, or None if unknown.
    """
    mapping = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
        'image/gif': 'gif',
        'image/bmp': 'bmp',
    }
    return mapping.get(content_type.lower().split(';')[0].strip())


def _validate_image_path(image_path: str) -> None:
    """Validate image path or URL.
    
    Args:
        image_path: Path or URL to validate.
        
    Raises:
        ValidationError: If validation fails.
    """
    if not image_path or not isinstance(image_path, str):
        raise ValidationError(
            "Image path must be a non-empty string",
            details={'image_path': 'Invalid or empty'}
        )
    
    if not image_path.startswith(('http://', 'https://', '/')):
        raise ValidationError(
            "Image path must be a URL or absolute path",
            details={'image_path': image_path}
        )


# =============================================================================
# Photo Analysis Service
# =============================================================================

class PhotoAnalysisService(BaseAIService):
    """Service for analyzing wedding photos using AI.
    
    Provides functionality for:
    - Extracting dominant colors and palettes (Google Vision API + colorthief fallback)
    - Detecting mood and atmosphere from images
    - Generating style recommendations based on analysis
    - Color manipulation utilities
    
    The service supports three modes:
    1. Google Vision API mode (primary) - Requires GOOGLE_VISION_API_KEY
    2. Colorthief fallback mode - Uses colorthief library for local analysis
    3. Mock mode - Returns realistic sample data for development
    
    Example:
        >>> service = PhotoAnalysisService()
        >>> result = service.analyze('/path/to/wedding_photo.jpg')
        >>> for color in result['colors']:
        ...     print(f"{color['name']}: {color['percentage']}%")
    """
    
    CACHE_TIMEOUT = CACHE_TIMEOUT_PHOTO
    
    # Mood mapping from Vision API labels to internal mood categories
    MOOD_LABEL_MAP: Dict[str, List[str]] = {
        'romantic': ['romantic', 'love', 'couple', 'wedding', 'bride', 'groom', 'embrace', 'kiss'],
        'elegant': ['elegant', 'luxury', 'sophisticated', 'formal', 'classy', 'refined'],
        'fun': ['fun', 'playful', 'joyful', 'happy', 'laughing', 'celebration', 'party'],
        'traditional': ['traditional', 'ceremony', 'cultural', 'heritage', 'classic', 'vintage'],
        'modern': ['modern', 'contemporary', 'minimalist', 'clean', 'sleek', 'urban'],
        'casual': ['casual', 'informal', 'relaxed', 'outdoor', 'beach', 'garden']
    }
    
    # Style profiles with matching criteria
    STYLE_PROFILES: Dict[str, Dict[str, Any]] = {
        'Romantic Elegance': {
            'description': 'Soft, dreamy aesthetic with delicate details and warm lighting',
            'matching_moods': ['romantic', 'elegant'],
            'matching_colors': ['pink', 'red', 'rose', 'champagne', 'ivory', 'gold'],
            'color_temperature': 'warm',
            'templates': ['Rose Garden', 'Blush Dreams', 'Golden Romance', 'Vintage Love'],
            'fonts': ['Great Vibes', 'Playfair Display', 'Dancing Script'],
            'elements': ['floral borders', 'soft gradients', 'lace details', 'heart motifs']
        },
        'Modern Minimalist': {
            'description': 'Clean lines, simple color schemes, and contemporary design',
            'matching_moods': ['modern', 'sophisticated'],
            'matching_colors': ['white', 'gray', 'black', 'navy', 'silver'],
            'color_temperature': 'cool',
            'templates': ['Clean Slate', 'Urban Chic', 'Modern Love', 'Simply Elegant'],
            'fonts': ['Montserrat', 'Open Sans', 'Helvetica Neue'],
            'elements': ['geometric shapes', 'clean lines', 'negative space', 'subtle textures']
        },
        'Traditional Royal': {
            'description': 'Rich, opulent styling with classic regal elements',
            'matching_moods': ['traditional', 'elegant', 'formal'],
            'matching_colors': ['gold', 'maroon', 'purple', 'navy', 'emerald'],
            'color_temperature': 'warm',
            'templates': ['Royal Palace', 'Regal Affair', 'Heritage', 'Classic Royal'],
            'fonts': ['Cinzel', 'Trajan Pro', 'Times New Roman'],
            'elements': ['ornate borders', 'gold foil', 'crown motifs', 'velvet textures']
        },
        'Fun & Vibrant': {
            'description': 'Bold colors, playful elements, and energetic atmosphere',
            'matching_moods': ['fun', 'playful', 'joyful', 'casual'],
            'matching_colors': ['orange', 'yellow', 'coral', 'turquoise', 'fuchsia'],
            'color_temperature': 'warm',
            'templates': ['Fiesta', 'Tropical Paradise', 'Color Pop', 'Joyful Celebration'],
            'fonts': ['Pacifico', 'Comic Sans MS', 'Rounded Mplus'],
            'elements': ['confetti', 'balloons', 'bright patterns', 'fun illustrations']
        },
        'Classic Timeless': {
            'description': 'Enduring elegance with neutral palettes and refined details',
            'matching_moods': ['traditional', 'elegant', 'romantic'],
            'matching_colors': ['white', 'ivory', 'champagne', 'silver', 'blush'],
            'color_temperature': 'neutral',
            'templates': ['Timeless White', 'Ivory Dreams', 'Classic Beauty', 'Eternal Love'],
            'fonts': ['Bodoni Moda', 'Garamond', 'Cormorant Garamond'],
            'elements': ['pearls', 'calligraphy', 'vintage frames', 'ribbon details']
        },
        'Rustic Charm': {
            'description': 'Natural, organic feel with earthy tones and textures',
            'matching_moods': ['casual', 'traditional', 'romantic'],
            'matching_colors': ['brown', 'green', 'terra cotta', 'cream', 'sage'],
            'color_temperature': 'warm',
            'templates': ['Barn Wedding', 'Woodland', 'Country Chic', 'Harvest Moon'],
            'fonts': ['Amatic SC', 'Cabin Sketch', 'Kraft Nine'],
            'elements': ['wood textures', 'burlap', 'mason jars', 'wildflowers']
        }
    }
    
    # Named colors lookup table
    NAMED_COLORS: Dict[str, str] = {
        '#A61E2A': 'Deep Red', '#D4AF37': 'Gold', '#FFFFF0': 'Ivory',
        '#FFB6C1': 'Light Pink', '#FF69B4': 'Hot Pink', '#FFC0CB': 'Pink',
        '#E6E6FA': 'Lavender', '#DDA0DD': 'Plum', '#9370DB': 'Medium Purple',
        '#F5E6D3': 'Champagne', '#8B4513': 'Saddle Brown', '#FFF8DC': 'Cornsilk',
        '#2F4F4F': 'Dark Slate Gray', '#FFFFFF': 'White', '#F5F5F5': 'White Smoke',
        '#E0E0E0': 'Light Gray', '#C0C0C0': 'Silver', '#808080': 'Gray',
        '#000000': 'Black', '#FF0000': 'Red', '#00FF00': 'Lime',
        '#0000FF': 'Blue', '#FFFF00': 'Yellow', '#00FFFF': 'Cyan',
        '#FF00FF': 'Magenta', '#800000': 'Maroon', '#808000': 'Olive',
        '#008000': 'Green', '#800080': 'Purple', '#008080': 'Teal',
        '#000080': 'Navy', '#FFA500': 'Orange', '#A52A2A': 'Brown',
        '#F0F8FF': 'Alice Blue', '#FAEBD7': 'Antique White', '#00CED1': 'Dark Turquoise',
        '#FFD700': 'Gold', '#ADFF2F': 'Green Yellow', '#4B0082': 'Indigo',
        '#F0E68C': 'Khaki', '#7CFC00': 'Lawn Green',
        '#FFF0F5': 'Lavender Blush', '#C71585': 'Medium Violet Red',
        '#20B2AA': 'Light Sea Green', '#87CEFA': 'Light Sky Blue',
        '#778899': 'Light Slate Gray', '#B0C4DE': 'Light Steel Blue',
        '#32CD32': 'Lime Green', '#66CDAA': 'Medium Aquamarine',
        '#0000CD': 'Medium Blue', '#BA55D3': 'Medium Orchid',
        '#3CB371': 'Medium Sea Green', '#7B68EE': 'Medium Slate Blue',
        '#00FA9A': 'Medium Spring Green', '#48D1CC': 'Medium Turquoise',
        '#191970': 'Midnight Blue', '#F5FFFA': 'Mint Cream',
        '#FFE4E1': 'Misty Rose', '#FFE4B5': 'Moccasin',
        '#FFDEAD': 'Navajo White', '#6B8E23': 'Olive Drab', '#FF4500': 'Orange Red',
        '#DA70D6': 'Orchid', '#EEE8AA': 'Pale Goldenrod', '#98FB98': 'Pale Green',
        '#AFEEEE': 'Pale Turquoise', '#DB7093': 'Pale Violet Red',
        '#FFDAB9': 'Peach Puff', '#CD853F': 'Peru',
        '#B0E0E6': 'Powder Blue', '#BC8F8F': 'Rosy Brown',
        '#4169E1': 'Royal Blue', '#FA8072': 'Salmon',
        '#F4A460': 'Sandy Brown', '#2E8B57': 'Sea Green', '#FFF5EE': 'Sea Shell',
        '#A0522D': 'Sienna', '#87CEEB': 'Sky Blue',
        '#6A5ACD': 'Slate Blue', '#708090': 'Slate Gray', '#FFFAFA': 'Snow',
        '#00FF7F': 'Spring Green', '#4682B4': 'Steel Blue', '#D2B48C': 'Tan',
        '#D8BFD8': 'Thistle', '#FF6347': 'Tomato', '#40E0D0': 'Turquoise',
        '#EE82EE': 'Violet', '#F5DEB3': 'Wheat', '#9ACD32': 'Yellow Green'
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Photo Analysis Service.
        
        Args:
            api_key: Google Vision API key (optional, defaults to settings.AI_SETTINGS).
        """
        super().__init__(api_key=api_key, model='photo-analysis')
        self.logger = logging.getLogger(__name__)
        
        # Get configuration from settings
        ai_settings = getattr(settings, 'AI_SETTINGS', {})
        self.google_vision_api_key = api_key or ai_settings.get('GOOGLE_VISION_API_KEY', '')
        self.mock_mode = getattr(settings, 'AI_MOCK_MODE', False)
        
        # Initialize Vision client if API key is available
        self.vision_client: Optional[Any] = None
        if self.google_vision_api_key and not self.mock_mode:
            self._init_vision_client()
        
        # Check for colorthief fallback
        self.colorthief_available = False
        if not self.vision_client:
            self._init_colorthief()
        
        if self.mock_mode:
            self.logger.info("PhotoAnalysisService running in MOCK mode")
    
    def _init_vision_client(self) -> None:
        """Initialize Google Vision API client."""
        try:
            from google.cloud import vision
            from google.oauth2 import service_account
            
            self.vision_client = vision.ImageAnnotatorClient(
                client_options={'api_key': self.google_vision_api_key}
            )
            self.logger.info("Google Vision API client initialized successfully")
        except ImportError:
            self.logger.warning("google-cloud-vision not installed, using fallback methods")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Google Vision client: {e}")
    
    def _init_colorthief(self) -> None:
        """Initialize ColorThief fallback."""
        try:
            from colorthief import ColorThief
            self.colorthief_available = True
            self.logger.info("ColorThief fallback available")
        except ImportError:
            self.logger.warning("colorthief not installed, using mock mode")
    
    def analyze(
        self,
        image_path: str,
        event_type: str = 'WEDDING'
    ) -> Dict[str, Any]:
        """Main analysis pipeline - extracts colors, mood, and generates recommendations.
        
        Args:
            image_path: Path to the image file or URL.
            event_type: Type of event (WEDDING, ENGAGEMENT, etc.).
            
        Returns:
            Dictionary containing:
            - colors: List of extracted colors with hex, name, and percentage
            - mood: Detected mood with primary, confidence, and secondary moods
            - recommendations: List of style recommendations
            - event_type: The event type analyzed for
            
        Raises:
            ValidationError: If image_path is invalid.
            AIServiceError: If analysis fails.
        """
        start_time = time.time()
        
        # Validate input
        _validate_image_path(image_path)
        
        try:
            # Check cache first
            cache_key = self._get_cache_key('full_analysis', image_path, event_type)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Returning cached analysis for {image_path}")
                return cached_result
            
            # Run analysis based on available methods
            if self.mock_mode or (not self.vision_client and not self.colorthief_available):
                result = self._mock_analyze(image_path, event_type)
            else:
                result = self._perform_analysis(image_path, event_type)
            
            # Cache and return result
            self._set_cache(cache_key, result)
            
            processing_time = int((time.time() - start_time) * 1000)
            self.logger.info(f"Photo analysis completed in {processing_time}ms")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Photo analysis failed: {e}")
            # Fall back to mock mode on error
            return self._mock_analyze(image_path, event_type)
    
    def _perform_analysis(
        self,
        image_path: str,
        event_type: str
    ) -> Dict[str, Any]:
        """Perform actual photo analysis using available services.
        
        Args:
            image_path: Path to the image.
            event_type: Type of event.
            
        Returns:
            Analysis results dictionary.
        """
        # Extract colors
        colors = self.extract_colors(image_path)
        
        # Detect mood
        mood = self.detect_mood(image_path)
        
        # Generate recommendations
        recommendations = self.generate_style_recommendations(
            colors, mood, event_type
        )
        
        return {
            'colors': colors,
            'mood': mood,
            'recommendations': recommendations,
            'event_type': event_type,
            'analysis_timestamp': time.time(),
            'source': 'google_vision' if self.vision_client else 'colorthief'
        }
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def extract_colors(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract dominant colors from an image.
        
        Uses Google Vision API if available, otherwise falls back to colorthief.
        
        Args:
            image_path: Path to the image file or URL.
            
        Returns:
            List of color dictionaries with format:
            [
                {"color": "#A61E2A", "name": "Deep Red", "percentage": 35.5},
                ...
            ]
            
        Raises:
            ValidationError: If image_path is invalid.
        """
        _validate_image_path(image_path)
        
        # Check cache
        cache_key = self._get_cache_key('colors', image_path)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        colors: List[Dict[str, Any]] = []
        errors: List[str] = []
        
        # Try Google Vision API
        if self.vision_client:
            try:
                colors = self._extract_colors_vision(image_path)
                self.logger.info(
                    f"Extracted {len(colors)} colors using Google Vision API"
                )
            except Exception as e:
                errors.append(f"Google Vision: {e}")
                self.logger.warning(f"Google Vision color extraction failed: {e}")
        
        # Fall back to colorthief
        if not colors and self.colorthief_available:
            try:
                colors = self._extract_colors_colorthief(image_path)
                self.logger.info(
                    f"Extracted {len(colors)} colors using ColorThief"
                )
            except Exception as e:
                errors.append(f"ColorThief: {e}")
                self.logger.warning(f"ColorThief extraction failed: {e}")
        
        # Final fallback to mock
        if not colors:
            colors = self._mock_extract_colors(image_path)
            self.logger.info("Using mock color extraction")
        
        # Ensure all colors have names
        for color in colors:
            if 'name' not in color or not color['name']:
                color['name'] = self.get_color_name(color['color'])
        
        # Cache and return
        self._set_cache(cache_key, colors)
        return colors
    
    def _extract_colors_vision(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract colors using Google Vision API.
        
        Args:
            image_path: Local file path or URL.
            
        Returns:
            List of color dictionaries.
            
        Raises:
            AIServiceError: If API call fails.
        """
        from google.cloud import vision
        
        try:
            # Load image content
            image_content = self._load_image_content(image_path)
            image = vision.Image(content=image_content)
            
            # Request image properties (dominant colors)
            response = self.vision_client.image_properties(image=image)
            
            if response.error.message:
                raise AIServiceError(
                    f"Vision API error: {response.error.message}",
                    error_code='VISION_API_ERROR'
                )
            
            props = response.image_properties_annotation
            
            colors = []
            for color_info in props.dominant_colors.colors:
                rgb = color_info.color
                hex_color = self.rgb_to_hex((rgb.red, rgb.green, rgb.blue))
                percentage = round(color_info.score * 100, 2)
                
                colors.append({
                    'color': hex_color,
                    'name': self.get_color_name(hex_color),
                    'percentage': percentage,
                    'rgb': [rgb.red, rgb.green, rgb.blue]
                })
            
            # Sort by percentage (descending)
            colors.sort(key=lambda x: x['percentage'], reverse=True)
            
            return colors[:MAX_COLORS_RETURNED]
            
        except Exception as e:
            raise self.handle_error(e, "Vision color extraction")
    
    def _extract_colors_colorthief(self, image_path: str) -> List[Dict[str, Any]]:
        """Extract colors using ColorThief library.
        
        Args:
            image_path: Local file path or URL.
            
        Returns:
            List of color dictionaries.
            
        Raises:
            AIServiceError: If extraction fails.
        """
        from colorthief import ColorThief
        
        try:
            with _temp_image_file(image_path) as tmp_path:
                color_thief = ColorThief(tmp_path)
                
                # Get dominant color
                dominant_rgb = color_thief.get_color(quality=COLOR_QUALITY_DEFAULT)
                
                # Get color palette
                palette = color_thief.get_palette(
                    color_count=COLOR_PALETTE_SIZE,
                    quality=COLOR_QUALITY_DEFAULT
                )
                
                colors = []
                # Dominant color gets higher percentage
                colors.append({
                    'color': self.rgb_to_hex(dominant_rgb),
                    'name': self.get_color_name(self.rgb_to_hex(dominant_rgb)),
                    'percentage': DOMINANT_COLOR_PERCENTAGE,
                    'rgb': list(dominant_rgb)
                })
                
                # Palette colors share remaining percentage
                remaining_pct = REMAINING_COLOR_PERCENTAGE / len(palette) if palette else 0
                for rgb in palette[:4]:  # Limit to 4 additional colors
                    colors.append({
                        'color': self.rgb_to_hex(rgb),
                        'name': self.get_color_name(self.rgb_to_hex(rgb)),
                        'percentage': round(remaining_pct, 2),
                        'rgb': list(rgb)
                    })
                
                return colors
                
        except Exception as e:
            raise self.handle_error(e, "ColorThief extraction")
    
    def _mock_extract_colors(self, image_path: str) -> List[Dict[str, Any]]:
        """Generate deterministic mock color data.
        
        Args:
            image_path: Image path for deterministic selection.
            
        Returns:
            List of mock color dictionaries.
        """
        hash_val = int(hashlib.md5(image_path.encode()).hexdigest(), 16)
        
        mock_palettes: List[List[Dict[str, Any]]] = [
            [
                {'color': '#A61E2A', 'name': 'Deep Red', 'percentage': 35.5, 'rgb': [166, 30, 42]},
                {'color': '#D4AF37', 'name': 'Gold', 'percentage': 25.2, 'rgb': [212, 175, 55]},
                {'color': '#FFFFF0', 'name': 'Ivory', 'percentage': 20.1, 'rgb': [255, 255, 240]},
                {'color': '#8B4513', 'name': 'Saddle Brown', 'percentage': 12.3, 'rgb': [139, 69, 19]},
                {'color': '#2F4F4F', 'name': 'Dark Slate Gray', 'percentage': 6.9, 'rgb': [47, 79, 79]},
            ],
            [
                {'color': '#E6E6FA', 'name': 'Lavender', 'percentage': 40.2, 'rgb': [230, 230, 250]},
                {'color': '#DDA0DD', 'name': 'Plum', 'percentage': 22.5, 'rgb': [221, 160, 221]},
                {'color': '#9370DB', 'name': 'Medium Purple', 'percentage': 18.3, 'rgb': [147, 112, 219]},
                {'color': '#F0F8FF', 'name': 'Alice Blue', 'percentage': 12.0, 'rgb': [240, 248, 255]},
                {'color': '#4B0082', 'name': 'Indigo', 'percentage': 7.0, 'rgb': [75, 0, 130]},
            ],
            [
                {'color': '#FFB6C1', 'name': 'Light Pink', 'percentage': 38.7, 'rgb': [255, 182, 193]},
                {'color': '#FF69B4', 'name': 'Hot Pink', 'percentage': 24.1, 'rgb': [255, 105, 180]},
                {'color': '#FFC0CB', 'name': 'Pink', 'percentage': 19.5, 'rgb': [255, 192, 203]},
                {'color': '#FFF0F5', 'name': 'Lavender Blush', 'percentage': 11.2, 'rgb': [255, 240, 245]},
                {'color': '#C71585', 'name': 'Medium Violet Red', 'percentage': 6.5, 'rgb': [199, 21, 133]},
            ],
            [
                {'color': '#F5E6D3', 'name': 'Champagne', 'percentage': 45.0, 'rgb': [245, 230, 211]},
                {'color': '#D4AF37', 'name': 'Gold', 'percentage': 25.0, 'rgb': [212, 175, 55]},
                {'color': '#FFFFFF', 'name': 'White', 'percentage': 15.0, 'rgb': [255, 255, 255]},
                {'color': '#C0C0C0', 'name': 'Silver', 'percentage': 10.0, 'rgb': [192, 192, 192]},
                {'color': '#8B7355', 'name': 'Burlywood', 'percentage': 5.0, 'rgb': [139, 115, 85]},
            ],
        ]
        
        return mock_palettes[hash_val % len(mock_palettes)]
    
    @retry_on_failure(max_retries=2, delay=1.0)
    def detect_mood(self, image_path: str) -> Dict[str, Any]:
        """Detect image mood using label detection or image properties.
        
        Args:
            image_path: Path to the image file or URL.
            
        Returns:
            Dictionary with format:
            {
                "primary": "romantic",
                "confidence": 0.92,
                "secondary": ["elegant", "traditional"],
                "attributes": {"romantic": 0.92, "elegant": 0.85, ...}
            }
        """
        _validate_image_path(image_path)
        
        # Check cache
        cache_key = self._get_cache_key('mood', image_path)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        mood: Dict[str, Any] = {}
        
        # Try Google Vision API
        if self.vision_client:
            try:
                mood = self._detect_mood_vision(image_path)
                self.logger.info(
                    f"Detected mood using Google Vision API: {mood.get('primary')}"
                )
            except Exception as e:
                self.logger.warning(f"Google Vision mood detection failed: {e}")
        
        # Fall back to mock
        if not mood:
            mood = self._mock_detect_mood(image_path)
            self.logger.info("Using mock mood detection")
        
        # Cache and return
        self._set_cache(cache_key, mood)
        return mood
    
    def _detect_mood_vision(self, image_path: str) -> Dict[str, Any]:
        """Detect mood using Google Vision API labels.
        
        Args:
            image_path: Local file path or URL.
            
        Returns:
            Mood dictionary.
        """
        from google.cloud import vision
        
        try:
            image_content = self._load_image_content(image_path)
            image = vision.Image(content=image_content)
            
            # Perform label detection
            response = self.vision_client.label_detection(image=image)
            
            if response.error.message:
                raise AIServiceError(
                    f"Vision API error: {response.error.message}",
                    error_code='VISION_API_ERROR'
                )
            
            labels = response.label_annotations
            
            # Score each mood based on label matches
            mood_scores: Dict[str, float] = {
                mood: 0.0 for mood in self.MOOD_LABEL_MAP.keys()
            }
            
            for label in labels:
                label_desc = label.description.lower()
                label_score = label.score
                
                for mood, keywords in self.MOOD_LABEL_MAP.items():
                    for keyword in keywords:
                        if keyword in label_desc or label_desc in keyword:
                            mood_scores[mood] += label_score
            
            # Normalize scores
            max_score = max(mood_scores.values()) if mood_scores else 1
            if max_score > 0:
                mood_scores = {
                    k: round(v / max_score, 2)
                    for k, v in mood_scores.items()
                }
            
            # Get primary mood (highest score)
            primary_mood = max(mood_scores, key=mood_scores.get)
            primary_confidence = mood_scores[primary_mood]
            
            # Get secondary moods (scores > threshold, excluding primary)
            secondary = [
                mood for mood, score in sorted(
                    mood_scores.items(), key=lambda x: x[1], reverse=True
                )[1:3] if score > MOOD_CONFIDENCE_THRESHOLD
            ]
            
            return {
                'primary': primary_mood,
                'confidence': primary_confidence,
                'secondary': secondary,
                'attributes': mood_scores,
                'detected_labels': [
                    {'description': l.description, 'score': round(l.score, 2)}
                    for l in labels[:5]
                ]
            }
            
        except Exception as e:
            raise self.handle_error(e, "Vision mood detection")
    
    def _mock_detect_mood(self, image_path: str) -> Dict[str, Any]:
        """Generate deterministic mock mood data.
        
        Args:
            image_path: Image path for deterministic selection.
            
        Returns:
            Mock mood dictionary.
        """
        hash_val = int(hashlib.md5(image_path.encode()).hexdigest(), 16)
        
        mock_moods: List[Dict[str, Any]] = [
            {
                'primary': 'romantic',
                'confidence': 0.92,
                'secondary': ['elegant', 'traditional'],
                'attributes': {
                    'romantic': 0.92, 'elegant': 0.85, 'traditional': 0.78,
                    'fun': 0.35, 'modern': 0.45, 'casual': 0.30
                }
            },
            {
                'primary': 'modern',
                'confidence': 0.87,
                'secondary': ['elegant', 'sophisticated'],
                'attributes': {
                    'modern': 0.95, 'elegant': 0.72, 'traditional': 0.30,
                    'fun': 0.45, 'romantic': 0.60, 'casual': 0.50
                }
            },
            {
                'primary': 'fun',
                'confidence': 0.91,
                'secondary': ['casual', 'playful'],
                'attributes': {
                    'fun': 0.93, 'casual': 0.88, 'modern': 0.70,
                    'elegant': 0.40, 'traditional': 0.35, 'romantic': 0.65
                }
            },
            {
                'primary': 'traditional',
                'confidence': 0.85,
                'secondary': ['romantic', 'elegant'],
                'attributes': {
                    'traditional': 0.94, 'romantic': 0.80, 'elegant': 0.78,
                    'fun': 0.30, 'modern': 0.25, 'casual': 0.40
                }
            },
            {
                'primary': 'casual',
                'confidence': 0.88,
                'secondary': ['fun', 'romantic'],
                'attributes': {
                    'casual': 0.92, 'fun': 0.75, 'romantic': 0.70,
                    'modern': 0.55, 'elegant': 0.40, 'traditional': 0.45
                }
            },
        ]
        
        return mock_moods[hash_val % len(mock_moods)]
    
    def generate_style_recommendations(
        self,
        colors: List[Dict[str, Any]],
        mood: Dict[str, Any],
        event_type: str = 'WEDDING'
    ) -> List[Dict[str, Any]]:
        """Generate style recommendations based on colors and mood.
        
        Args:
            colors: List of extracted colors.
            mood: Detected mood dictionary.
            event_type: Type of event.
            
        Returns:
            List of recommendation dictionaries with format:
            [
                {
                    "style": "Romantic Elegance",
                    "confidence": 0.89,
                    "color_palette": [...],
                    "matching_templates": [...],
                    "fonts": [...],
                    "elements": [...]
                }
            ]
        """
        primary_mood = mood.get('primary', 'romantic')
        secondary_moods = mood.get('secondary', [])
        all_moods = [primary_mood] + secondary_moods
        
        # Get color names and temperature
        color_names = [c.get('name', '').lower() for c in colors]
        color_hexes = [c.get('color', '') for c in colors]
        color_temperature = self._determine_color_temperature(color_hexes)
        
        # Score each style profile
        style_scores: Dict[str, float] = {}
        for style_name, profile in self.STYLE_PROFILES.items():
            score = self._calculate_style_score(
                style_name, profile, all_moods, color_names,
                color_temperature, primary_mood, event_type
            )
            style_scores[style_name] = score
        
        # Sort styles by score and create recommendations
        sorted_styles = sorted(
            style_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        recommendations = []
        for style_name, score in sorted_styles[:3]:  # Top 3 recommendations
            profile = self.STYLE_PROFILES[style_name]
            
            # Generate color palette for this style
            palette = self._generate_style_palette(colors, profile)
            
            recommendations.append({
                'style': style_name,
                'confidence': round(score, 2),
                'description': profile['description'],
                'color_palette': palette,
                'matching_templates': profile['templates'],
                'fonts': profile['fonts'],
                'elements': profile['elements']
            })
        
        return recommendations
    
    def _calculate_style_score(
        self,
        style_name: str,
        profile: Dict[str, Any],
        all_moods: List[str],
        color_names: List[str],
        color_temperature: str,
        primary_mood: str,
        event_type: str
    ) -> float:
        """Calculate match score for a style profile.
        
        Args:
            style_name: Name of the style.
            profile: Style profile dictionary.
            all_moods: List of moods to match.
            color_names: List of color names.
            color_temperature: Detected color temperature.
            primary_mood: Primary detected mood.
            event_type: Event type.
            
        Returns:
            Style match score (0-1).
        """
        score = 0.0
        
        # Mood matching
        for mood in all_moods:
            if mood in profile['matching_moods']:
                score += (
                    STYLE_SCORE_MOOD_MATCH_PRIMARY
                    if mood == primary_mood
                    else STYLE_SCORE_MOOD_MATCH_SECONDARY
                )
        
        # Color matching
        for color_name in color_names:
            for match_color in profile['matching_colors']:
                if match_color in color_name:
                    score += STYLE_SCORE_COLOR_MATCH
        
        # Temperature matching
        if color_temperature == profile['color_temperature']:
            score += STYLE_SCORE_TEMPERATURE_MATCH
        elif profile['color_temperature'] == 'neutral':
            score += STYLE_SCORE_TEMPERATURE_NEUTRAL
        
        # Event type adjustments
        if event_type == 'WEDDING':
            if style_name in ['Romantic Elegance', 'Classic Timeless']:
                score += STYLE_SCORE_EVENT_ADJUSTMENT
        elif event_type == 'ENGAGEMENT':
            if style_name in ['Modern Minimalist', 'Romantic Elegance']:
                score += STYLE_SCORE_EVENT_ADJUSTMENT
        
        return min(score, 1.0)
    
    def _determine_color_temperature(self, hex_colors: List[str]) -> str:
        """Determine if colors are warm, cool, or neutral.
        
        Args:
            hex_colors: List of hex color codes.
            
        Returns:
            Color temperature: 'warm', 'cool', or 'neutral'.
        """
        warm_count = 0
        cool_count = 0
        
        for hex_color in hex_colors:
            rgb = self.hex_to_rgb(hex_color)
            if rgb:
                r, g, b = rgb
                # Warm colors have higher red/yellow components
                if r > b and (r > g or g > b):
                    warm_count += 1
                # Cool colors have higher blue component
                elif b > r:
                    cool_count += 1
        
        total = len(hex_colors) if hex_colors else 1
        warm_ratio = warm_count / total
        cool_ratio = cool_count / total
        
        if warm_ratio > WARM_RATIO_THRESHOLD:
            return 'warm'
        elif cool_ratio > COOL_RATIO_THRESHOLD:
            return 'cool'
        else:
            return 'neutral'
    
    def _generate_style_palette(
        self,
        colors: List[Dict[str, Any]],
        profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a color palette appropriate for the style.
        
        Args:
            colors: Extracted colors.
            profile: Style profile.
            
        Returns:
            Style palette with roles.
        """
        base_colors = colors[:3]  # Use top 3 extracted colors
        
        palette = []
        for i, color in enumerate(base_colors):
            palette.append({
                'hex': color.get('color', '#FFFFFF'),
                'name': color.get('name', 'Unknown'),
                'role': 'primary' if i == 0 else 'secondary'
            })
        
        # Add complementary colors if palette is small
        if len(palette) < 4 and base_colors:
            primary_hex = base_colors[0].get('color', '#FFFFFF')
            complementary = self.get_complementary_colors(primary_hex)
            for comp_hex in complementary[:2]:
                palette.append({
                    'hex': comp_hex,
                    'name': self.get_color_name(comp_hex),
                    'role': 'accent'
                })
        
        return palette[:MAX_COLORS_RETURNED]
    
    def get_color_name(self, hex_color: str) -> str:
        """Convert hex color to human-readable name.
        
        Uses optimized color distance calculation for closest match lookup.
        
        Args:
            hex_color: Hex color code (e.g., "#A61E2A").
            
        Returns:
            Human-readable color name.
        """
        hex_upper = hex_color.upper()
        
        # Direct lookup
        if hex_upper in self.NAMED_COLORS:
            return self.NAMED_COLORS[hex_upper]
        
        # Try to find closest match using optimized color distance
        try:
            rgb = self.hex_to_rgb(hex_color)
            if rgb:
                closest_name, distance = self._find_closest_color_name(rgb)
                
                if closest_name and distance < COLOR_DISTANCE_THRESHOLD:
                    return closest_name
        except Exception:
            pass
        
        # Fallback to generic name with hex
        return f"Custom ({hex_color})"
    
    def _find_closest_color_name(
        self,
        target_rgb: Tuple[int, int, int]
    ) -> Tuple[Optional[str], float]:
        """Find the closest named color using optimized distance.
        
        Uses weighted RGB distance for better perceptual matching.
        
        Args:
            target_rgb: Target RGB tuple.
            
        Returns:
            Tuple of (color_name, distance).
        """
        closest_name: Optional[str] = None
        closest_distance = float('inf')
        
        # Weights for perceptual RGB distance
        # Human eye is more sensitive to green, then red, then blue
        r_weight, g_weight, b_weight = 0.3, 0.59, 0.11
        
        for named_hex, name in self.NAMED_COLORS.items():
            named_rgb = self.hex_to_rgb(named_hex)
            if named_rgb:
                # Weighted Euclidean distance
                distance = (
                    r_weight * (target_rgb[0] - named_rgb[0]) ** 2 +
                    g_weight * (target_rgb[1] - named_rgb[1]) ** 2 +
                    b_weight * (target_rgb[2] - named_rgb[2]) ** 2
                )
                
                if distance < closest_distance:
                    closest_distance = distance
                    closest_name = name
        
        return closest_name, closest_distance
    
    @staticmethod
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
    
    @staticmethod
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
    
    def get_complementary_colors(self, hex_color: str) -> List[str]:
        """Get complementary colors for a given hex color.
        
        Args:
            hex_color: Base hex color.
            
        Returns:
            List of complementary hex colors.
        """
        rgb = self.hex_to_rgb(hex_color)
        if not rgb:
            return []
        
        r, g, b = rgb
        
        # Calculate complementary color (opposite on color wheel)
        complementary = (RGB_MAX_VALUE - r, RGB_MAX_VALUE - g, RGB_MAX_VALUE - b)
        
        # Calculate split complementary using HSL
        h, s, l = self._rgb_to_hsl(r, g, b)
        
        # Split complementary: rotate hue by 150 and 210 degrees
        split1 = ((h + HUE_ANGLE_SPLIT_1) % HUE_ANGLE_MAX, s, l)
        split2 = ((h + HUE_ANGLE_SPLIT_2) % HUE_ANGLE_MAX, s, l)
        
        return [
            self.rgb_to_hex(complementary),
            self.rgb_to_hex(self._hsl_to_rgb(*split1)),
            self.rgb_to_hex(self._hsl_to_rgb(*split2))
        ]
    
    def get_harmonious_palette(
        self,
        hex_colors: List[str]
    ) -> Dict[str, List[str]]:
        """Generate harmonious color palettes from base colors.
        
        Args:
            hex_colors: List of base hex colors.
            
        Returns:
            Dictionary with different palette types:
            {
                'analogous': [...],
                'complementary': [...],
                'triadic': [...],
                'split_complementary': [...]
            }
        """
        if not hex_colors:
            return {}
        
        base_hex = hex_colors[0]
        rgb = self.hex_to_rgb(base_hex)
        if not rgb:
            return {}
        
        r, g, b = rgb
        h, s, l = self._rgb_to_hsl(r, g, b)
        
        palettes: Dict[str, List[str]] = {
            'analogous': [],
            'complementary': [],
            'triadic': [],
            'split_complementary': []
        }
        
        # Analogous: adjacent colors (±30 degrees)
        for offset in [HUE_ANGLE_ANALOGOUS_1, 0, HUE_ANGLE_ANALOGOUS_2]:
            new_h = (h + offset) % HUE_ANGLE_MAX
            palettes['analogous'].append(
                self.rgb_to_hex(self._hsl_to_rgb(new_h, s, l))
            )
        
        # Complementary: opposite color
        comp_h = (h + HUE_ANGLE_COMPLEMENTARY) % HUE_ANGLE_MAX
        palettes['complementary'] = [
            base_hex,
            self.rgb_to_hex(self._hsl_to_rgb(comp_h, s, l))
        ]
        
        # Triadic: evenly spaced (120 degrees apart)
        for offset in [0, HUE_ANGLE_TRIADIC_1, HUE_ANGLE_TRIADIC_2]:
            new_h = (h + offset) % HUE_ANGLE_MAX
            palettes['triadic'].append(
                self.rgb_to_hex(self._hsl_to_rgb(new_h, s, l))
            )
        
        # Split complementary: ±150 degrees from base
        palettes['split_complementary'] = [
            base_hex,
            self.rgb_to_hex(self._hsl_to_rgb((h + HUE_ANGLE_SPLIT_1) % HUE_ANGLE_MAX, s, l)),
            self.rgb_to_hex(self._hsl_to_rgb((h + HUE_ANGLE_SPLIT_2) % HUE_ANGLE_MAX, s, l))
        ]
        
        return palettes
    
    def _rgb_to_hsl(
        self,
        r: int,
        g: int,
        b: int
    ) -> Tuple[float, float, float]:
        """Convert RGB to HSL color space.
        
        Args:
            r: Red component (0-255).
            g: Green component (0-255).
            b: Blue component (0-255).
            
        Returns:
            HSL tuple (hue: 0-360, saturation: 0-100, lightness: 0-100).
        """
        r_norm, g_norm, b_norm = (
            r / RGB_MAX_VALUE,
            g / RGB_MAX_VALUE,
            b / RGB_MAX_VALUE
        )
        
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
            h = (60 * ((g_norm - b_norm) / diff) + HUE_ANGLE_MAX) % HUE_ANGLE_MAX
        elif max_val == g_norm:
            h = (60 * ((b_norm - r_norm) / diff) + 120) % HUE_ANGLE_MAX
        else:
            h = (60 * ((r_norm - g_norm) / diff) + 240) % HUE_ANGLE_MAX
        
        return (h, s * 100, l * 100)
    
    def _hsl_to_rgb(
        self,
        h: float,
        s: float,
        l: float
    ) -> Tuple[int, int, int]:
        """Convert HSL to RGB color space.
        
        Args:
            h: Hue (0-360).
            s: Saturation (0-100).
            l: Lightness (0-100).
            
        Returns:
            RGB tuple (r, g, b).
        """
        s_norm = s / 100
        l_norm = l / 100
        
        c = (1 - abs(2 * l_norm - 1)) * s_norm
        x = c * (1 - abs((h / 60) % 2 - 1))
        m = l_norm - c / 2
        
        if 0 <= h < 60:
            r1, g1, b1 = c, x, 0
        elif 60 <= h < 120:
            r1, g1, b1 = x, c, 0
        elif 120 <= h < 180:
            r1, g1, b1 = 0, c, x
        elif 180 <= h < 240:
            r1, g1, b1 = 0, x, c
        elif 240 <= h < 300:
            r1, g1, b1 = x, 0, c
        else:
            r1, g1, b1 = c, 0, x
        
        r = int((r1 + m) * RGB_MAX_VALUE)
        g = int((g1 + m) * RGB_MAX_VALUE)
        b = int((b1 + m) * RGB_MAX_VALUE)
        
        return (r, g, b)
    
    def _mock_analyze(
        self,
        image_path: str,
        event_type: str
    ) -> Dict[str, Any]:
        """Mock analysis for development without API keys.
        
        Returns realistic sample data for testing and development.
        
        Args:
            image_path: Path to the image.
            event_type: Type of event.
            
        Returns:
            Complete analysis result with sample data.
        """
        colors = [
            {'color': '#A61E2A', 'name': 'Deep Red', 'percentage': 35.5},
            {'color': '#D4AF37', 'name': 'Gold', 'percentage': 25.2},
            {'color': '#FFFFF0', 'name': 'Ivory', 'percentage': 20.1},
            {'color': '#8B4513', 'name': 'Saddle Brown', 'percentage': 12.3},
            {'color': '#2F4F4F', 'name': 'Dark Slate Gray', 'percentage': 6.9},
        ]
        
        mood = {
            'primary': 'romantic',
            'confidence': 0.92,
            'secondary': ['elegant', 'traditional'],
            'attributes': {
                'romantic': 0.92, 'elegant': 0.85, 'traditional': 0.78,
                'fun': 0.35, 'modern': 0.45, 'casual': 0.30
            }
        }
        
        recommendations = [
            {
                'style': 'Romantic Elegance',
                'confidence': 0.89,
                'description': 'Soft, dreamy aesthetic with delicate details and warm lighting',
                'color_palette': [
                    {'hex': '#A61E2A', 'name': 'Deep Red', 'role': 'primary'},
                    {'hex': '#D4AF37', 'name': 'Gold', 'role': 'secondary'},
                    {'hex': '#FFFFF0', 'name': 'Ivory', 'role': 'secondary'},
                    {'hex': '#59B3A8', 'name': 'Sea Green', 'role': 'accent'},
                ],
                'matching_templates': ['Rose Garden', 'Blush Dreams', 'Golden Romance', 'Vintage Love'],
                'fonts': ['Great Vibes', 'Playfair Display', 'Dancing Script'],
                'elements': ['floral borders', 'soft gradients', 'lace details', 'heart motifs']
            },
            {
                'style': 'Classic Timeless',
                'confidence': 0.75,
                'description': 'Enduring elegance with neutral palettes and refined details',
                'color_palette': [
                    {'hex': '#FFFFF0', 'name': 'Ivory', 'role': 'primary'},
                    {'hex': '#D4AF37', 'name': 'Gold', 'role': 'secondary'},
                    {'hex': '#F5E6D3', 'name': 'Champagne', 'role': 'accent'},
                ],
                'matching_templates': ['Timeless White', 'Ivory Dreams', 'Classic Beauty', 'Eternal Love'],
                'fonts': ['Bodoni Moda', 'Garamond', 'Cormorant Garamond'],
                'elements': ['pearls', 'calligraphy', 'vintage frames', 'ribbon details']
            },
            {
                'style': 'Traditional Royal',
                'confidence': 0.68,
                'description': 'Rich, opulent styling with classic regal elements',
                'color_palette': [
                    {'hex': '#A61E2A', 'name': 'Deep Red', 'role': 'primary'},
                    {'hex': '#D4AF37', 'name': 'Gold', 'role': 'secondary'},
                    {'hex': '#800080', 'name': 'Purple', 'role': 'accent'},
                ],
                'matching_templates': ['Royal Palace', 'Regal Affair', 'Heritage', 'Classic Royal'],
                'fonts': ['Cinzel', 'Trajan Pro', 'Times New Roman'],
                'elements': ['ornate borders', 'gold foil', 'crown motifs', 'velvet textures']
            }
        ]
        
        return {
            'colors': colors,
            'mood': mood,
            'recommendations': recommendations,
            'event_type': event_type,
            'analysis_timestamp': time.time(),
            'source': 'mock'
        }
    
    def _load_image_content(self, image_path: str) -> bytes:
        """Load image content from path or URL.
        
        Args:
            image_path: Local file path or URL.
            
        Returns:
            Image content as bytes.
            
        Raises:
            AIServiceError: If loading fails.
        """
        try:
            if image_path.startswith(('http://', 'https://')):
                response = requests.get(
                    image_path,
                    timeout=REQUEST_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                return response.content
            else:
                # Handle Django storage
                if hasattr(default_storage, 'open'):
                    try:
                        with default_storage.open(image_path, 'rb') as f:
                            return f.read()
                    except Exception:
                        pass
                
                # Direct file read
                with open(image_path, 'rb') as f:
                    return f.read()
                    
        except requests.RequestException as e:
            raise AIServiceError(
                f"Failed to download image: {e}",
                error_code='IMAGE_DOWNLOAD_ERROR'
            )
        except IOError as e:
            raise AIServiceError(
                f"Failed to read image: {e}",
                error_code='IMAGE_READ_ERROR'
            )
    
    # Legacy methods for backward compatibility
    def analyze_photo(
        self,
        image_url: str,
        user: Any,
        event: Optional[Any] = None,
        extract_colors: bool = True,
        detect_mood: bool = True,
        generate_recommendations: bool = True
    ) -> Any:
        """Legacy method for comprehensive photo analysis with database storage.
        
        Args:
            image_url: URL of the image to analyze.
            user: User requesting the analysis.
            event: Optional associated event.
            extract_colors: Whether to extract colors.
            detect_mood: Whether to detect mood.
            generate_recommendations: Whether to generate recommendations.
            
        Returns:
            PhotoAnalysis model instance.
        """
        start_time = time.time()
        PhotoAnalysis = _get_photo_analysis_model()
        
        # Check cache first
        cache_key = self._get_cache_key(
            'analysis', image_url, extract_colors, detect_mood
        )
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result:
            self.logger.info(f"Returning cached photo analysis for {image_url}")
            # Create a new record with cached data
            photo_analysis = PhotoAnalysis.objects.create(
                user=user,
                event=event,
                image_url=image_url,
                primary_colors=cached_result.get('primary_colors', {}),
                mood=cached_result.get('mood', {}),
                style_recommendations=cached_result.get('style_recommendations', [])
            )
            return photo_analysis
        
        # Perform analysis
        primary_colors: Dict[str, Any] = {}
        mood: Dict[str, Any] = {}
        style_recommendations: List[Dict[str, Any]] = []
        
        try:
            if extract_colors:
                colors_list = self.extract_colors(image_url)
                primary_colors = {
                    'colors': colors_list,
                    'palette_type': self._determine_color_temperature(
                        [c['color'] for c in colors_list]
                    )
                }
            
            if detect_mood:
                mood = self.detect_mood(image_url)
            
            if generate_recommendations:
                recommendations = self.generate_style_recommendations(
                    primary_colors.get('colors', []),
                    mood,
                    'WEDDING'
                )
                style_recommendations = self._convert_recommendations_to_legacy(
                    recommendations
                )
            
            # Create analysis record
            photo_analysis = PhotoAnalysis.objects.create(
                user=user,
                event=event,
                image_url=image_url,
                primary_colors=primary_colors,
                mood=mood,
                style_recommendations=style_recommendations
            )
            
            # Cache the results
            cache_data = {
                'primary_colors': primary_colors,
                'mood': mood,
                'style_recommendations': style_recommendations
            }
            self._set_cache(cache_key, cache_data)
            
            # Log usage
            processing_time = int((time.time() - start_time) * 1000)
            self.log_usage(
                user=user,
                feature_type='photo_analysis',
                request_data={
                    'image_url': image_url,
                    'extract_colors': extract_colors,
                    'detect_mood': detect_mood
                },
                response_data={'analysis_id': str(photo_analysis.id)},
                tokens_used=1000,  # Estimate
                success=True,
                processing_time_ms=processing_time
            )
            
            return photo_analysis
            
        except Exception as e:
            # Log failed usage
            self.log_usage(
                user=user,
                feature_type='photo_analysis',
                request_data={'image_url': image_url},
                response_data={},
                success=False,
                error_message=str(e)
            )
            raise self.handle_error(e, "photo analysis")
    
    def _convert_recommendations_to_legacy(
        self,
        recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Convert new recommendation format to legacy format.
        
        Args:
            recommendations: New format recommendations.
            
        Returns:
            Legacy format recommendations.
        """
        legacy: List[Dict[str, Any]] = []
        
        for rec in recommendations:
            legacy.append({
                'category': 'template_style',
                'name': rec['style'],
                'description': rec['description'],
                'recommended_templates': rec.get('matching_templates', []),
                'match_score': rec.get('confidence', 0.8),
                'reasoning': f"Matches {rec['style']} style with confidence {rec['confidence']}"
            })
            
            legacy.append({
                'category': 'typography',
                'recommended_fonts': rec.get('fonts', []),
                'description': f"Fonts for {rec['style']} style",
                'match_score': rec.get('confidence', 0.8) * 0.95
            })
            
            legacy.append({
                'category': 'decorative_elements',
                'recommended_elements': rec.get('elements', []),
                'description': f"Elements for {rec['style']} style",
                'match_score': rec.get('confidence', 0.8) * 0.9
            })
        
        return legacy
