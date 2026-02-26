# AI Features API Documentation

This document describes the AI-powered features API endpoints available in the Wedding Invitation Platform.

## Base URL

```
/api/v1/ai/
```

## Authentication

All AI endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

## Rate Limiting

AI features have rate limits based on user plans:

| Plan | Daily Token Limit | Photo Analysis | Message Generation |
|------|-------------------|----------------|-------------------|
| Basic | 5,000 | 5/day | 10/day |
| Premium | 15,000 | 20/day | 50/day |
| Luxury | 50,000 | 100/day | 200/day |

## Endpoints

### 1. Photo Analysis

#### POST /api/v1/ai/analyze-photo/

Analyze an uploaded photo to extract colors, detect mood, and get style recommendations.

**Content-Type:** `multipart/form-data`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| photo | File | Yes | Image file (JPG, PNG, WebP, max 10MB) |
| event_type | String | No | Event type: WEDDING, BIRTHDAY, PARTY, FESTIVAL (default: WEDDING) |
| order_id | Integer | No | Optional existing order ID to associate |

**Response:**

```json
{
  "success": true,
  "data": {
    "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
    "primary_colors": {
      "dominant": {"hex": "#E8B4B8", "percentage": 35.5, "name": "Dusty Rose"},
      "palette": [
        {"hex": "#E8B4B8", "percentage": 35.5, "name": "Dusty Rose"},
        {"hex": "#EAD2AC", "percentage": 25.3, "name": "Champagne"},
        {"hex": "#6B8E8E", "percentage": 20.1, "name": "Sage Green"}
      ],
      "palette_type": "romantic"
    },
    "mood": {
      "primary_mood": "romantic",
      "confidence": 0.87,
      "tags": ["romantic", "elegant", "soft", "dreamy"],
      "emotions": ["love", "joy", "tenderness"],
      "atmosphere": "warm and intimate"
    },
    "style_recommendations": [
      {
        "type": "style",
        "name": "Romantic Garden",
        "description": "Soft, floral designs with elegant typography",
        "suggestions": {
          "fonts": ["Playfair Display", "Cormorant Garamond"],
          "layouts": ["asymmetric", "organic"],
          "decor_elements": ["flowers", "lace", "soft lighting"]
        }
      }
    ],
    "ai_suggestions": {
      "event_type": "WEDDING",
      "suggested_templates": {
        "based_on_mood": ["romantic", "elegant", "soft"],
        "recommended_categories": ["classic", "modern"]
      },
      "suggested_styles": ["Floral", "Soft Lighting", "Pastel Colors"]
    }
  },
  "processing_time_ms": 1250
}
```

---

### 2. Color Extraction

#### POST /api/v1/ai/extract-colors/

Extract colors from a photo (simpler endpoint for just color analysis).

**Content-Type:** `multipart/form-data` or `application/json`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| photo | File | Yes* | Image file (JPG, PNG, WebP, max 10MB) |
| image_url | String | Yes* | URL of image to analyze |

*Either photo or image_url is required

**Response:**

```json
{
  "success": true,
  "data": {
    "dominant": {"hex": "#E8B4B8", "percentage": 35.5, "name": "Dusty Rose"},
    "palette": [
      {"hex": "#E8B4B8", "percentage": 35.5, "name": "Dusty Rose"},
      {"hex": "#EAD2AC", "percentage": 25.3, "name": "Champagne"}
    ],
    "palette_type": "romantic"
  }
}
```

---

### 3. Mood Detection

#### POST /api/v1/ai/detect-mood/

Detect mood and atmosphere from a photo.

**Content-Type:** `multipart/form-data` or `application/json`

**Request Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| photo | File | Yes* | Image file (max 10MB) |
| image_url | String | Yes* | URL of image to analyze |

**Response:**

```json
{
  "success": true,
  "data": {
    "primary_mood": "romantic",
    "confidence": 0.87,
    "tags": ["romantic", "elegant", "soft", "dreamy"],
    "emotions": ["love", "joy", "tenderness"],
    "atmosphere": "warm and intimate"
  }
}
```

---

### 4. Message Generation

#### POST /api/v1/ai/generate-messages/

Generate AI-powered invitation messages.

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "bride_name": "Emma",
  "groom_name": "James",
  "event_type": "WEDDING",
  "style": "romantic",
  "culture": "modern",
  "tone": "warm",
  "event_date": "2024-06-15",
  "venue": "Grand Plaza Hotel",
  "details": "Outdoor ceremony followed by reception"
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| bride_name | String | Yes | Bride's name |
| groom_name | String | Yes | Groom's name |
| event_type | String | No | WEDDING, BIRTHDAY, PARTY, FESTIVAL |
| style | String | No | romantic, formal, casual, funny, poetic, traditional, modern |
| culture | String | No | modern, traditional, fusion, etc. |
| tone | String | No | warm, formal, casual, funny |
| event_date | Date | No | Event date (YYYY-MM-DD) |
| venue | String | No | Venue name |
| details | String | No | Additional details |

**Response:**

```json
{
  "success": true,
  "data": {
    "options": [
      {
        "id": "opt_1",
        "text": "Together with our families, we Emma and James invite you to share in the joy of our wedding day...",
        "style": "romantic",
        "tone": "warm"
      },
      {
        "id": "opt_2",
        "text": "Love has brought us together, and now we invite you to witness our happily ever after...",
        "style": "romantic",
        "tone": "warm"
      },
      {
        "id": "opt_3",
        "text": "Two hearts, one love, endless possibilities. We, Emma and James, would be honored...",
        "style": "romantic",
        "tone": "warm"
      }
    ],
    "message_id": "550e8400-e29b-41d4-a716-446655440000",
    "tokens_used": 150,
    "generation_time_ms": 850
  }
}
```

---

### 5. Get Message Styles

#### GET /api/v1/ai/message-styles/

Get available message styles.

**Response:**

```json
{
  "success": true,
  "data": {
    "styles": [
      {"code": "romantic", "name": "Romantic", "description": "Soft, loving, and emotional tone"},
      {"code": "formal", "name": "Formal", "description": "Professional and elegant tone"},
      {"code": "casual", "name": "Casual", "description": "Relaxed and friendly tone"},
      {"code": "funny", "name": "Funny", "description": "Humorous and light-hearted tone"},
      {"code": "poetic", "name": "Poetic", "description": "Artistic and lyrical tone"},
      {"code": "traditional", "name": "Traditional", "description": "Classic and timeless tone"},
      {"code": "modern", "name": "Modern", "description": "Contemporary and trendy tone"}
    ]
  }
}
```

---

### 6. Hashtag Generation

#### POST /api/v1/ai/generate-hashtags/

Generate wedding hashtags based on couple names.

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "bride_name": "Emma Johnson",
  "groom_name": "James Smith",
  "style": "romantic",
  "count": 10
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "hashtags": [
      "#EmmaJamesForever",
      "#EmmaAndJamesTieTheKnot",
      "#LoveEmmaJames",
      "#EmmaJamesWedding",
      "#HappilyEverAfterEmmaJames"
    ],
    "style": "romantic",
    "couple_names": {
      "bride": "Emma Johnson",
      "groom": "James Smith"
    }
  }
}
```

---

### 7. Template Recommendations

#### GET /api/v1/ai/recommend-templates/

Get template recommendations based on event type, style, and colors.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| event_type | String | WEDDING, BIRTHDAY, PARTY, etc. |
| style | String | romantic, modern, vintage, etc. |
| colors[] | Array | Array of hex color codes |

**Example:** `/api/v1/ai/recommend-templates/?event_type=WEDDING&style=romantic&colors[]=%23E8B4B8&colors[]=%23EAD2AC`

**Response:**

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "template_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Romantic Garden",
        "match_score": 0.95,
        "match_reasons": ["Perfect match for romantic style", "Colors complement your palette"],
        "preview_url": "https://example.com/templates/romantic-garden.jpg",
        "thumbnail": "https://example.com/templates/romantic-garden-thumb.jpg"
      }
    ],
    "filters_applied": {
      "event_type": "WEDDING",
      "style": "romantic",
      "colors": ["#E8B4B8", "#EAD2AC"],
      "user_plan": "PREMIUM"
    }
  }
}
```

---

### 8. Style Recommendations

#### GET /api/v1/ai/style-recommendations/

Get style recommendations without needing a photo upload.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| colors[] | Array | Array of hex color codes |
| mood | String | Target mood (romantic, modern, vintage, etc.) |
| event_type | String | Type of event |

**Response:**

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "style": "romantic",
        "match_confidence": 0.95,
        "details": {
          "name": "Romantic Elegance",
          "description": "Soft, flowing designs with delicate details and warm colors",
          "suitable_for": ["WEDDING", "ANNIVERSARY"],
          "font_pairing": ["Playfair Display", "Lato"],
          "decor_elements": ["Fresh flowers", "Candlelight", "Lace details"]
        }
      }
    ],
    "based_on": {
      "colors": ["#E8B4B8", "#EAD2AC"],
      "mood": "romantic",
      "event_type": "WEDDING"
    }
  }
}
```

---

### 9. Get Usage Statistics

#### GET /api/v1/ai/usage/

Get user's AI feature usage statistics.

**Response:**

```json
{
  "success": true,
  "data": {
    "total_requests_today": 5,
    "total_tokens_today": 1250,
    "total_requests_this_month": 45,
    "total_tokens_this_month": 12500,
    "requests_by_feature": {
      "photo_analysis": 2,
      "message_generation": 3
    },
    "feature_display_names": {
      "photo_analysis": "Photo Analysis",
      "message_generation": "Message Generation",
      "template_recommendation": "Template Recommendation",
      "color_extraction": "Color Extraction",
      "mood_detection": "Mood Detection",
      "smart_suggestions": "Smart Suggestions"
    }
  }
}
```

---

### 10. Get Usage Limits

#### GET /api/v1/ai/limits/

Get user's current rate limits and remaining quota.

**Response:**

```json
{
  "success": true,
  "data": {
    "daily_token_limit": 15000,
    "monthly_token_limit": 200000,
    "tokens_used_today": 1250,
    "tokens_used_this_month": 12500,
    "tokens_remaining_today": 13750,
    "tokens_remaining_this_month": 187500,
    "can_make_request": true,
    "feature_usage": {
      "photo_analysis": {
        "used_today": 2,
        "limit": 20,
        "remaining": 18
      },
      "message_generation": {
        "used_today": 3,
        "limit": 50,
        "remaining": 47
      }
    }
  }
}
```

---

### 11. Smart Suggestions

#### POST /api/v1/ai/smart-suggestions/

Get AI-powered suggestions for event planning.

**Content-Type:** `application/json`

**Request Body:**

```json
{
  "category": "venue",
  "context": {
    "guest_count": 150,
    "budget": "medium",
    "season": "summer"
  }
}
```

**Categories:** venue, timeline, budget, decor, photography, invitation

**Response:**

```json
{
  "success": true,
  "data": {
    "category": "venue",
    "suggestions": [
      "Consider venues with both indoor and outdoor options for flexibility",
      "Visit your top 3 venues at the same time of day as your event",
      "Ask about vendor restrictions and corkage fees"
    ],
    "context_used": {
      "guest_count": 150,
      "budget": "medium",
      "season": "summer"
    }
  }
}
```

---

### 12. ViewSets

#### Photo Analysis CRUD

- `GET /api/v1/ai/photo-analysis/` - List all photo analyses
- `POST /api/v1/ai/photo-analysis/` - Create new analysis
- `GET /api/v1/ai/photo-analysis/{id}/` - Get specific analysis
- `PUT /api/v1/ai/photo-analysis/{id}/` - Update analysis
- `DELETE /api/v1/ai/photo-analysis/{id}/` - Delete analysis
- `POST /api/v1/ai/photo-analysis/{id}/reanalyze/` - Reanalyze photo

#### Generated Messages CRUD

- `GET /api/v1/ai/generated-messages/` - List all generated messages
- `POST /api/v1/ai/generated-messages/` - Create new message
- `GET /api/v1/ai/generated-messages/{id}/` - Get specific message
- `PUT /api/v1/ai/generated-messages/{id}/` - Update message
- `DELETE /api/v1/ai/generated-messages/{id}/` - Delete message
- `POST /api/v1/ai/generated-messages/{id}/regenerate/` - Regenerate with same context

---

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Error message description",
  "details": {}  // Optional additional details
}
```

### Common HTTP Status Codes

| Status | Description |
|--------|-------------|
| 200 OK | Successful GET request |
| 201 Created | Successful POST request |
| 400 Bad Request | Invalid request data |
| 401 Unauthorized | Missing or invalid authentication |
| 403 Forbidden | Rate limit exceeded or permission denied |
| 404 Not Found | Resource not found |
| 429 Too Many Requests | Rate limit exceeded |
| 500 Internal Server Error | Server error |

### Common Error Messages

- `"AI feature usage limit exceeded or not available for your plan."` - Rate limit reached
- `"File size exceeds 10MB limit"` - Uploaded file too large
- `"Invalid file type. Allowed: image/jpeg, image/png, image/webp"` - Wrong file format
- `"Either photo file or image_url is required"` - Missing required parameter

---

## Python Usage Examples

### Using Requests

```python
import requests

headers = {
    'Authorization': 'Bearer <your_access_token>'
}

# Upload and analyze a photo
with open('wedding_photo.jpg', 'rb') as f:
    files = {'photo': f}
    data = {'event_type': 'WEDDING'}
    response = requests.post(
        'http://localhost:8000/api/v1/ai/analyze-photo/',
        headers=headers,
        files=files,
        data=data
    )
    result = response.json()

# Generate messages
payload = {
    'bride_name': 'Emma',
    'groom_name': 'James',
    'style': 'romantic',
    'tone': 'warm'
}
response = requests.post(
    'http://localhost:8000/api/v1/ai/generate-messages/',
    headers=headers,
    json=payload
)
messages = response.json()
```

### Using cURL

```bash
# Analyze photo
curl -X POST http://localhost:8000/api/v1/ai/analyze-photo/ \
  -H "Authorization: Bearer <token>" \
  -F "photo=@wedding_photo.jpg" \
  -F "event_type=WEDDING"

# Generate messages
curl -X POST http://localhost:8000/api/v1/ai/generate-messages/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "bride_name": "Emma",
    "groom_name": "James",
    "style": "romantic"
  }'

# Get usage limits
curl http://localhost:8000/api/v1/ai/limits/ \
  -H "Authorization: Bearer <token>"
```

---

## Notes

1. **File Uploads**: Maximum file size is 10MB. Supported formats: JPG, PNG, WebP.

2. **Mock Mode**: In development mode (`AI_MOCK_MODE=True`), AI features return simulated responses without calling external APIs.

3. **Caching**: Photo analysis results are cached for 24 hours to improve performance.

4. **Async Processing**: Heavy operations use Celery for background processing.

5. **Logging**: All AI feature usage is logged for analytics and rate limiting.
