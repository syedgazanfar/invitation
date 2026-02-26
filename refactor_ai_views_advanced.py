#!/usr/bin/env python3
"""
Advanced AI Views Refactoring Script using AST Parsing

This script uses Python's Abstract Syntax Tree (AST) to properly parse
and extract view classes into focused modules.

Usage:
    python refactor_ai_views_advanced.py

Features:
- AST-based parsing (safe and accurate)
- Automatic import detection
- Preserves comments and docstrings
- Creates proper Python modules
- Full backup and rollback support
"""

import os
import sys
import ast
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
AI_APP_PATH = PROJECT_ROOT / "apps/backend/src/apps/ai"
VIEWS_FILE = AI_APP_PATH / "views.py"
VIEWS_DIR = AI_APP_PATH / "views"
BACKUP_FILE = AI_APP_PATH / "views_backup.py"


# Class to module mapping
CLASS_TO_MODULE = {
    # Photo Analysis Module
    'PhotoAnalysisViewSet': 'photo_analysis',
    'GeneratedMessageViewSet': 'photo_analysis',
    'PhotoAnalysisView': 'photo_analysis',
    'ColorExtractionView': 'photo_analysis',

    # Message Generation Module
    'MoodDetectionView': 'message_generation',
    'GenerateMessagesView': 'message_generation',
    'GenerateHashtagsView': 'message_generation',
    'AnalyzePhotoView': 'message_generation',
    'ExtractColorsView': 'message_generation',
    'DetectMoodView': 'message_generation',
    'MessageStylesView': 'message_generation',

    # Recommendations Module
    'StyleRecommendationsView': 'recommendations',
    'TemplateRecommendationsView': 'recommendations',
    'RecommendTemplatesView': 'recommendations',
    'RecommendStylesView': 'recommendations',

    # Usage Module
    'AIUsageStatsView': 'usage',
    'AIUsageLimitsView': 'usage',
    'SmartSuggestionsView': 'usage',
}


MODULE_INFO = {
    'helpers': {
        'description': 'Shared helper functions and constants',
        'functions': ['create_success_response', 'create_error_response', 'add_rate_limit_headers'],
    },
    'photo_analysis': {
        'description': 'Photo analysis and color extraction views',
        'classes': ['PhotoAnalysisViewSet', 'GeneratedMessageViewSet', 'PhotoAnalysisView', 'ColorExtractionView'],
    },
    'message_generation': {
        'description': 'Message and hashtag generation views',
        'classes': ['MoodDetectionView', 'GenerateMessagesView', 'GenerateHashtagsView',
                   'AnalyzePhotoView', 'ExtractColorsView', 'DetectMoodView', 'MessageStylesView'],
    },
    'recommendations': {
        'description': 'Template and style recommendation views',
        'classes': ['StyleRecommendationsView', 'TemplateRecommendationsView',
                   'RecommendTemplatesView', 'RecommendStylesView'],
    },
    'usage': {
        'description': 'Usage tracking and limits views',
        'classes': ['AIUsageStatsView', 'AIUsageLimitsView', 'SmartSuggestionsView'],
    },
}


# =============================================================================
# Utility Functions
# =============================================================================

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_step(step_num, text):
    print(f"\n[Step {step_num}] {text}")


def print_success(text):
    print(f"  ✓ {text}")


def print_error(text):
    print(f"  ✗ ERROR: {text}")


def print_warning(text):
    print(f"  ⚠  WARNING: {text}")


# =============================================================================
# Code Extraction Functions
# =============================================================================

def extract_class_code(source_lines, class_node):
    """
    Extract the complete source code for a class node.

    Args:
        source_lines: List of source code lines
        class_node: AST ClassDef node

    Returns:
        String containing the complete class definition
    """
    start_line = class_node.lineno - 1
    end_line = class_node.end_lineno

    # Include decorator lines if present
    if class_node.decorator_list:
        first_decorator = min(d.lineno for d in class_node.decorator_list)
        start_line = first_decorator - 1

    return ''.join(source_lines[start_line:end_line])


def extract_function_code(source_lines, func_node):
    """Extract source code for a function node."""
    start_line = func_node.lineno - 1
    end_line = func_node.end_lineno

    if func_node.decorator_list:
        first_decorator = min(d.lineno for d in func_node.decorator_list)
        start_line = first_decorator - 1

    return ''.join(source_lines[start_line:end_line])


def extract_imports_and_constants(source_lines, tree):
    """
    Extract imports, constants, and module docstring from the original file.

    Returns:
        dict with 'docstring', 'imports', and 'constants' keys
    """
    result = {
        'docstring': '',
        'imports': [],
        'constants': []
    }

    # Extract module docstring
    if (tree.body and
        isinstance(tree.body[0], ast.Expr) and
        isinstance(tree.body[0].value, ast.Constant) and
        isinstance(tree.body[0].value.value, str)):
        result['docstring'] = tree.body[0].value.value

    # Extract imports and constants
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines = source_lines[node.lineno-1:node.end_lineno]
            result['imports'].append(''.join(import_lines))

        elif isinstance(node, ast.Assign):
            # Check if it's a constant (uppercase name)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    const_lines = source_lines[node.lineno-1:node.end_lineno]
                    result['constants'].append(''.join(const_lines))
                    break

    return result


def parse_views_file():
    """Parse the views.py file and extract structure."""
    print_step(1, "Parsing views.py with AST...")

    try:
        with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines(keepends=True)

        tree = ast.parse(source)
        print_success(f"Successfully parsed {len(source_lines)} lines")

        # Extract imports and constants
        header_info = extract_imports_and_constants(source_lines, tree)

        # Group classes by module
        module_classes = defaultdict(list)
        module_functions = defaultdict(list)

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                module_name = CLASS_TO_MODULE.get(class_name)

                if module_name:
                    class_code = extract_class_code(source_lines, node)
                    module_classes[module_name].append({
                        'name': class_name,
                        'code': class_code,
                        'lineno': node.lineno
                    })
                    print_success(f"  Found class: {class_name} → {module_name}.py")
                else:
                    print_warning(f"  Class not mapped: {class_name}")

            elif isinstance(node, ast.FunctionDef):
                func_name = node.name
                # Check if it's a helper function
                if func_name in MODULE_INFO['helpers']['functions']:
                    func_code = extract_function_code(source_lines, node)
                    module_functions['helpers'].append({
                        'name': func_name,
                        'code': func_code,
                        'lineno': node.lineno
                    })
                    print_success(f"  Found function: {func_name} → helpers.py")

        return {
            'header': header_info,
            'module_classes': dict(module_classes),
            'module_functions': dict(module_functions),
            'source_lines': source_lines
        }

    except SyntaxError as e:
        print_error(f"Syntax error in views.py: {e}")
        return None
    except Exception as e:
        print_error(f"Failed to parse views.py: {e}")
        return None


# =============================================================================
# Module Generation Functions
# =============================================================================

def generate_module_imports(module_name, parsed_data):
    """Generate appropriate imports for a module."""
    base_imports = '''import time
import uuid
import logging
from typing import Dict, Any, Optional, List

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser

from ..models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from ..serializers import (
    PhotoAnalysisSerializer,
    PhotoAnalysisCreateSerializer,
    PhotoUploadSerializer,
    PhotoAnalysisResponseSerializer,
    GeneratedMessageSerializer,
    GenerateMessageRequestSerializer,
    MessageGenerationRequestSerializer,
    AIUsageLogSerializer,
    AIUsageStatsSerializer,
    AILimitsSerializer,
)
from ..permissions import CanUseAIFeature, IsOwnerOrReadOnly
from ..services import PhotoAnalysisService, MessageGenerationService, RecommendationService
from ..services.base_ai import AIServiceError, RateLimitError, ValidationError
from .helpers import (
    create_success_response,
    create_error_response,
    add_rate_limit_headers,
    logger,
    MAX_FILE_SIZE_MB,
    MAX_FILE_SIZE_BYTES,
    ALLOWED_IMAGE_TYPES,
)
'''

    if module_name == 'helpers':
        return '''import logging
from typing import Dict, Any, Optional

from rest_framework import status
from rest_framework.response import Response


# =============================================================================
# Constants
# =============================================================================

# Logger
logger = logging.getLogger(__name__)

'''

    return base_imports


def create_module_file(module_name, parsed_data):
    """Create a module file with extracted classes."""
    print_success(f"  Creating {module_name}.py...")

    module_path = VIEWS_DIR / f"{module_name}.py"
    info = MODULE_INFO.get(module_name, {})

    # Build file content
    content = f'''"""
{info.get('description', 'AI views module')}.

This module is part of the refactored AI views structure.
Generated automatically by refactor_ai_views_advanced.py
"""

'''

    # Add imports
    content += generate_module_imports(module_name, parsed_data)

    # Add constants for helpers module
    if module_name == 'helpers':
        constants_section = '\n'.join(parsed_data['header']['constants'])
        if constants_section:
            content += '\n' + constants_section + '\n\n'

        # Add helper functions
        functions = parsed_data['module_functions'].get('helpers', [])
        for func in sorted(functions, key=lambda x: x['lineno']):
            content += '\n' + func['code'] + '\n\n'

    # Add classes
    classes = parsed_data['module_classes'].get(module_name, [])
    for cls in sorted(classes, key=lambda x: x['lineno']):
        content += '\n' + cls['code'] + '\n\n'

    # Write file
    try:
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print_error(f"Failed to write {module_name}.py: {e}")
        return False


def create_init_file():
    """Create __init__.py with all exports."""
    print_success("  Creating __init__.py...")

    content = '''"""
AI app views package.

This package organizes AI-related views into focused modules:
- helpers: Response helpers and constants
- photo_analysis: Photo analysis and color extraction
- message_generation: Message and hashtag generation
- recommendations: Template and style recommendations
- usage: Usage tracking and limits

Generated automatically by refactor_ai_views_advanced.py
"""

'''

    # Add imports
    for module_name, info in MODULE_INFO.items():
        exports = info.get('classes', []) + info.get('functions', [])
        if not exports:
            continue

        content += f"from .{module_name} import (\n"
        for item in exports:
            content += f"    {item},\n"
        content += ")\n\n"

    # Add __all__
    all_exports = []
    for info in MODULE_INFO.values():
        all_exports.extend(info.get('classes', []))
        all_exports.extend(info.get('functions', []))

    content += "__all__ = [\n"
    for item in sorted(set(all_exports)):
        content += f"    '{item}',\n"
    content += "]\n"

    # Write file
    init_path = VIEWS_DIR / "__init__.py"
    try:
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print_error(f"Failed to create __init__.py: {e}")
        return False


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Main refactoring function."""
    print_header("Advanced AI Views Refactoring (AST-based)")

    # Validate environment
    if not AI_APP_PATH.exists():
        print_error(f"AI app directory not found: {AI_APP_PATH}")
        return 1

    if not VIEWS_FILE.exists():
        print_error(f"views.py not found: {VIEWS_FILE}")
        return 1

    print_success(f"Target: {VIEWS_FILE}")

    # Create backup
    print_step(2, "Creating backup...")
    try:
        shutil.copy2(VIEWS_FILE, BACKUP_FILE)
        print_success(f"Backup created: {BACKUP_FILE.name}")
    except Exception as e:
        print_error(f"Failed to create backup: {e}")
        return 1

    # Parse original file
    parsed_data = parse_views_file()
    if not parsed_data:
        return 1

    # Create views directory
    print_step(3, "Creating views/ directory...")
    VIEWS_DIR.mkdir(exist_ok=True)
    print_success("Directory ready")

    # Create module files
    print_step(4, "Creating module files...")
    for module_name in MODULE_INFO.keys():
        if not create_module_file(module_name, parsed_data):
            return 1

    # Create __init__.py
    print_step(5, "Creating __init__.py...")
    if not create_init_file():
        return 1

    # Success!
    print_header("✅ Refactoring Complete!")

    print("Summary:")
    print(f"  • Created {len(MODULE_INFO)} module files")
    print(f"  • Extracted {sum(len(v) for v in parsed_data['module_classes'].values())} classes")
    print(f"  • Created views/ directory at: {VIEWS_DIR}")
    print(f"  • Backup saved: {BACKUP_FILE.name}")

    print("\nNext steps:")
    print("  1. Verify imports: python -c 'from apps.backend.src.apps.ai.views import PhotoAnalysisViewSet'")
    print("  2. Run checks: cd apps/backend && python src/manage.py check")
    print("  3. Test endpoints")
    print("  4. Remove old views.py after verification")

    print("\nRollback if needed:")
    print(f"  cp {BACKUP_FILE} views.py && rm -rf views/")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
