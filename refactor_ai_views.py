#!/usr/bin/env python3
"""
AI Views Refactoring Script

This script automatically refactors apps/backend/src/apps/ai/views.py
into a modular structure with multiple focused files.

Usage:
    python refactor_ai_views.py

The script will:
1. Create views/ directory in apps/backend/src/apps/ai/
2. Split views.py into focused modules
3. Create __init__.py with proper exports
4. Backup original views.py as views_backup.py
5. Generate a verification report

Safety:
- Creates backup before making changes
- Validates file structure before proceeding
- Provides rollback instructions if needed
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
AI_APP_PATH = PROJECT_ROOT / "apps/backend/src/apps/ai"
VIEWS_FILE = AI_APP_PATH / "views.py"
VIEWS_DIR = AI_APP_PATH / "views"
BACKUP_FILE = AI_APP_PATH / "views_backup.py"


# =============================================================================
# Module Definitions
# =============================================================================

MODULES = {
    'helpers.py': {
        'description': 'Response helpers and constants',
        'line_range': (1, 170),
        'classes': [],
        'functions': ['create_success_response', 'create_error_response', 'add_rate_limit_headers'],
        'imports': """import logging
from typing import Dict, Any, Optional

from rest_framework import status
from rest_framework.response import Response
""",
        'exports': ['create_success_response', 'create_error_response', 'add_rate_limit_headers', 'logger']
    },

    'photo_analysis.py': {
        'description': 'Photo analysis and color extraction views',
        'line_range': (171, 609),
        'classes': ['PhotoAnalysisViewSet', 'GeneratedMessageViewSet', 'PhotoAnalysisView', 'ColorExtractionView'],
        'imports': """import time
import uuid
import logging
from typing import Dict, Any, Optional, List

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth.models import AbstractUser

from ..models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from ..serializers import (
    PhotoAnalysisSerializer,
    PhotoAnalysisCreateSerializer,
    PhotoUploadSerializer,
    PhotoAnalysisResponseSerializer,
    GeneratedMessageSerializer,
)
from ..permissions import CanUseAIFeature, IsOwnerOrReadOnly
from ..services import PhotoAnalysisService, MessageGenerationService
from ..services.base_ai import AIServiceError, RateLimitError
from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_IMAGE_TYPES,
)
""",
        'exports': ['PhotoAnalysisViewSet', 'GeneratedMessageViewSet', 'PhotoAnalysisView', 'ColorExtractionView']
    },

    'message_generation.py': {
        'description': 'Message and hashtag generation views',
        'line_range': (610, 1059),
        'classes': ['MoodDetectionView', 'GenerateMessagesView', 'GenerateHashtagsView',
                   'AnalyzePhotoView', 'ExtractColorsView', 'DetectMoodView', 'MessageStylesView'],
        'imports': """import logging
from typing import Dict, Any, Optional, List

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import GeneratedMessage, AIUsageLog, PhotoAnalysis
from ..serializers import (
    GenerateMessageRequestSerializer,
    MessageGenerationRequestSerializer,
    GeneratedMessageSerializer,
    PhotoAnalysisSerializer,
)
from ..permissions import CanUseAIFeature
from ..services import MessageGenerationService, PhotoAnalysisService
from ..services.base_ai import AIServiceError, RateLimitError
from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
)
""",
        'exports': ['MoodDetectionView', 'GenerateMessagesView', 'GenerateHashtagsView',
                   'AnalyzePhotoView', 'ExtractColorsView', 'DetectMoodView', 'MessageStylesView']
    },

    'recommendations.py': {
        'description': 'Template and style recommendation views',
        'line_range': (700, 866, 1237, 1346),  # Non-contiguous ranges
        'classes': ['StyleRecommendationsView', 'TemplateRecommendationsView',
                   'RecommendTemplatesView', 'RecommendStylesView'],
        'imports': """import logging
from typing import Dict, Any, Optional, List

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import PhotoAnalysis
from ..serializers import PhotoAnalysisSerializer
from ..permissions import CanUseAIFeature
from ..services import RecommendationService, PhotoAnalysisService
from ..services.base_ai import AIServiceError
from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
)
""",
        'exports': ['StyleRecommendationsView', 'TemplateRecommendationsView',
                   'RecommendTemplatesView', 'RecommendStylesView']
    },

    'usage.py': {
        'description': 'Usage tracking and limits views',
        'line_range': (1347, 1496),
        'classes': ['AIUsageStatsView', 'AIUsageLimitsView', 'SmartSuggestionsView'],
        'imports': """import logging
from typing import Dict, Any, Optional

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
from .helpers import (
    create_success_response,
    create_error_response,
    logger,
)
""",
        'exports': ['AIUsageStatsView', 'AIUsageLimitsView', 'SmartSuggestionsView']
    }
}


# =============================================================================
# Helper Functions
# =============================================================================

def print_header(text):
    """Print formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_step(step_num, text):
    """Print formatted step."""
    print(f"[Step {step_num}] {text}")


def print_success(text):
    """Print success message."""
    print(f"  ✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"  ✗ ERROR: {text}")


def validate_environment():
    """Validate that we're in the correct directory and files exist."""
    print_step(1, "Validating environment...")

    if not AI_APP_PATH.exists():
        print_error(f"AI app directory not found: {AI_APP_PATH}")
        print(f"\nExpected path: {AI_APP_PATH}")
        print(f"Current working directory: {os.getcwd()}")
        print("\nPlease run this script from the project root directory.")
        return False

    print_success(f"AI app directory found: {AI_APP_PATH}")

    if not VIEWS_FILE.exists():
        print_error(f"views.py not found: {VIEWS_FILE}")
        return False

    print_success(f"views.py found: {VIEWS_FILE}")

    # Check file size
    file_size = VIEWS_FILE.stat().st_size
    print_success(f"views.py size: {file_size:,} bytes")

    if file_size < 10000:
        print_error("views.py seems too small. Expected ~60KB+")
        return False

    return True


def create_backup():
    """Create backup of original views.py."""
    print_step(2, "Creating backup...")

    if BACKUP_FILE.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_backup = AI_APP_PATH / f"views_backup_{timestamp}.py"
        shutil.copy2(VIEWS_FILE, new_backup)
        print_success(f"Existing backup preserved: {new_backup.name}")

    shutil.copy2(VIEWS_FILE, BACKUP_FILE)
    print_success(f"Backup created: {BACKUP_FILE.name}")
    return True


def read_views_file():
    """Read the original views.py file."""
    print_step(3, "Reading original views.py...")

    try:
        with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        print_success(f"Read {len(lines)} lines from views.py")
        return lines
    except Exception as e:
        print_error(f"Failed to read views.py: {e}")
        return None


def extract_lines(lines, line_range):
    """Extract lines from a range (1-indexed to 0-indexed)."""
    if isinstance(line_range[0], tuple):
        # Handle non-contiguous ranges
        extracted = []
        for start, end in [line_range[i:i+2] for i in range(0, len(line_range), 2)]:
            extracted.extend(lines[start-1:end])
        return extracted
    else:
        start, end = line_range
        return lines[start-1:end]


def create_views_directory():
    """Create the views/ directory."""
    print_step(4, "Creating views/ directory...")

    if VIEWS_DIR.exists():
        print_success(f"views/ directory already exists")
    else:
        VIEWS_DIR.mkdir(parents=True, exist_ok=True)
        print_success(f"Created views/ directory")

    return True


def create_module_file(module_name, config, lines):
    """Create a module file with extracted content."""
    module_path = VIEWS_DIR / module_name

    # Extract content
    if 'line_range' in config:
        content_lines = extract_lines(lines, config['line_range'])
    else:
        content_lines = []

    # Build file content
    file_content = f'''"""
{config['description'].capitalize()}.

This module is part of the refactored AI views structure.
Generated automatically by refactor_ai_views.py
"""

{config['imports']}
'''

    # Add the extracted code
    if content_lines:
        # Skip the imports/header from original file
        code_start = 0
        for i, line in enumerate(content_lines):
            if line.strip().startswith('class ') or line.strip().startswith('def ') and not line.strip().startswith('def __'):
                code_start = i
                break

        file_content += '\n'.join(content_lines[code_start:])

    # Write file
    try:
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        return True
    except Exception as e:
        print_error(f"Failed to create {module_name}: {e}")
        return False


def create_init_file():
    """Create __init__.py with all exports."""
    print_step(5, "Creating __init__.py...")

    init_content = '''"""
AI app views package.

This package organizes AI-related views into focused modules:
- helpers: Response helpers and constants
- photo_analysis: Photo analysis and color extraction
- message_generation: Message and hashtag generation
- recommendations: Template and style recommendations
- usage: Usage tracking and limits

Generated automatically by refactor_ai_views.py
"""

'''

    # Add imports from each module
    for module_name, config in MODULES.items():
        module_base = module_name.replace('.py', '')
        exports = config['exports']

        init_content += f"from .{module_base} import (\n"
        for export in exports:
            init_content += f"    {export},\n"
        init_content += ")\n\n"

    # Add __all__
    all_exports = []
    for config in MODULES.values():
        all_exports.extend(config['exports'])

    init_content += "__all__ = [\n"
    for export in sorted(all_exports):
        init_content += f"    '{export}',\n"
    init_content += "]\n"

    # Write file
    init_path = VIEWS_DIR / "__init__.py"
    try:
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(init_content)
        print_success("Created __init__.py with exports")
        return True
    except Exception as e:
        print_error(f"Failed to create __init__.py: {e}")
        return False


def generate_report():
    """Generate a refactoring report."""
    print_step(6, "Generating report...")

    report_path = PROJECT_ROOT / "REFACTORING_REPORT.md"

    report_content = f"""# AI Views Refactoring Report

**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Status:** Completed Successfully

## Summary

Original file `apps/backend/src/apps/ai/views.py` (1,496 lines) has been refactored into a modular structure.

## New Structure

```
apps/backend/src/apps/ai/
├── views/
│   ├── __init__.py          # Package exports
│   ├── helpers.py           # Response helpers & constants
│   ├── photo_analysis.py    # Photo analysis views
│   ├── message_generation.py # Message generation views
│   ├── recommendations.py   # Recommendation views
│   └── usage.py            # Usage tracking views
└── views_backup.py         # Original file backup
```

## Module Breakdown

"""

    for module_name, config in MODULES.items():
        report_content += f"""### {module_name}
**Description:** {config['description']}
**Classes:** {len(config['classes'])}
**Exports:** {', '.join(config['exports'])}

"""

    report_content += """## Verification Checklist

Before deploying, verify:

- [ ] All files created successfully
- [ ] No import errors: `python manage.py check`
- [ ] Test endpoints still work
- [ ] URLs resolve correctly
- [ ] No breaking changes in production

## Rollback Instructions

If issues occur:

1. Stop the application
2. Restore from backup:
   ```bash
   cd apps/backend/src/apps/ai
   cp views_backup.py views.py
   rm -rf views/
   ```
3. Restart the application

## Next Steps

1. Update imports in urls.py if needed
2. Run Django checks: `python manage.py check`
3. Test all AI endpoints
4. Run automated tests
5. Deploy with confidence

## Files Modified

- Created: `apps/backend/src/apps/ai/views/` directory
- Created: 5 new module files + __init__.py
- Backed up: `views.py` → `views_backup.py`
- Original `views.py` remains unchanged (will be removed after verification)
"""

    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        print_success(f"Report generated: {report_path.name}")
        return True
    except Exception as e:
        print_error(f"Failed to generate report: {e}")
        return False


def main():
    """Main refactoring function."""
    print_header("AI Views Refactoring Script")

    print("This script will refactor apps/backend/src/apps/ai/views.py")
    print("into a modular structure with multiple focused files.")
    print(f"\nTarget directory: {AI_APP_PATH}")

    # Validation
    if not validate_environment():
        print("\n❌ Environment validation failed. Exiting.")
        return 1

    # Create backup
    if not create_backup():
        print("\n❌ Backup creation failed. Exiting.")
        return 1

    # Read original file
    lines = read_views_file()
    if not lines:
        print("\n❌ Failed to read original file. Exiting.")
        return 1

    # Create views directory
    if not create_views_directory():
        print("\n❌ Failed to create views directory. Exiting.")
        return 1

    # Create module files
    print_step(5, "Creating module files...")
    for module_name, config in MODULES.items():
        if module_name == 'helpers.py':
            # helpers.py already created manually with better content
            if (VIEWS_DIR / module_name).exists():
                print_success(f"  {module_name} (already exists)")
                continue

        if create_module_file(module_name, config, lines):
            print_success(f"  {module_name}")
        else:
            print_error(f"  {module_name}")
            return 1

    # Create __init__.py
    if not create_init_file():
        print("\n❌ Failed to create __init__.py. Exiting.")
        return 1

    # Generate report
    if not generate_report():
        print("\n⚠️  Warning: Failed to generate report, but refactoring completed.")

    # Success!
    print_header("✅ Refactoring Complete!")

    print("Summary:")
    print(f"  • Created views/ directory: {VIEWS_DIR}")
    print(f"  • Created {len(MODULES)} module files")
    print(f"  • Created __init__.py with exports")
    print(f"  • Backup saved: {BACKUP_FILE.name}")
    print(f"  • Report saved: REFACTORING_REPORT.md")

    print("\n⚠️  IMPORTANT: The original views.py still exists!")
    print("     After testing, you can safely remove it.")

    print("\nNext steps:")
    print("  1. Test imports: python -c 'from apps.ai.views import PhotoAnalysisViewSet'")
    print("  2. Run checks: cd apps/backend && python src/manage.py check")
    print("  3. Test endpoints with Postman or curl")
    print("  4. If all works, remove old views.py")

    print("\nRollback if needed:")
    print(f"  cp {BACKUP_FILE.name} views.py && rm -rf views/")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Changes may be incomplete.")
        print(f"   Backup available at: {BACKUP_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        print(f"   Backup available at: {BACKUP_FILE}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
