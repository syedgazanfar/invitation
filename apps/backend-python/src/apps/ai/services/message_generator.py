"""
Message Generation Service using OpenAI GPT-4.

This module provides AI-powered message generation for wedding invitations using
OpenAI's GPT-4 API with fallback to GPT-3.5 and mock mode for development.

Features:
- Generate 3 personalized invitation message options in different styles
- Generate wedding hashtags
- Generate smart suggestions for event improvements
- Comprehensive error handling with retry logic
- Token usage tracking and logging
- Response validation and sanitization

Example:
    >>> service = MessageGenerationService()
    >>> result = service.generate_messages({
    ...     'bride_name': 'Jane',
    ...     'groom_name': 'John',
    ...     'event_type': 'WEDDING'
    ... })
    >>> for option in result.generated_options:
    ...     print(option['text'])
"""

import time
import logging
import random
import re
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass

from django.conf import settings

from .base_ai import (
    BaseAIService, AIServiceError, RateLimitError, ValidationError,
    retry_on_failure, validate_string, validate_positive_integer
)

# Try to import OpenAI, handle gracefully if not available
try:
    from openai import OpenAI, APIError, RateLimitError as OpenAIRateLimitError
    from openai.types.chat import ChatCompletion
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None
    APIError = Exception
    OpenAIRateLimitError = Exception
    ChatCompletion = Any


# =============================================================================
# Constants
# =============================================================================

# Cache settings
CACHE_TIMEOUT_MESSAGES = 0  # No cache for message generation - always fresh

# Rate limiting
RATE_LIMIT_REQUESTS_MSG = 30  # per hour for message generation
RATE_LIMIT_WINDOW_MSG = 3600  # 1 hour

# Token settings
MAX_TOKENS_DEFAULT = 500
TEMPERATURE_DEFAULT = 0.8
TOKEN_ESTIMATE_WORD_MULTIPLIER = 1.5
TOKEN_ESTIMATE_BASE = 50

# Message generation settings
MESSAGE_WORD_COUNT_MIN = 50
MESSAGE_WORD_COUNT_MAX = 150
MESSAGE_OPTIONS_COUNT = 3

# Retry settings for OpenAI API
OPENAI_MAX_RETRIES = 3
OPENAI_RETRY_DELAY = 1.0
OPENAI_RETRY_BACKOFF = 2.0
OPENAI_RETRY_MAX_WAIT = 60.0  # Maximum wait between retries

# Validation limits
MAX_NAME_LENGTH = 100
MAX_DETAILS_LENGTH = 2000
MAX_VENUE_LENGTH = 500

# Logger
logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Constants
# =============================================================================

SYSTEM_PROMPT_TEMPLATE = """You are a professional wedding invitation copywriter with 20 years of experience crafting personalized, heartfelt invitation messages for couples around the world.

Your expertise includes:
- Writing messages that capture the couple's unique love story
- Adapting tone and style to match cultural contexts (Indian, Western, Modern)
- Creating messages that balance tradition with personal touches
- Ensuring every message feels authentic and never generic

Guidelines for message quality:
1. Keep messages between {min_words}-{max_words} words each
2. Match tone to the event type and couple's personality
3. Include essential details naturally (names, date, venue if provided)
4. Make it feel personal and heartfelt - avoid clichés
5. Consider cultural context (Indian traditions for Indian weddings)
6. Use the couple's names naturally within the text
7. Each option should have a distinctly different feel while remaining appropriate

Output format:
Provide exactly {num_options} message options labeled as:
OPTION 1 - Traditional & Formal: [message]
OPTION 2 - Warm & Personal: [message]
OPTION 3 - Fun & Modern: [message]

Each message should be complete and ready to use."""

USER_PROMPT_TEMPLATE = """Generate an invitation message for:

Couple: {bride_name} & {groom_name}
Event Type: {event_type}
Cultural Context: {culture}
Desired Tone: {tone}
{optional_fields}

Generate {num_options} options with different styles:
1. Traditional & Formal - respectful, classic wording with cultural elements
2. Warm & Personal - heartfelt, storytelling approach
3. Fun & Modern - lighthearted, contemporary style

Each message should be {min_words}-{max_words} words. Include the couple's names naturally.
Make each option distinctly different in tone and style."""

OPTIONAL_FIELDS_TEMPLATE = """Preferred Style: {style}
Story/Details: {details}
Date: {wedding_date}
Venue: {venue_hint}"""

# Mock message templates for development
MOCK_MESSAGES_WEDDING_INDIAN = {
    'traditional': """With the blessings of our elders and the love of our families, we invite you to celebrate the union of {bride_name} and {groom_name}.

As we embark on this sacred journey of marriage, your presence would honor us greatly. Join us for the joyous festivities as two families become one.

We look forward to celebrating with you.{detail_text}""",
    'warm': """From the moment our eyes met, we knew our souls were destined to be together. {bride_name} and {groom_name} invite you to witness the beginning of our forever.

Our wedding is not just a celebration of our love, but a merging of two hearts, two families, and two stories into one beautiful journey. Your presence will make our day truly special.

Come dance, laugh, and celebrate with us!{detail_text}""",
    'fun': """Finally making it official! {bride_name} and {groom_name} are tying the knot and we want YOU there to celebrate with us!

Expect great food, amazing music, questionable dance moves, and lots of love. Bring your appetite and your dancing shoes - this is going to be a celebration to remember!

Don't forget to RSVP - we need to know how much biryani to order! 🎉{detail_text}"""
}

MOCK_MESSAGES_WEDDING_WESTERN = {
    'traditional': """Together with their families,

{bride_name} and {groom_name}

request the pleasure of your company at their wedding celebration.

Your presence would mean the world to us as we exchange vows and begin our new life together. Please join us for a ceremony followed by dinner and dancing.

We look forward to sharing this special day with you.{detail_text}""",
    'warm': """We've dreamed of this day, and now it's almost here! {bride_name} and {groom_name} invite you to be part of our love story as we say "I do."

From our first date to this moment, every step has led us here. Your friendship and support have meant everything to us, and we can't imagine celebrating without you.

Join us for a day filled with love, laughter, and happily ever after.{detail_text}""",
    'fun': """OMG, we're getting married! 🎉

After all this time, {bride_name} and {groom_name} are finally making it legal! Join us for what promises to be an epic party with cake, cocktails, and questionable dance moves.

When: Our special day
Where: The venue
What to bring: Your awesome self and your party spirit

Warning: There will be cheesy love songs and embarrassing speeches. You don't want to miss it!{detail_text}"""
}


# =============================================================================
# Utility Functions
# =============================================================================

def _get_generated_message_model() -> Any:
    """Lazy import of GeneratedMessage model to avoid AppRegistryNotReady."""
    from ..models import GeneratedMessage
    return GeneratedMessage


def estimate_token_count(text: str) -> int:
    """Estimate token count for OpenAI API.
    
    Uses a more accurate estimation method based on word count
    and character patterns.
    
    Args:
        text: Text to estimate tokens for.
        
    Returns:
        Estimated token count.
    """
    if not text:
        return 0
    
    # Rough estimation: ~4 characters per token for English
    # More accurate than simple word count
    char_count = len(text)
    word_count = len(text.split())
    
    # Blend character and word-based estimates
    char_estimate = char_count / 4
    word_estimate = word_count * 1.3  # Account for punctuation
    
    return int((char_estimate + word_estimate) / 2)


def validate_context(context: Dict[str, Any]) -> None:
    """Validate message generation context.
    
    Args:
        context: Context dictionary to validate.
        
    Raises:
        ValidationError: If validation fails.
    """
    required_fields = ['bride_name', 'groom_name']
    
    for field in required_fields:
        if field not in context or not context[field]:
            raise ValidationError(
                f"Missing required field: {field}",
                details={'field': field, 'error': 'required'}
            )
    
    # Validate string fields
    if 'bride_name' in context:
        validate_string(context['bride_name'], 'bride_name', MAX_NAME_LENGTH)
    if 'groom_name' in context:
        validate_string(context['groom_name'], 'groom_name', MAX_NAME_LENGTH)
    if 'details' in context and context['details']:
        validate_string(context['details'], 'details', MAX_DETAILS_LENGTH)
    if 'venue_hint' in context and context['venue_hint']:
        validate_string(context['venue_hint'], 'venue_hint', MAX_VENUE_LENGTH)


def sanitize_message_text(text: str) -> str:
    """Sanitize generated message text.
    
    Removes excessive whitespace, ensures proper formatting.
    
    Args:
        text: Raw message text.
        
    Returns:
        Sanitized message text.
    """
    if not text:
        return ""
    
    # Remove excessive newlines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Ensure no leading/trailing whitespace on each line
    lines = [line.strip() for line in text.split('\n')]
    
    return '\n'.join(lines)


# =============================================================================
# Message Generation Service
# =============================================================================

class MessageGenerationService(BaseAIService):
    """Service for generating AI-powered wedding invitation messages using OpenAI GPT-4.
    
    This service generates personalized invitation messages with the following features:
    - 3 different message styles per request (traditional, warm, fun)
    - Cultural context awareness (Indian, Western, Modern)
    - Fallback chain: GPT-4 -> GPT-3.5 -> Mock mode
    - Comprehensive error handling and retry logic
    - Token usage tracking and analytics
    
    Attributes:
        client: OpenAI client instance.
        primary_model: Primary OpenAI model (default: gpt-4).
        fallback_model: Fallback model (default: gpt-3.5-turbo).
        mock_mode: Whether to use mock responses instead of API calls.
    """
    
    CACHE_TIMEOUT = CACHE_TIMEOUT_MESSAGES
    RATE_LIMIT_REQUESTS = RATE_LIMIT_REQUESTS_MSG
    RATE_LIMIT_WINDOW = RATE_LIMIT_WINDOW_MSG
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize the message generation service.
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY).
            model: OpenAI model to use (defaults to settings.OPENAI_MODEL).
        """
        super().__init__(api_key=api_key, model=model)
        self.logger = logging.getLogger(__name__)
        
        # Get configuration from settings
        self.api_key = api_key or getattr(settings, 'AI_SETTINGS', {}).get('OPENAI_API_KEY', '')
        self.primary_model = model or getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        self.fallback_model = getattr(settings, 'OPENAI_FALLBACK_MODEL', 'gpt-3.5-turbo')
        self.mock_mode = getattr(settings, 'AI_MOCK_MODE', False) or not self.api_key
        
        # Initialize OpenAI client if not in mock mode
        self.client: Optional[Any] = None
        if not self.mock_mode and OPENAI_AVAILABLE and self.api_key:
            self._init_openai_client()
        elif not OPENAI_AVAILABLE:
            self.logger.warning("OpenAI package not available. Using mock mode.")
            self.mock_mode = True
    
    def _init_openai_client(self) -> None:
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info(
                f"OpenAI client initialized with model: {self.primary_model}"
            )
        except Exception as e:
            self.logger.warning(
                f"Failed to initialize OpenAI client: {e}. Using mock mode."
            )
            self.mock_mode = True
    
    def generate_messages(
        self,
        context: Dict[str, Any],
        style: str = 'romantic',
        num_options: int = MESSAGE_OPTIONS_COUNT,
        user: Optional[Any] = None,
        event: Optional[Any] = None
    ) -> Any:
        """Generate personalized invitation message options using OpenAI GPT-4.
        
        Args:
            context: Dictionary containing message context with keys:
                - bride_name: str - Bride's name
                - groom_name: str - Groom's name
                - event_type: str - Event type (WEDDING, BIRTHDAY, etc.)
                - style: str (optional) - Preferred style override
                - culture: str (optional) - Cultural context (north_indian, south_indian, modern)
                - tone: str (optional) - Message tone (warm, formal, casual, funny)
                - details: str (optional) - Additional details about the couple/story
                - wedding_date: str (optional) - Wedding date string
                - venue_hint: str (optional) - Venue hint to include
            style: Message style preference (romantic, formal, casual, etc.).
            num_options: Number of message options to generate (default: 3).
            user: User requesting generation (for logging and database record).
            event: Associated event (for database record).
            
        Returns:
            GeneratedMessage model instance with:
                - id: UUID of the record
                - context: Original context dictionary
                - generated_options: List of message option dictionaries
                - tokens_used: Number of tokens consumed
                - generation_time_ms: Time taken for generation
                
        Raises:
            ValidationError: If context validation fails.
            RateLimitError: If rate limit exceeded.
            AIServiceError: If generation fails after all retries.
        """
        start_time = time.time()
        
        # Validate context
        validate_context(context)
        validate_positive_integer(num_options, 'num_options')
        
        # Check rate limit if user provided
        if user and not self.check_rate_limit(user, 'message_generation'):
            raise RateLimitError(
                "Rate limit exceeded for message generation. Please try again later.",
                retry_after=RATE_LIMIT_WINDOW_MSG
            )
        
        tokens_used = 0
        success = False
        error_message = ""
        generation_result: Optional[Dict[str, Any]] = None
        generated_message: Optional[Any] = None
        
        try:
            if self.mock_mode:
                # Use mock generation for development
                generation_result = self._mock_generate(context)
                tokens_used = generation_result.get('tokens_used', 0)
                success = True
                self.logger.info("Generated messages using mock mode")
            else:
                # Use OpenAI API
                generation_result = self._generate_with_openai(context)
                tokens_used = generation_result.get('tokens_used', 0)
                success = True
                self.logger.info(
                    f"Generated messages using OpenAI. Tokens: {tokens_used}"
                )
            
            # Format options for the model
            formatted_options = self._format_options(
                generation_result.get('options', []),
                style
            )
            
            # Create database record
            GeneratedMessage = _get_generated_message_model()
            if user:
                generated_message = GeneratedMessage.objects.create(
                    user=user,
                    event=event,
                    context=context,
                    generated_options=formatted_options,
                    style_used=style,
                    tokens_used=tokens_used
                )
            else:
                # Create unsaved instance for return (won't have an ID)
                generated_message = GeneratedMessage(
                    context=context,
                    generated_options=formatted_options,
                    style_used=style,
                    tokens_used=tokens_used
                )
            
            # Attach metadata for views that need it
            generated_message.generation_time_ms = generation_result.get(
                'generation_time_ms', 0
            )
            generated_message.model_used = generation_result.get(
                'model_used', 'mock' if self.mock_mode else 'unknown'
            )
            
            return generated_message
            
        except Exception as e:
            error_message = str(e)
            self.logger.error(f"Message generation failed: {error_message}")
            
            # If API call failed and we're not already in mock mode, try fallback
            if not self.mock_mode and not success:
                return self._fallback_to_mock(
                    context, style, user, event, error_message
                )
            
            raise self.handle_error(e, context="generate_messages")
            
        finally:
            # Log usage
            processing_time_ms = int((time.time() - start_time) * 1000)
            if user:
                self.log_usage(
                    user=user,
                    feature_type='message_generation',
                    request_data=self._sanitize_for_log(context),
                    response_data={'success': success, 'tokens_used': tokens_used},
                    tokens_used=tokens_used,
                    success=success,
                    error_message=error_message,
                    processing_time_ms=processing_time_ms
                )
    
    def _fallback_to_mock(
        self,
        context: Dict[str, Any],
        style: str,
        user: Optional[Any],
        event: Optional[Any],
        original_error: str
    ) -> Any:
        """Fallback to mock generation when API fails.
        
        Args:
            context: Message generation context.
            style: Message style.
            user: User requesting generation.
            event: Associated event.
            original_error: Original API error message.
            
        Returns:
            GeneratedMessage instance with mock data.
        """
        self.logger.info("Attempting fallback to mock mode")
        
        try:
            generation_result = self._mock_generate(context)
            tokens_used = generation_result.get('tokens_used', 0)
            
            # Format options for the model
            formatted_options = self._format_options(
                generation_result.get('options', []),
                style
            )
            
            GeneratedMessage = _get_generated_message_model()
            if user:
                generated_message = GeneratedMessage.objects.create(
                    user=user,
                    event=event,
                    context=context,
                    generated_options=formatted_options,
                    style_used=style,
                    tokens_used=tokens_used
                )
            else:
                generated_message = GeneratedMessage(
                    context=context,
                    generated_options=formatted_options,
                    style_used=style,
                    tokens_used=tokens_used
                )
            
            generated_message.generation_time_ms = generation_result.get(
                'generation_time_ms', 0
            )
            generated_message.model_used = 'mock_fallback'
            
            return generated_message
            
        except Exception as mock_error:
            raise AIServiceError(
                f"API error: {original_error}, Mock error: {mock_error}",
                error_code='ALL_GENERATION_FAILED'
            )
    
    def _format_options(
        self,
        options: List[Dict[str, Any]],
        default_style: str
    ) -> List[Dict[str, Any]]:
        """Format options for database storage.
        
        Args:
            options: Raw options from generation.
            default_style: Default style if not specified.
            
        Returns:
            Formatted options list.
        """
        formatted = []
        style_mapping = {
            '1': 'traditional_formal',
            '2': 'warm_personal',
            '3': 'fun_modern'
        }
        
        for i, opt in enumerate(options):
            text = sanitize_message_text(opt.get('message', ''))
            formatted.append({
                'id': f"opt_{i+1}",
                'text': text,
                'style': opt.get('style', style_mapping.get(str(i+1), default_style)),
                'tone': opt.get('style_name', 'warm'),
                'word_count': len(text.split()) if text else 0
            })
        
        return formatted
    
    def _generate_with_openai(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate messages using OpenAI API with retry logic.
        
        Tries GPT-4 first, then falls back to GPT-3.5 if that fails.
        Implements exponential backoff with jitter for retries.
        
        Args:
            context: Message generation context.
            
        Returns:
            Dictionary with generated options, tokens used, and generation time.
            
        Raises:
            AIServiceError: If all API calls fail.
        """
        start_time = time.time()
        
        if not self.client:
            raise AIServiceError(
                "OpenAI client not initialized",
                error_code='CLIENT_NOT_INITIALIZED'
            )
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(context)
        
        # Try primary model first, then fallback
        models_to_try = [self.primary_model, self.fallback_model]
        last_error: Optional[Exception] = None
        
        for model in models_to_try:
            for attempt in range(OPENAI_MAX_RETRIES):
                try:
                    self.logger.info(
                        f"Attempting generation with model: {model} (attempt {attempt + 1})"
                    )
                    
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=getattr(settings, 'OPENAI_MAX_TOKENS', MAX_TOKENS_DEFAULT),
                        temperature=getattr(settings, 'OPENAI_TEMPERATURE', TEMPERATURE_DEFAULT),
                        n=1
                    )
                    
                    # Validate response
                    options = self._parse_and_validate_response(
                        response.choices[0].message.content
                    )
                    
                    generation_time_ms = int((time.time() - start_time) * 1000)
                    tokens_used = response.usage.total_tokens if response.usage else 0
                    
                    self.logger.info(f"Successfully generated with {model}")
                    
                    return {
                        'options': options,
                        'tokens_used': tokens_used,
                        'generation_time_ms': generation_time_ms,
                        'model_used': model
                    }
                    
                except OpenAIRateLimitError as e:
                    self.logger.warning(f"Rate limit hit for {model}: {e}")
                    last_error = e
                    # Use exponential backoff with jitter
                    if attempt < OPENAI_MAX_RETRIES - 1:
                        wait_time = min(
                            OPENAI_RETRY_DELAY * (OPENAI_RETRY_BACKOFF ** attempt) +
                            random.uniform(0, 1),
                            OPENAI_RETRY_MAX_WAIT
                        )
                        time.sleep(wait_time)
                    continue
                    
                except APIError as e:
                    self.logger.warning(f"API error with {model}: {e}")
                    last_error = e
                    if attempt < OPENAI_MAX_RETRIES - 1:
                        time.sleep(OPENAI_RETRY_DELAY * (OPENAI_RETRY_BACKOFF ** attempt))
                    continue
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error with {model}: {e}")
                    last_error = e
                    if attempt < OPENAI_MAX_RETRIES - 1:
                        time.sleep(OPENAI_RETRY_DELAY)
                    continue
            
            # If we've exhausted retries for this model, try next model
            self.logger.warning(f"Exhausted retries for {model}, trying fallback")
        
        # All models failed
        raise AIServiceError(
            f"All OpenAI models failed. Last error: {last_error}",
            error_code='ALL_MODELS_FAILED'
        )
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the AI.
        
        Returns:
            System prompt string.
        """
        return SYSTEM_PROMPT_TEMPLATE.format(
            min_words=MESSAGE_WORD_COUNT_MIN,
            max_words=MESSAGE_WORD_COUNT_MAX,
            num_options=MESSAGE_OPTIONS_COUNT
        )
    
    def _build_user_prompt(self, context: Dict[str, Any]) -> str:
        """Build the user prompt with context.
        
        Args:
            context: Message context dictionary.
            
        Returns:
            Formatted user prompt string.
        """
        bride_name = context.get('bride_name', '')
        groom_name = context.get('groom_name', '')
        event_type = context.get('event_type', 'WEDDING')
        culture = context.get('culture', 'modern')
        tone = context.get('tone', 'warm')
        
        # Build optional fields section
        optional_parts = []
        if context.get('style'):
            optional_parts.append(f"Preferred Style: {context['style']}")
        if context.get('details'):
            optional_parts.append(f"Story/Details: {context['details']}")
        if context.get('wedding_date'):
            optional_parts.append(f"Date: {context['wedding_date']}")
        if context.get('venue_hint'):
            optional_parts.append(f"Venue: {context['venue_hint']}")
        
        optional_fields = '\n'.join(optional_parts) if optional_parts else ''
        
        return USER_PROMPT_TEMPLATE.format(
            bride_name=bride_name,
            groom_name=groom_name,
            event_type=event_type,
            culture=culture,
            tone=tone,
            optional_fields=optional_fields,
            num_options=MESSAGE_OPTIONS_COUNT,
            min_words=MESSAGE_WORD_COUNT_MIN,
            max_words=MESSAGE_WORD_COUNT_MAX
        )
    
    def _parse_and_validate_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse and validate OpenAI response into structured options.
        
        Args:
            content: Raw response content from OpenAI.
            
        Returns:
            List of validated option dictionaries.
            
        Raises:
            AIServiceError: If response cannot be parsed or is invalid.
        """
        options = self._parse_response(content)
        
        # Validate we have the expected number of options
        if len(options) < MESSAGE_OPTIONS_COUNT:
            self.logger.warning(
                f"Expected {MESSAGE_OPTIONS_COUNT} options, got {len(options)}. "
                "Padding with duplicates."
            )
            # Duplicate first option if needed
            while len(options) < MESSAGE_OPTIONS_COUNT:
                options.append(options[0].copy() if options else {
                    'style': 'generated',
                    'message': 'Please try generating again.',
                    'style_name': 'Generated'
                })
        
        # Validate word counts
        for opt in options:
            message = opt.get('message', '')
            word_count = len(message.split())
            
            if word_count < MESSAGE_WORD_COUNT_MIN:
                self.logger.warning(
                    f"Message too short ({word_count} words, min {MESSAGE_WORD_COUNT_MIN})"
                )
            elif word_count > MESSAGE_WORD_COUNT_MAX * 1.5:  # Allow some leeway
                self.logger.warning(
                    f"Message too long ({word_count} words, max {MESSAGE_WORD_COUNT_MAX})"
                )
            
            opt['word_count'] = word_count
        
        return options[:MESSAGE_OPTIONS_COUNT]
    
    def _parse_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse OpenAI response into structured options.
        
        Extracts the 3 message options from the AI response, handling
        various response formats gracefully.
        
        Args:
            content: Raw response content from OpenAI.
            
        Returns:
            List of dictionaries with 'style' and 'message' keys.
        """
        options = []
        
        # Try to find options using pattern matching
        patterns = [
            # Pattern: OPTION 1 - Style: message
            r'OPTION\s*(\d+)\s*[-–:]\s*([^:\n]+)[:\n](.*?)(?=OPTION\s*\d+|$)',
            # Pattern: 1. Style: message
            r'(?:^|\n)\s*(\d+)\.\s*([^:\n]+)[:\n](.*?)(?=\n\s*\d+\.|$)',
            # Pattern: **Option 1 - Style**: message
            r'\*\*Option\s*(\d+)\s*[-–:]\s*([^*]+)\*\*[:\n]?(.*?)(?=\*\*Option|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
            if len(matches) >= MESSAGE_OPTIONS_COUNT:
                style_mapping = {
                    '1': 'traditional_formal',
                    '2': 'warm_personal',
                    '3': 'fun_modern'
                }
                for i, (num, style_name, message) in enumerate(matches[:MESSAGE_OPTIONS_COUNT]):
                    clean_message = sanitize_message_text(message)
                    
                    options.append({
                        'style': style_mapping.get(num, f'option_{num}'),
                        'message': clean_message,
                        'style_name': style_name.strip()
                    })
                break
        
        # If pattern matching failed, try splitting by double newlines
        if len(options) < MESSAGE_OPTIONS_COUNT:
            sections = re.split(r'\n\s*\n', content.strip())
            if len(sections) >= MESSAGE_OPTIONS_COUNT:
                styles = ['traditional_formal', 'warm_personal', 'fun_modern']
                for i, section in enumerate(sections[:MESSAGE_OPTIONS_COUNT]):
                    # Remove any "Option X" or numbering from the start
                    clean = re.sub(
                        r'^(?:OPTION\s*\d+|\d+\.)\s*[-–:]?\s*',
                        '',
                        section,
                        flags=re.IGNORECASE
                    )
                    clean = re.sub(r'^[^\n]*?[-–:]\s*', '', clean)  # Remove style label
                    options.append({
                        'style': styles[i],
                        'message': sanitize_message_text(clean),
                        'style_name': styles[i].replace('_', ' ').title()
                    })
        
        # If still no options, treat entire content as one option
        if len(options) == 0:
            options = [{
                'style': 'generated',
                'message': sanitize_message_text(content),
                'style_name': 'Generated'
            }]
        
        return options
    
    def _mock_generate(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate mock messages for development.
        
        Returns realistic sample messages based on the provided context,
        allowing development without API keys.
        
        Args:
            context: Message context dictionary.
            
        Returns:
            Dictionary with mock options, token count, and generation time.
        """
        start_time = time.time()
        
        bride_name = context.get('bride_name', 'Bride')
        groom_name = context.get('groom_name', 'Groom')
        event_type = context.get('event_type', 'WEDDING')
        culture = context.get('culture', 'modern')
        details = context.get('details', '')
        
        detail_text = f"\n\n{details}" if details else ""
        
        # Generate context-appropriate messages
        if event_type.upper() == 'WEDDING':
            options = self._get_wedding_mock_messages(
                bride_name, groom_name, culture, detail_text
            )
        elif event_type.upper() == 'BIRTHDAY':
            options = self._get_birthday_mock_messages(
                bride_name, culture
            )
        else:
            options = self._get_generic_mock_messages(
                bride_name, groom_name, event_type
            )
        
        # Calculate word counts
        for opt in options:
            opt['word_count'] = len(opt['message'].split())
        
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        # Estimate tokens
        total_words = sum(opt['word_count'] for opt in options)
        tokens_used = int(total_words * TOKEN_ESTIMATE_WORD_MULTIPLIER) + TOKEN_ESTIMATE_BASE
        
        return {
            'options': options,
            'tokens_used': tokens_used,
            'generation_time_ms': generation_time_ms,
            'model_used': 'mock'
        }
    
    def _get_wedding_mock_messages(
        self,
        bride_name: str,
        groom_name: str,
        culture: str,
        detail_text: str
    ) -> List[Dict[str, Any]]:
        """Get wedding-specific mock messages.
        
        Args:
            bride_name: Bride's name.
            groom_name: Groom's name.
            culture: Cultural context.
            detail_text: Additional details text.
            
        Returns:
            List of message options.
        """
        if 'indian' in culture.lower():
            templates = MOCK_MESSAGES_WEDDING_INDIAN
        else:
            templates = MOCK_MESSAGES_WEDDING_WESTERN
        
        return [
            {
                'style': 'traditional_formal',
                'message': templates['traditional'].format(
                    bride_name=bride_name,
                    groom_name=groom_name,
                    detail_text=detail_text
                ),
                'style_name': 'Traditional & Formal'
            },
            {
                'style': 'warm_personal',
                'message': templates['warm'].format(
                    bride_name=bride_name,
                    groom_name=groom_name,
                    detail_text=detail_text
                ),
                'style_name': 'Warm & Personal'
            },
            {
                'style': 'fun_modern',
                'message': templates['fun'].format(
                    bride_name=bride_name,
                    groom_name=groom_name,
                    detail_text=detail_text
                ),
                'style_name': 'Fun & Modern'
            }
        ]
    
    def _get_birthday_mock_messages(
        self,
        name: str,
        culture: str
    ) -> List[Dict[str, Any]]:
        """Get birthday-specific mock messages.
        
        Args:
            name: Birthday person's name.
            culture: Cultural context.
            
        Returns:
            List of message options.
        """
        traditional = f"""You are cordially invited to celebrate

{name}'s Birthday

Please join us for an elegant evening of dinner, drinks, and celebration as we mark this special milestone.

Your presence would be an honor."""
        
        warm = f"""Come celebrate with us!

We're throwing a birthday party for {name}, and it wouldn't be the same without you.

Good food, great company, and wonderful memories await. Let's make this birthday unforgettable!"""
        
        fun = f"""Party Alert! 🎂🎈

{name} is turning another year fabulous, and we're celebrating in style!

Join us for cake, confetti, and chaos (the good kind). Bring your party spirit and your appetite!

Warning: May contain excessive fun and terrible karaoke."""
        
        return [
            {
                'style': 'traditional_formal',
                'message': traditional,
                'style_name': 'Traditional & Formal'
            },
            {
                'style': 'warm_personal',
                'message': warm,
                'style_name': 'Warm & Personal'
            },
            {
                'style': 'fun_modern',
                'message': fun,
                'style_name': 'Fun & Modern'
            }
        ]
    
    def _get_generic_mock_messages(
        self,
        host_name: str,
        co_host_name: str,
        event_type: str
    ) -> List[Dict[str, Any]]:
        """Get generic event mock messages.
        
        Args:
            host_name: Primary host name.
            co_host_name: Co-host name.
            event_type: Type of event.
            
        Returns:
            List of message options.
        """
        traditional = f"""You are invited to attend

{host_name} and {co_host_name}'s {event_type.title()}

Please join us for an evening of celebration and joy.

Your presence is requested."""
        
        warm = f"""We'd love to see you!

Join {host_name} and {co_host_name} as we celebrate our {event_type.title()}.

It means so much to us to share this special occasion with friends and family.

Hope you can make it!"""
        
        fun = f"""Guess what? It's party time! 🎉

{host_name} and {co_host_name} are hosting an awesome {event_type.title()}, and you're on the guest list!

Come for the fun, stay for the memories. It's going to be legendary!"""
        
        return [
            {
                'style': 'traditional_formal',
                'message': traditional,
                'style_name': 'Traditional & Formal'
            },
            {
                'style': 'warm_personal',
                'message': warm,
                'style_name': 'Warm & Personal'
            },
            {
                'style': 'fun_modern',
                'message': fun,
                'style_name': 'Fun & Modern'
            }
        ]
    
    def generate_hashtags(
        self,
        bride_name: str,
        groom_name: str,
        wedding_date: Optional[str] = None,
        style: str = 'classic',
        count: int = 9
    ) -> Dict[str, Any]:
        """Generate wedding hashtags for the couple.
        
        Creates personalized hashtags using various patterns and styles,
        organized into categories.
        
        Args:
            bride_name: Bride's name.
            groom_name: Groom's name.
            wedding_date: Optional wedding date for year-based hashtags.
            style: Style preference (classic, fun, modern).
            count: Total number of hashtags to generate (default 9).
            
        Returns:
            Dictionary with hashtags organized by category:
            {
                'hashtags': ['#NameWedsName', ...],
                'by_category': {
                    'classic': ['...', '...'],
                    'fun': ['...', '...'],
                    'trending': ['...', '...']
                },
                'top_pick': '#BestHashtag'
            }
        """
        # Clean names for hashtag use
        bride_clean = re.sub(r'[^\w]', '', bride_name.split()[0])
        groom_clean = re.sub(r'[^\w]', '', groom_name.split()[0])
        
        # Extract year from date if provided
        year = ''
        if wedding_date:
            try:
                if isinstance(wedding_date, str):
                    year_match = re.search(r'\b(20\d{2})\b', wedding_date)
                    if year_match:
                        year = year_match.group(1)
                elif isinstance(wedding_date, datetime):
                    year = str(wedding_date.year)
            except Exception:
                pass
        
        # Generate hashtags by category
        classic_hashtags = [
            f"#{bride_clean}Weds{groom_clean}",
            f"#{groom_clean}And{bride_clean}Forever",
            f"#Forever{bride_clean}{groom_clean}",
            f"#{bride_clean}And{groom_clean}TieTheKnot",
        ]
        
        if year:
            classic_hashtags.append(f"#{bride_clean}{groom_clean}{year}")
        
        fun_hashtags = [
            f"#{bride_clean}KiShaadi",
            f"#{groom_clean}KaDin",
            f"#TwoHeartsOne{bride_clean}{groom_clean}",
            f"#GettingHitched{year}" if year else "#GettingHitched",
            f"#Team{bride_clean}And{groom_clean}",
        ]
        
        trending_hashtags = [
            "#TwoHeartsOneSoul",
            "#HappilyEverAfter",
            f"#WeddingBells{year}" if year else "#WeddingBells",
            f"#FromMsToMrs{bride_clean}",
            "#PutARingOnIt",
            "#LoveWins",
        ]
        
        # Combine based on style preference
        if style == 'classic':
            hashtags = classic_hashtags[:3] + fun_hashtags[:2] + trending_hashtags[:4]
        elif style == 'fun':
            hashtags = fun_hashtags[:4] + classic_hashtags[:2] + trending_hashtags[:3]
        else:  # modern
            hashtags = trending_hashtags[:4] + classic_hashtags[:2] + fun_hashtags[:3]
        
        # Ensure we have exactly the requested count
        all_hashtags = classic_hashtags + fun_hashtags + trending_hashtags
        hashtags = all_hashtags[:count]
        
        return {
            'hashtags': hashtags,
            'by_category': {
                'classic': classic_hashtags[:3],
                'fun': fun_hashtags[:3],
                'trending': trending_hashtags[:3]
            },
            'top_pick': hashtags[0] if hashtags else f"#{bride_clean}Weds{groom_clean}",
            'couple_names': {
                'bride': bride_name,
                'groom': groom_name
            }
        }
    
    def generate_smart_suggestions(
        self,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate smart suggestions for event improvements.
        
        Analyzes event data and provides AI-powered suggestions for:
        - Hashtags
        - Music recommendations
        - Optimal send time
        - Guest engagement tips
        - Cultural considerations
        
        Args:
            event_data: Dictionary containing event information:
                - event_type: str
                - bride_name: str
                - groom_name: str
                - event_date: str (optional)
                - venue_type: str (optional)
                - guest_count: int (optional)
                - culture: str (optional)
                
        Returns:
            Dictionary with categorized suggestions.
        """
        event_type = event_data.get('event_type', 'WEDDING')
        bride_name = event_data.get('bride_name', '')
        groom_name = event_data.get('groom_name', '')
        event_date = event_data.get('event_date', '')
        venue_type = event_data.get('venue_type', 'indoor')
        guest_count = event_data.get('guest_count', 100)
        culture = event_data.get('culture', 'modern')
        
        suggestions: Dict[str, Any] = {
            'hashtags': {},
            'music_suggestions': [],
            'optimal_send_time': {},
            'engagement_tips': [],
            'cultural_notes': [],
            'timing_recommendations': []
        }
        
        # Generate hashtags
        if bride_name and groom_name:
            suggestions['hashtags'] = self.generate_hashtags(
                bride_name=bride_name,
                groom_name=groom_name,
                wedding_date=event_date,
                style='classic'
            )
        
        # Music suggestions
        suggestions['music_suggestions'] = self._get_music_suggestions(
            event_type, culture, venue_type
        )
        
        # Optimal send time
        suggestions['optimal_send_time'] = self._get_optimal_send_time(
            event_type, event_date, culture
        )
        
        # Engagement tips
        suggestions['engagement_tips'] = self._get_engagement_tips(guest_count)
        
        # Cultural notes
        suggestions['cultural_notes'] = self._get_cultural_notes(culture, event_type)
        
        # Timing recommendations
        suggestions['timing_recommendations'] = self._get_timing_recommendations(
            event_date, culture
        )
        
        return suggestions
    
    def _get_music_suggestions(
        self,
        event_type: str,
        culture: str,
        venue_type: str
    ) -> List[Dict[str, Any]]:
        """Get music suggestions based on event context.
        
        Args:
            event_type: Type of event.
            culture: Cultural context.
            venue_type: Venue type (indoor/outdoor).
            
        Returns:
            List of music suggestions by category.
        """
        if 'indian' in culture.lower():
            suggestions = [
                {'category': 'Entry', 'songs': ['London Thumakda', 'Navrai Majhi', 'Sadi Gali']},
                {'category': 'Reception', 'songs': ['Kala Chashma', 'Nashe Si Chadh Gayi', 'Dil Diyan Gallan']},
                {'category': 'Romantic', 'songs': ['Tum Hi Ho', 'Agar Tum Saath Ho', 'Raabta']}
            ]
        else:
            suggestions = [
                {'category': 'Entry', 'songs': ['Canon in D', 'A Thousand Years', 'Perfect']},
                {'category': 'Reception', 'songs': ['Shut Up and Dance', 'Uptown Funk', 'Can\'t Stop the Feeling']},
                {'category': 'First Dance', 'songs': ['At Last', 'All of Me', 'Thinking Out Loud']}
            ]
        
        if venue_type == 'outdoor':
            suggestions.append({
                'category': 'Outdoor Acoustic',
                'songs': ['Blackbird', 'I\'m Yours', 'Banana Pancakes']
            })
        
        return suggestions
    
    def _get_optimal_send_time(
        self,
        event_type: str,
        event_date: str,
        culture: str
    ) -> Dict[str, Any]:
        """Get optimal invitation send time recommendations.
        
        Args:
            event_type: Type of event.
            event_date: Event date string.
            culture: Cultural context.
            
        Returns:
            Dictionary with send time recommendations.
        """
        return {
            'recommendation': 'Send 6-8 weeks before the event',
            'ideal_notice_days': 60,
            'save_the_date': 'Send 4-6 months before for destination weddings',
            'digital_timing': 'Send between Tuesday-Thursday, 10 AM - 2 PM',
            'reminder_timing': 'Send reminder 1-2 weeks before RSVP deadline',
            'cultural_notes': 'Indian weddings typically need 2-3 months notice due to extended celebrations'
        }
    
    def _get_engagement_tips(self, guest_count: int) -> List[Dict[str, Any]]:
        """Get guest engagement tips based on guest count.
        
        Args:
            guest_count: Number of guests.
            
        Returns:
            List of engagement tips.
        """
        tips = [
            {
                'tip': 'Include a personal note for close family members',
                'priority': 'high',
                'category': 'personalization'
            },
            {
                'tip': 'Add an RSVP deadline 2-3 weeks before the event',
                'priority': 'high',
                'category': 'logistics'
            },
            {
                'tip': 'Include accommodation details for out-of-town guests',
                'priority': 'medium',
                'category': 'hospitality'
            }
        ]
        
        if guest_count > 150:
            tips.extend([
                {
                    'tip': 'Consider digital RSVP for easier tracking with large guest list',
                    'priority': 'high',
                    'category': 'logistics'
                },
                {
                    'tip': 'Set up a wedding website with FAQs to reduce repetitive questions',
                    'priority': 'medium',
                    'category': 'communication'
                }
            ])
        
        return tips
    
    def _get_cultural_notes(self, culture: str, event_type: str) -> List[str]:
        """Get cultural considerations for the invitation.
        
        Args:
            culture: Cultural context.
            event_type: Type of event.
            
        Returns:
            List of cultural notes.
        """
        if 'north_indian' in culture.lower() or 'punjabi' in culture.lower():
            return [
                'Consider mentioning all pre-wedding events (Sangeet, Mehendi, Haldi)',
                'Include both families\' names prominently',
                'Mention dress code if traditional attire is preferred',
                'Note any specific rituals guests should be aware of'
            ]
        elif 'south_indian' in culture.lower():
            return [
                'Include muhurtham (auspicious time) details if applicable',
                'Mention temple ceremonies separately from reception',
                'Note traditional dress expectations',
                'Consider including a brief ritual guide for non-Indian guests'
            ]
        else:
            return [
                'Clearly state ceremony start time vs. reception time',
                'Mention dress code if formal attire is required',
                'Include gift registry information tastefully',
                'Add parking/transportation details if needed'
            ]
    
    def _get_timing_recommendations(
        self,
        event_date: str,
        culture: str
    ) -> List[Dict[str, Any]]:
        """Get timing recommendations for invitation sending.
        
        Args:
            event_date: Event date string.
            culture: Cultural context.
            
        Returns:
            List of timing recommendations.
        """
        return [
            {
                'milestone': 'Save the Date',
                'timing': '4-6 months before',
                'recommended': True,
                'notes': 'Essential for destination weddings'
            },
            {
                'milestone': 'Formal Invitation',
                'timing': '6-8 weeks before',
                'recommended': True,
                'notes': 'Standard timeline for most events'
            },
            {
                'milestone': 'RSVP Deadline',
                'timing': '3 weeks before',
                'recommended': True,
                'notes': 'Allows time for final headcount'
            },
            {
                'milestone': 'Reminder Message',
                'timing': '1 week before deadline',
                'recommended': True,
                'notes': 'Gentle reminder for non-responders'
            }
        ]
    
    def customize_message(
        self,
        base_message: str,
        customizations: Dict[str, str]
    ) -> str:
        """Customize a generated message with user modifications.
        
        Args:
            base_message: Original generated message.
            customizations: Dictionary of customizations:
                - opening: Replace first line
                - closing: Add at the end
                - additional_info: Insert before closing
                
        Returns:
            Customized message string.
        """
        message = base_message
        
        if 'opening' in customizations:
            lines = message.split('\n')
            if lines:
                lines[0] = customizations['opening']
                message = '\n'.join(lines)
        
        if 'additional_info' in customizations:
            # Insert before last paragraph or at end
            paragraphs = message.split('\n\n')
            if len(paragraphs) > 1:
                paragraphs.insert(-1, customizations['additional_info'])
                message = '\n\n'.join(paragraphs)
            else:
                message += f"\n\n{customizations['additional_info']}"
        
        if 'closing' in customizations:
            message += f"\n\n{customizations['closing']}"
        
        return sanitize_message_text(message)
    
    def get_style_description(self, style: str) -> Dict[str, Any]:
        """Get description and characteristics of a message style.
        
        Args:
            style: Message style code.
            
        Returns:
            Dictionary with style information.
        """
        style_info = {
            'traditional_formal': {
                'name': 'Traditional & Formal',
                'description': 'Respectful, classic wording with cultural elements',
                'characteristics': ['respectful', 'classic', 'timeless', 'ceremonial'],
                'best_for': ['formal weddings', 'traditional ceremonies', 'family-focused events'],
                'tone': 'dignified and respectful'
            },
            'warm_personal': {
                'name': 'Warm & Personal',
                'description': 'Heartfelt, storytelling approach that feels intimate',
                'characteristics': ['emotional', 'heartfelt', 'personal', 'warm'],
                'best_for': ['close friends and family', 'intimate gatherings', 'second weddings'],
                'tone': 'warm and intimate'
            },
            'fun_modern': {
                'name': 'Fun & Modern',
                'description': 'Lighthearted, contemporary style for modern couples',
                'characteristics': ['playful', 'contemporary', 'laid-back', 'fun'],
                'best_for': ['casual weddings', 'non-traditional venues', 'young couples'],
                'tone': 'light and entertaining'
            }
        }
        
        return style_info.get(style, style_info['warm_personal'])
