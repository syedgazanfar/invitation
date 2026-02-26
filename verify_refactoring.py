#!/usr/bin/env python3
"""
Refactoring Verification Script

This script verifies that the AI views refactoring was successful.

Usage:
    python verify_refactoring.py

Checks:
1. All module files exist
2. All classes can be imported
3. No syntax errors
4. Django checks pass
5. Module sizes are reasonable
"""

import os
import sys
import subprocess
from pathlib import Path


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent
AI_APP_PATH = PROJECT_ROOT / "apps/backend/src/apps/ai"
VIEWS_DIR = AI_APP_PATH / "views"


# Expected structure
EXPECTED_MODULES = {
    'helpers.py': {
        'exports': ['create_success_response', 'create_error_response', 'add_rate_limit_headers'],
        'min_lines': 100,
        'max_lines': 200,
    },
    'photo_analysis.py': {
        'exports': ['PhotoAnalysisViewSet', 'GeneratedMessageViewSet', 'PhotoAnalysisView', 'ColorExtractionView'],
        'min_lines': 300,
        'max_lines': 500,
    },
    'message_generation.py': {
        'exports': ['MoodDetectionView', 'GenerateMessagesView', 'GenerateHashtagsView'],
        'min_lines': 250,
        'max_lines': 500,
    },
    'recommendations.py': {
        'exports': ['StyleRecommendationsView', 'TemplateRecommendationsView',
                   'RecommendTemplatesView', 'RecommendStylesView'],
        'min_lines': 200,
        'max_lines': 400,
    },
    'usage.py': {
        'exports': ['AIUsageStatsView', 'AIUsageLimitsView', 'SmartSuggestionsView'],
        'min_lines': 100,
        'max_lines': 300,
    },
}


# =============================================================================
# Utility Functions
# =============================================================================

def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_check(text):
    print(f"[CHECK] {text}")


def print_success(text):
    print(f"  ✓ {text}")


def print_error(text):
    print(f"  ✗ {text}")


def print_warning(text):
    print(f"  ⚠  {text}")


# =============================================================================
# Verification Functions
# =============================================================================

def check_directory_structure():
    """Check that views/ directory and files exist."""
    print_check("Verifying directory structure...")

    if not VIEWS_DIR.exists():
        print_error(f"views/ directory not found: {VIEWS_DIR}")
        return False

    print_success(f"views/ directory exists")

    # Check __init__.py
    init_file = VIEWS_DIR / "__init__.py"
    if not init_file.exists():
        print_error("__init__.py not found in views/")
        return False

    print_success("__init__.py exists")

    # Check module files
    all_exist = True
    for module_name in EXPECTED_MODULES.keys():
        module_path = VIEWS_DIR / module_name
        if module_path.exists():
            print_success(f"{module_name} exists")
        else:
            print_error(f"{module_name} not found")
            all_exist = False

    return all_exist


def check_file_sizes():
    """Check that module files are reasonable sizes."""
    print_check("Verifying file sizes...")

    all_ok = True
    for module_name, config in EXPECTED_MODULES.items():
        module_path = VIEWS_DIR / module_name
        if not module_path.exists():
            continue

        with open(module_path, 'r', encoding='utf-8') as f:
            line_count = len(f.readlines())

        min_lines = config['min_lines']
        max_lines = config['max_lines']

        if min_lines <= line_count <= max_lines:
            print_success(f"{module_name}: {line_count} lines (OK)")
        elif line_count < min_lines:
            print_warning(f"{module_name}: {line_count} lines (expected >={min_lines})")
            all_ok = False
        else:
            print_warning(f"{module_name}: {line_count} lines (expected <={max_lines})")

    return all_ok


def check_syntax():
    """Check for syntax errors in all modules."""
    print_check("Checking for syntax errors...")

    all_ok = True
    for module_name in EXPECTED_MODULES.keys():
        module_path = VIEWS_DIR / module_name

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(module_path)],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                print_success(f"{module_name}: No syntax errors")
            else:
                print_error(f"{module_name}: Syntax error\n{result.stderr}")
                all_ok = False

        except subprocess.TimeoutExpired:
            print_error(f"{module_name}: Compilation timeout")
            all_ok = False
        except Exception as e:
            print_error(f"{module_name}: {e}")
            all_ok = False

    return all_ok


def check_imports():
    """Check that all classes can be imported."""
    print_check("Verifying imports...")

    # Add project root to Python path
    sys.path.insert(0, str(PROJECT_ROOT))

    all_ok = True
    for module_name, config in EXPECTED_MODULES.items():
        module_path = f"apps.backend.src.apps.ai.views.{module_name.replace('.py', '')}"

        for export_name in config['exports']:
            try:
                # Dynamic import
                parts = module_path.split('.')
                module = __import__(module_path, fromlist=[export_name])
                obj = getattr(module, export_name)

                print_success(f"Import successful: {export_name} from {module_name}")

            except ImportError as e:
                print_error(f"Import failed: {export_name} from {module_name}")
                print(f"    Error: {e}")
                all_ok = False
            except AttributeError as e:
                print_error(f"Class not found: {export_name} in {module_name}")
                all_ok = False
            except Exception as e:
                print_error(f"Unexpected error importing {export_name}: {e}")
                all_ok = False

    return all_ok


def check_django():
    """Run Django system checks."""
    print_check("Running Django checks...")

    manage_py = PROJECT_ROOT / "apps/backend/src/manage.py"

    if not manage_py.exists():
        print_warning("manage.py not found, skipping Django checks")
        return True

    try:
        result = subprocess.run(
            [sys.executable, str(manage_py), 'check'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(manage_py.parent)
        )

        if result.returncode == 0:
            print_success("Django checks passed")
            print(f"    {result.stdout.strip()}")
            return True
        else:
            print_error("Django checks failed")
            print(f"    {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print_warning("Django check timeout (30s)")
        return False
    except Exception as e:
        print_error(f"Failed to run Django checks: {e}")
        return False


def check_backup_exists():
    """Check that backup file exists."""
    print_check("Verifying backup...")

    backup_file = AI_APP_PATH / "views_backup.py"

    if backup_file.exists():
        size = backup_file.stat().st_size
        print_success(f"Backup exists: views_backup.py ({size:,} bytes)")
        return True
    else:
        print_warning("Backup not found: views_backup.py")
        return False


def generate_report(results):
    """Generate verification report."""
    print_header("Verification Report")

    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r)
    failed_checks = total_checks - passed_checks

    print(f"Total Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")

    print("\nDetailed Results:")
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {check_name}")

    if failed_checks == 0:
        print("\n" + "="*70)
        print("  ✅ ALL CHECKS PASSED - REFACTORING SUCCESSFUL!")
        print("="*70)
        print("\nNext steps:")
        print("  1. Test endpoints manually or with automated tests")
        print("  2. If all works, remove old views.py:")
        print("     rm apps/backend/src/apps/ai/views.py")
        print("  3. Keep backup for at least 30 days")
        return 0
    else:
        print("\n" + "="*70)
        print(f"  ⚠️  {failed_checks} CHECKS FAILED - REVIEW REQUIRED")
        print("="*70)
        print("\nRecommended actions:")
        print("  1. Review error messages above")
        print("  2. Fix issues manually or rollback:")
        print("     cd apps/backend/src/apps/ai")
        print("     cp views_backup.py views.py")
        print("     rm -rf views/")
        return 1


# =============================================================================
# Main Execution
# =============================================================================

def main():
    """Run all verification checks."""
    print_header("Refactoring Verification Script")

    print(f"Target: {VIEWS_DIR}")
    print(f"Python: {sys.version}")

    results = {}

    # Run all checks
    results['Directory Structure'] = check_directory_structure()
    results['File Sizes'] = check_file_sizes()
    results['Syntax Errors'] = check_syntax()
    results['Imports'] = check_imports()
    results['Django Checks'] = check_django()
    results['Backup Exists'] = check_backup_exists()

    # Generate report
    exit_code = generate_report(results)

    return exit_code


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
