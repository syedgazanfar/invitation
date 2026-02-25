# AI Features Technical Specification

> Detailed implementation guide for AI-powered features

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Feature 1: Photo-to-Theme Analysis](#feature-1-photo-to-theme-analysis)
4. [Feature 2: Template Recommendation Engine](#feature-2-template-recommendation-engine)
5. [Feature 3: Smart Message Generator](#feature-3-smart-message-generator)
6. [Feature 4: Color Palette Extraction](#feature-4-color-palette-extraction)
7. [Feature 5: Hashtag Generator](#feature-5-hashtag-generator)
8. [Feature 6: RSVP Prediction](#feature-6-rsvp-prediction)
9. [API Integration Guide](#api-integration-guide)
10. [Cost Estimation](#cost-estimation)

---

## Overview

### AI Feature Philosophy
```
Our AI features follow the "1-Click Magic" principle:
├── User uploads/inputs something
├── AI processes automatically
├── User gets 3 curated suggestions
└── One click to apply
```

### AI Stack
```
┌─────────────────────────────────────────────────────────────┐
│                      AI TECH STACK                           │
├─────────────────────────────────────────────────────────────┤
│  Image Analysis                                             │
│  ├── Google Vision API (primary)                            │
│  └── AWS Rekognition (backup)                               │
│                                                             │
│  Text Generation                                            │
│  ├── OpenAI GPT-4 (primary)                                 │
│  └── Claude 3 (backup)                                      │
│                                                             │
│  Custom ML (Self-hosted)                                    │
│  ├── TensorFlow.js (browser)                                │
│  ├── scikit-learn (Python)                                  │
│  └── FastAPI model serving                                  │
│                                                             │
│  Infrastructure                                             │
│  ├── Redis (caching)                                        │
│  ├── Celery (async processing)                              │
│  └── S3 (image storage)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Architecture

### System Flow
```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Frontend   │──────▶│   Backend    │──────▶│  AI Services │
│   (React)    │◀──────│   (Django)   │◀──────│  (External)  │
└──────────────┘      └──────┬───────┘      └──────────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │    Redis     │
                      │    Cache     │
                      └──────────────┘
```

### Data Flow
```
1. User uploads photo
   ↓
2. Django receives → Stores in S3
   ↓
3. Celery task triggered
   ↓
4. AI analysis (Vision API + Custom ML)
   ↓
5. Results cached in Redis
   ↓
6. Response to frontend
   ↓
7. User sees recommendations
```

---

## Feature 1: Photo-to-Theme Analysis

### Description
Analyzes couple's photo to extract mood, style, and theme preferences.

### User Flow
```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Upload Photo                                       │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  📷 Drag & drop or click to upload                    │  │
│  │                                                        │  │
│  │  [Upload your couple photo]                           │  │
│  │                                                        │  │
│  │  Tips: Use a clear photo showing both of you          │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  Step 2: AI Analysis (2-3 seconds)                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  🤖 Analyzing your photo...                           │  │
│  │  ✓ Detecting colors                                   │  │
│  │  ✓ Identifying mood                                   │  │
│  │  ✓ Extracting style                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓                                │
│  Step 3: Recommendations                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Based on your photo, we recommend:                   │  │
│  │                                                        │  │
│  │  🎨 Romantic Elegance    🎨 Modern Minimalist         │  │
│  │  🎨 Traditional Royal    [View All 5 Suggestions]     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### API Specification

#### Endpoint
```http
POST /api/v1/ai/analyze-photo/
Content-Type: multipart/form-data
```

#### Request
```json
{
  "photo": "<file>",
  "event_type": "WEDDING",
  "language": "en"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "analysis_id": "uuid",
    "primary_colors": [
      {"color": "#A61E2A", "name": "Deep Red", "percentage": 35},
      {"color": "#2E2E2E", "name": "Charcoal", "percentage": 25},
      {"color": "#D4AF37", "name": "Gold", "percentage": 20}
    ],
    "mood": {
      "primary": "romantic",
      "confidence": 0.92,
      "secondary": ["elegant", "traditional"]
    },
    "style_recommendations": [
      {
        "style": "Romantic Elegance",
        "confidence": 0.89,
        "matching_templates": ["template_id_1", "template_id_2"],
        "color_palette": ["#A61E2A", "#FFFFFF", "#D4AF37"]
      }
    ],
    "ai_suggestions": {
      "message_tone": "warm and romantic",
      "hashtag_ideas": ["#ForeverBegins", "#TwoSoulsOneHeart"],
      "music_mood": "soft romantic"
    }
  }
}
```

### Implementation

#### Backend (Django)
```python
# apps/ai/services/photo_analysis.py
import google.cloud.vision as vision
from typing import Dict, List
import colorsys

class PhotoAnalysisService:
    def __init__(self):
        self.vision_client = vision.ImageAnnotatorClient()
    
    def analyze(self, image_path: str) -> Dict:
        """
        Main analysis pipeline
        """
        # 1. Get dominant colors
        colors = self._extract_colors(image_path)
        
        # 2. Detect mood from image properties
        mood = self._detect_mood(image_path)
        
        # 3. Generate recommendations
        recommendations = self._generate_recommendations(colors, mood)
        
        return {
            'primary_colors': colors,
            'mood': mood,
            'recommendations': recommendations
        }
    
    def _extract_colors(self, image_path: str) -> List[Dict]:
        """
        Extract dominant colors using Google Vision API
        """
        with open(image_path, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        response = self.vision_client.image_properties(image=image)
        
        colors = []
        for color in response.image_properties_annotation.dominant_colors.colors:
            rgb = color.color
            hex_color = '#{:02x}{:02x}{:02x}'.format(
                int(rgb.red), int(rgb.green), int(rgb.blue)
            )
            colors.append({
                'color': hex_color,
                'score': color.score,
                'pixel_fraction': color.pixel_fraction
            })
        
        return colors[:5]  # Top 5 colors
    
    def _detect_mood(self, image_path: str) -> Dict:
        """
        Detect image mood using label detection
        """
        with open(image_path, 'rb') as f:
            content = f.read()
        
        image = vision.Image(content=content)
        response = self.vision_client.label_detection(image=image)
        
        labels = [label.description for label in response.label_annotations]
        
        # Map labels to moods
        mood_mapping = {
            'romantic': ['romance', 'love', 'couple', 'wedding', 'bride'],
            'fun': ['party', 'celebration', 'fun', 'laughing'],
            'elegant': ['formal', 'elegance', 'luxury', 'sophisticated'],
            'traditional': ['tradition', 'culture', 'ceremony', 'ritual']
        }
        
        mood_scores = {}
        for mood, keywords in mood_mapping.items():
            score = sum(1 for keyword in keywords if any(keyword in label.lower() for label in labels))
            mood_scores[mood] = score / len(keywords)
        
        primary_mood = max(mood_scores, key=mood_scores.get)
        
        return {
            'primary': primary_mood,
            'confidence': mood_scores[primary_mood],
            'all_scores': mood_scores
        }
```

#### Frontend (React)
```typescript
// hooks/usePhotoAnalysis.ts
import { useState, useCallback } from 'react';
import { aiApi } from '../services/api';

interface PhotoAnalysisResult {
  primaryColors: Array<{ color: string; name: string; percentage: number }>;
  mood: {
    primary: string;
    confidence: number;
  };
  recommendations: Array<{
    style: string;
    matchingTemplates: string[];
  }>;
}

export const usePhotoAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PhotoAnalysisResult | null>(null);
  const [progress, setProgress] = useState(0);

  const analyzePhoto = useCallback(async (file: File) => {
    setLoading(true);
    setProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress(p => Math.min(p + 10, 90));
    }, 200);
    
    try {
      const formData = new FormData();
      formData.append('photo', file);
      formData.append('event_type', 'WEDDING');
      
      const response = await aiApi.analyzePhoto(formData);
      
      if (response.success) {
        setResult(response.data);
      }
    } finally {
      clearInterval(progressInterval);
      setProgress(100);
      setLoading(false);
    }
  }, []);

  return { analyzePhoto, result, loading, progress };
};
```

---

## Feature 2: Template Recommendation Engine

### Description
ML-powered engine that recommends templates based on user preferences, photo analysis, and historical data.

### Algorithm
```python
# Recommendation logic
def recommend_templates(user_data, photo_analysis, event_type):
    # 1. Content-based filtering (photo colors, mood)
    content_score = calculate_content_match(photo_analysis, templates)
    
    # 2. Collaborative filtering (similar users)
    collaborative_score = get_similar_user_choices(user_data, templates)
    
    # 3. Popularity boost
    popularity_score = get_template_popularity(templates)
    
    # 4. Weighted combination
    final_score = (
        0.5 * content_score + 
        0.3 * collaborative_score + 
        0.2 * popularity_score
    )
    
    return top_n_templates(final_score, n=5)
```

### API Response
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "template_id": "tpl_123",
        "name": "Royal Red Affair",
        "match_score": 0.94,
        "match_reasons": [
          "Matches your photo's color scheme",
          "Popular for romantic weddings",
          "Trending in your region"
        ],
        "preview_url": "https://...",
        "thumbnail": "https://..."
      }
    ],
    "personalization_factors": {
      "color_match": 0.95,
      "mood_match": 0.88,
      "popularity": 0.92
    }
  }
}
```

---

## Feature 3: Smart Message Generator

### Description
GPT-4 powered message generator for invitation cards.

### Prompt Engineering
```python
# System prompt for message generation
SYSTEM_PROMPT = """
You are a professional wedding invitation copywriter with 20 years of experience.
Create warm, personalized invitation messages based on:
- Couple names
- Relationship details
- Wedding style/mood
- Cultural context

Guidelines:
- Keep messages between 50-150 words
- Match the tone to the event type
- Include essential details (date, venue hint)
- Make it feel personal and heartfelt
- Avoid clichés and generic phrases
"""

# User prompt template
USER_PROMPT_TEMPLATE = """
Generate an invitation message for:

Couple: {bride_name} & {groom_name}
Event Type: {event_type}
Style/Mood: {style}
Cultural Context: {culture}
Key Details: {details}
Tone: {tone}

Generate 3 options with different styles:
1. Traditional & Formal
2. Warm & Personal
3. Fun & Modern
"""
```

### API Endpoint
```http
POST /api/v1/ai/generate-message/
Content-Type: application/json
```

### Request/Response
```json
// Request
{
  "bride_name": "Priya",
  "groom_name": "Rahul",
  "event_type": "WEDDING",
  "style": "traditional_indian",
  "culture": "north_indian",
  "tone": "warm",
  "details": "Childhood sweethearts, 10 years together"
}

// Response
{
  "success": true,
  "data": {
    "options": [
      {
        "style": "traditional_formal",
        "message": "With the blessings of our elders and the love of our families, we invite you to celebrate the union of Priya and Rahul...",
        "word_count": 85
      },
      {
        "style": "warm_personal",
        "message": "From playground friends to soulmates, our 10-year journey comes full circle. Join us as we begin our forever...",
        "word_count": 72
      },
      {
        "style": "fun_modern",
        "message": "Finally making it official! After a decade of love, laughter, and countless memories...",
        "word_count": 68
      }
    ],
    "tokens_used": 450,
    "generation_time_ms": 1200
  }
}
```

### Implementation
```python
# apps/ai/services/message_generator.py
import openai
from django.conf import settings

class MessageGeneratorService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
    
    def generate(self, context: dict) -> list:
        prompt = self._build_prompt(context)
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=500,
            n=1
        )
        
        # Parse the response into structured options
        content = response.choices[0].message.content
        return self._parse_options(content)
    
    def _build_prompt(self, context: dict) -> str:
        return USER_PROMPT_TEMPLATE.format(**context)
```

---

## Feature 4: Color Palette Extraction

### Description
Extract and suggest color palettes from uploaded photos.

### Algorithm
```python
def extract_color_palette(image_path):
    # 1. Get dominant colors
    dominant = get_dominant_colors(image_path, n=5)
    
    # 2. Get accent colors (complementary)
    accent = get_complementary_colors(dominant[0])
    
    # 3. Generate palette variations
    palettes = {
        'harmonious': generate_harmonious_palette(dominant),
        'complementary': generate_complementary_palette(dominant),
        'monochromatic': generate_monochromatic_palette(dominant[0]),
        'triadic': generate_triadic_palette(dominant[0])
    }
    
    return palettes
```

### Response Format
```json
{
  "extracted_colors": [
    {"hex": "#A61E2A", "name": "Deep Red", "role": "primary"},
    {"hex": "#2E2E2E", "name": "Charcoal", "role": "secondary"},
    {"hex": "#D4AF37", "name": "Gold", "role": "accent"}
  ],
  "suggested_palettes": [
    {
      "name": "Royal Romance",
      "colors": ["#A61E2A", "#FFFFFF", "#D4AF37", "#2E2E2E"],
      "description": "Perfect for traditional Indian weddings"
    }
  ]
}
```

---

## Feature 5: Hashtag Generator

### Description
Generate creative wedding hashtags based on couple names.

### Algorithm
```python
def generate_hashtags(bride_name, groom_name, wedding_date=None, style="classic"):
    hashtags = []
    
    # Pattern 1: Simple combination
    hashtags.append(f"#{bride_name}Weds{groom_name}")
    hashtags.append(f"#{groom_name}And{bride_name}Forever")
    
    # Pattern 2: Phonetic combinations
    phonetic = create_phonetic_combination(bride_name, groom_name)
    hashtags.append(f"#{phonetic}")
    
    # Pattern 3: Date incorporation
    if wedding_date:
        year = wedding_date.year
        hashtags.append(f"#{bride_name}{groom_name}{year}")
    
    # Pattern 4: Style-based
    if style == "fun":
        hashtags.append(f"#Finally{bride_name}And{groom_name}")
        hashtags.append(f"#{bride_name}KiShaadi")
    
    # Pattern 5: Cultural
    hashtags.extend(get_cultural_hashtags(bride_name, groom_name))
    
    return {
        'classic': hashtags[:3],
        'fun': hashtags[3:6],
        'trending': hashtags[6:9]
    }
```

### API
```http
GET /api/v1/ai/generate-hashtags/?bride=Priya&groom=Rahul&date=2026-12-15&style=fun
```

---

## Feature 6: RSVP Prediction

### Description
ML model to predict attendance likelihood based on guest data.

### Features for Model
```python
FEATURES = [
    # Guest features
    'days_since_invited',
    'invitation_opened',
    'times_opened',
    'device_type',
    'location_distance_km',
    
    # Historical features
    'past_event_attendance_rate',
    'relationship_to_couple',
    
    # Temporal features
    'day_of_week',
    'month',
    'days_until_event',
    
    # Event features
    'event_type',
    'venue_distance_from_guest',
]
```

### Model Architecture
```python
from sklearn.ensemble import GradientBoostingClassifier

class RSVPPredictor:
    def __init__(self):
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1
        )
    
    def train(self, X, y):
        """Train on historical RSVP data"""
        self.model.fit(X, y)
    
    def predict(self, guest_features):
        """Predict attendance probability"""
        probability = self.model.predict_proba(guest_features)[0][1]
        return {
            'will_attend_probability': probability,
            'confidence': 'high' if probability > 0.7 or probability < 0.3 else 'medium',
            'expected_response_time_days': self._estimate_response_time(guest_features)
        }
```

---

## API Integration Guide

### Rate Limiting
```python
# settings.py
AI_RATE_LIMITS = {
    'photo_analysis': '10/minute',
    'message_generation': '30/hour',
    'hashtag_generation': '50/hour',
    'rsvp_prediction': '100/minute'
}
```

### Caching Strategy
```python
# Cache AI results to reduce API costs
CACHE_CONFIG = {
    'photo_analysis': '24 hours',  # Colors don't change
    'template_recommendations': '1 hour',
    'message_generation': 'no cache',  # Always fresh
    'hashtag_generation': 'infinite',  # Deterministic
}
```

### Error Handling
```python
class AIErrorHandler:
    @staticmethod
    def handle_vision_api_error(error):
        # Fallback to AWS Rekognition
        return fallback_to_rekognition()
    
    @staticmethod
    def handle_openai_error(error):
        # Use cached responses or templates
        return fallback_to_templates()
```

---

## Cost Estimation

### Monthly API Costs (1,000 users/month)

| Service | Usage | Unit Cost | Monthly Cost |
|---------|-------|-----------|--------------|
| Google Vision API | 2,000 images | $1.50/1000 | $3.00 |
| OpenAI GPT-4 | 50K tokens | $0.03/1K | $1.50 |
| OpenAI GPT-3.5 | 200K tokens | $0.002/1K | $0.40 |
| AWS Rekognition (backup) | 500 images | $1.00/1000 | $0.50 |
| **Total** | | | **~$5.40** |

### Scaling Costs
| Users | Monthly API Cost | Infrastructure |
|-------|------------------|----------------|
| 1,000 | $5 | $50 |
| 10,000 | $50 | $200 |
| 100,000 | $500 | $1,000 |

### Cost Optimization Tips
1. **Cache aggressively** - Reduce API calls by 80%
2. **Batch processing** - Process photos in background
3. **Tiered AI** - Use GPT-3.5 for simple tasks
4. **Smart fallbacks** - Use rules when AI is unnecessary

---

## Implementation Checklist

### Phase 1: Basic AI (Week 1-4)
- [ ] Google Vision API integration
- [ ] Photo color extraction
- [ ] Basic template matching
- [ ] Simple message generation

### Phase 2: Advanced AI (Week 5-8)
- [ ] Custom ML model training
- [ ] Collaborative filtering
- [ ] Hashtag generator
- [ ] RSVP prediction model

### Phase 3: Polish (Week 9-12)
- [ ] Performance optimization
- [ ] Caching implementation
- [ ] A/B testing setup
- [ ] Feedback loop integration

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Photo Analysis Accuracy | 85%+ | User feedback |
| Template Selection Rate | 60%+ | Click-through rate |
| Message Usage Rate | 40%+ | Generated messages used |
| API Response Time | <2s | 95th percentile |
| AI Feature Adoption | 70%+ | % users using AI features |
| Cost per User | <$0.10 | Monthly API cost / users |

---

## Conclusion

These AI features will differentiate our platform by:
1. **Reducing friction** - Users get suggestions instantly
2. **Improving outcomes** - Better template selection = happier users
3. **Creating delight** - "Magic" moments with AI
4. **Increasing conversions** - Guided experience leads to more purchases

**Total Development Time**: 12 weeks
**Total API Cost**: ~$5-50/month (scales with users)
**Expected Impact**: 30% increase in conversion rate
