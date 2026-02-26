# AI Views Refactoring Blueprint

**File:** `apps/backend/src/apps/ai/views.py` (1,496 lines)
**Goal:** Split into focused modules of ~250-400 lines each

## Current Structure Analysis

**Total Classes:** 18 view classes
**Helper Functions:** 3 (create_success_response, create_error_response, add_rate_limit_headers)
**Constants:** File limits, rate limit headers

## New Structure

```
apps/backend/src/apps/ai/
├── views/
│   ├── __init__.py           # Export all views (150 lines)
│   ├── helpers.py            # Response helpers & constants (140 lines) ✅ CREATED
│   ├── photo_analysis.py     # Photo analysis views (~400 lines)
│   ├── message_generation.py # Message & hashtag generation (~300 lines)
│   ├── recommendations.py    # Template & style recommendations (~350 lines)
│   └── usage.py              # Usage stats & limits (~250 lines)
└── views.py                  # DEPRECATED - Will be removed after testing
```

## View Class Mapping

### Module 1: `photo_analysis.py` (Lines 171-609, ~438 lines)

**Classes:**
1. `PhotoAnalysisViewSet` (171-232) - ModelViewSet for CRUD
2. `GeneratedMessageViewSet` (234-307) - ModelViewSet for messages
3. `PhotoAnalysisView` (309-522) - Main photo analysis endpoint
4. `ColorExtractionView` (524-609) - Color extraction endpoint

**Imports Needed:**
```python
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import PhotoAnalysis, GeneratedMessage
from ..serializers import (
    PhotoAnalysisSerializer,
    PhotoAnalysisCreateSerializer,
    PhotoUploadSerializer,
    ...
)
from ..permissions import CanUseAIFeature, IsOwnerOrReadOnly
from ..services import PhotoAnalysisService
from ..services.base_ai import AIServiceError, RateLimitError
from .helpers import create_success_response, create_error_response, logger
```

**Dependencies:**
- PhotoAnalysisService
- AIServiceError, RateLimitError, ValidationError
- Response helpers

---

### Module 2: `message_generation.py` (Lines 611-1059, ~448 lines)

**Classes:**
1. `MoodDetectionView` (611-700) - Mood detection
2. `GenerateMessagesView` (867-985) - Message generation
3. `GenerateHashtagsView` (987-1059) - Hashtag generation

**Also includes:**
- Message styles views
- Mood-related endpoints

**Imports Needed:**
```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import GeneratedMessage, AIUsageLog
from ..serializers import (
    GenerateMessageRequestSerializer,
    MessageGenerationRequestSerializer,
    GeneratedMessageSerializer,
)
from ..permissions import CanUseAIFeature
from ..services import MessageGenerationService
from ..services.base_ai import AIServiceError
from .helpers import create_success_response, create_error_response, logger
```

**Dependencies:**
- MessageGenerationService
- AIServiceError
- Response helpers

---

### Module 3: `recommendations.py` (Lines 702-1346, ~644 lines)

**Classes:**
1. `StyleRecommendationsView` (702-750) - Style recommendations
2. `TemplateRecommendationsView` (752-865) - Template recommendations
3. `RecommendTemplatesView` (1237-1300) - Recommend templates
4. `RecommendStylesView` (1302-1346) - Recommend styles
5. `AnalyzePhotoView` (1060-1120) - Photo analysis for recommendations
6. `ExtractColorsView` (1122-1168) - Color extraction
7. `DetectMoodView` (1170-1216) - Mood detection
8. `MessageStylesView` (1218-1235) - Available message styles

**Imports Needed:**
```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import PhotoAnalysis
from ..serializers import (
    PhotoAnalysisSerializer,
    # Add recommendation serializers
)
from ..permissions import CanUseAIFeature
from ..services import RecommendationService, PhotoAnalysisService
from ..services.base_ai import AIServiceError
from .helpers import create_success_response, create_error_response, logger
```

**Dependencies:**
- RecommendationService
- PhotoAnalysisService
- Response helpers

---

### Module 4: `usage.py` (Lines 1347-1496, ~149 lines)

**Classes:**
1. `AIUsageStatsView` (1347-1391) - Usage statistics
2. `AIUsageLimitsView` (1393-1457) - Usage limits
3. `SmartSuggestionsView` (1459-1496) - Smart suggestions

**Imports Needed:**
```python
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from django.utils import timezone

from ..models import AIUsageLog, PhotoAnalysis, GeneratedMessage
from ..serializers import (
    AIUsageStatsSerializer,
    AILimitsSerializer,
    AIUsageLogSerializer,
)
from ..permissions import CanUseAIFeature
from .helpers import create_success_response, create_error_response, logger
```

**Dependencies:**
- AIUsageLog model
- Usage serializers
- Response helpers

---

### Module 5: `__init__.py` (Export all views)

```python
"""
AI app views package.

This package organizes AI-related views into focused modules:
- photo_analysis: Photo analysis and color extraction
- message_generation: Message and hashtag generation
- recommendations: Template and style recommendations
- usage: Usage tracking and limits

Each module provides specific functionality while sharing common
helpers and response formats.
"""

from .photo_analysis import (
    PhotoAnalysisViewSet,
    GeneratedMessageViewSet,
    PhotoAnalysisView,
    ColorExtractionView,
)

from .message_generation import (
    MoodDetectionView,
    GenerateMessagesView,
    GenerateHashtagsView,
)

from .recommendations import (
    StyleRecommendationsView,
    TemplateRecommendationsView,
    RecommendTemplatesView,
    RecommendStylesView,
    AnalyzePhotoView,
    ExtractColorsView,
    DetectMoodView,
    MessageStylesView,
)

from .usage import (
    AIUsageStatsView,
    AIUsageLimitsView,
    SmartSuggestionsView,
)

from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
)

__all__ = [
    # Photo Analysis
    'PhotoAnalysisViewSet',
    'GeneratedMessageViewSet',
    'PhotoAnalysisView',
    'ColorExtractionView',
    # Message Generation
    'MoodDetectionView',
    'GenerateMessagesView',
    'GenerateHashtagsView',
    # Recommendations
    'StyleRecommendationsView',
    'TemplateRecommendationsView',
    'RecommendTemplatesView',
    'RecommendStylesView',
    'AnalyzePhotoView',
    'ExtractColorsView',
    'DetectMoodView',
    'MessageStylesView',
    # Usage
    'AIUsageStatsView',
    'AIUsageLimitsView',
    'SmartSuggestionsView',
    # Helpers
    'create_success_response',
    'create_error_response',
    'add_rate_limit_headers',
    'logger',
]
```

---

## URL Configuration Changes

**Current:** `apps/backend/src/apps/ai/urls.py`
```python
from .views import PhotoAnalysisViewSet, ...
```

**After Refactoring:**
```python
from .views import (
    PhotoAnalysisViewSet,
    PhotoAnalysisView,
    ColorExtractionView,
    # ... all other imports stay the same
)
# OR
from . import views
# Then use: views.PhotoAnalysisViewSet
```

**No changes required to URL patterns** - imports automatically resolve through `__init__.py`

---

## Migration Strategy

### Phase 1: Create New Structure (No Breaking Changes)
1. ✅ Create `views/` directory
2. ✅ Create `views/helpers.py`
3. ⏳ Create `views/photo_analysis.py`
4. ⏳ Create `views/message_generation.py`
5. ⏳ Create `views/recommendations.py`
6. ⏳ Create `views/usage.py`
7. ⏳ Create `views/__init__.py`

### Phase 2: Update Imports
8. Update `urls.py` to import from `views` package
9. Update any other files that import from `views.py`

### Phase 3: Testing
10. Run Django checks: `python manage.py check`
11. Test all AI endpoints manually or with automated tests
12. Verify no import errors

### Phase 4: Cleanup
13. Rename old `views.py` to `views_old.py` (backup)
14. After verification, delete `views_old.py`

---

## Benefits of This Refactoring

### Before:
- ❌ Single 1,496-line file
- ❌ 18 view classes mixed together
- ❌ Hard to navigate and find specific functionality
- ❌ Difficult to understand relationships
- ❌ Large git diffs on changes

### After:
- ✅ 5 focused modules (150-400 lines each)
- ✅ Logical grouping by functionality
- ✅ Easy to find specific features
- ✅ Clear module responsibilities
- ✅ Smaller, focused git diffs
- ✅ Better testability (can mock individual modules)
- ✅ Easier onboarding for new developers

---

## Testing Checklist

After refactoring, verify these endpoints still work:

**Photo Analysis:**
- [ ] POST /api/ai/photo-analyses/
- [ ] GET /api/ai/photo-analyses/
- [ ] POST /api/ai/photo-analyses/{id}/reanalyze/
- [ ] POST /api/ai/photo-analysis/
- [ ] POST /api/ai/color-extraction/

**Message Generation:**
- [ ] POST /api/ai/generate-messages/
- [ ] POST /api/ai/generate-hashtags/
- [ ] POST /api/ai/mood-detection/

**Recommendations:**
- [ ] POST /api/ai/style-recommendations/
- [ ] POST /api/ai/template-recommendations/
- [ ] POST /api/ai/recommend-templates/
- [ ] POST /api/ai/recommend-styles/

**Usage:**
- [ ] GET /api/ai/usage-stats/
- [ ] GET /api/ai/usage-limits/
- [ ] POST /api/ai/smart-suggestions/

---

## Risk Mitigation

**Risk:** Import errors breaking the application
**Mitigation:**
- Create new structure without deleting old file
- Test thoroughly before removing old file
- Keep `views_old.py` as backup during transition

**Risk:** Missing dependencies in new modules
**Mitigation:**
- Carefully analyze imports for each class
- Use IDE to verify import paths
- Run Django check command

**Risk:** URL routing breaks
**Mitigation:**
- URLs import from package, not specific file
- Python's `__init__.py` handles re-exports
- No URL pattern changes needed

---

## Implementation Status

- [x] Create `views/` directory
- [x] Create `views/helpers.py`
- [ ] Create `views/photo_analysis.py`
- [ ] Create `views/message_generation.py`
- [ ] Create `views/recommendations.py`
- [ ] Create `views/usage.py`
- [ ] Create `views/__init__.py`
- [ ] Update imports
- [ ] Test endpoints
- [ ] Remove old file

---

**Next Action:** Create `views/photo_analysis.py` with first 4 view classes
