#!/usr/bin/env python3
"""
Admin Dashboard Views Refactoring Script

This script automatically refactors apps/backend/src/apps/admin_dashboard/views.py
into a modular structure with focused files.

Usage:
    python refactor_admin_dashboard_views.py

The script will:
1. Create views/ directory in apps/backend/src/apps/admin_dashboard/
2. Split views.py into focused modules (permissions, dashboard, approvals, users, notifications)
3. Create __init__.py with proper exports
4. Backup original views.py
5. Generate verification report
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
ADMIN_APP_PATH = PROJECT_ROOT / "apps/backend/src/apps/admin_dashboard"
VIEWS_FILE = ADMIN_APP_PATH / "views.py"
VIEWS_DIR = ADMIN_APP_PATH / "views"
BACKUP_FILE = ADMIN_APP_PATH / "views_backup.py"


# Class to module mapping
CLASS_TO_MODULE = {
    # Permissions
    'IsAdminUser': 'permissions',

    # Dashboard
    'DashboardStatsView': 'dashboard',
    'RecentApprovalsView': 'dashboard',

    # Approvals
    'PendingApprovalsView': 'approvals',
    'ApproveUserPlanView': 'approvals',
    'RejectUserPlanView': 'approvals',
    'ApproveUserView': 'approvals',
    'RejectUserView': 'approvals',
    'GrantAdditionalLinksView': 'approvals',

    # Users
    'PendingUsersListView': 'users',
    'AllUsersListView': 'users',
    'UserDetailView': 'users',
    'UpdateUserNotesView': 'users',

    # Notifications
    'NotificationsListView': 'notifications',
    'MarkNotificationReadView': 'notifications',
}


MODULE_INFO = {
    'permissions': {
        'description': 'Admin permission classes',
        'classes': ['IsAdminUser'],
    },
    'dashboard': {
        'description': 'Dashboard statistics and overview',
        'classes': ['DashboardStatsView', 'RecentApprovalsView'],
    },
    'approvals': {
        'description': 'Approval workflow views',
        'classes': ['PendingApprovalsView', 'ApproveUserPlanView', 'RejectUserPlanView',
                   'ApproveUserView', 'RejectUserView', 'GrantAdditionalLinksView'],
    },
    'users': {
        'description': 'User management views',
        'classes': ['PendingUsersListView', 'AllUsersListView', 'UserDetailView', 'UpdateUserNotesView'],
    },
    'notifications': {
        'description': 'Notification management views',
        'classes': ['NotificationsListView', 'MarkNotificationReadView'],
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
    print(f"  [OK] {text}")


def print_error(text):
    print(f"  [ERROR] {text}")


def print_warning(text):
    print(f"  [WARN] {text}")


# =============================================================================
# Code Extraction Functions
# =============================================================================

def extract_class_code(source_lines, class_node):
    """Extract the complete source code for a class node."""
    start_line = class_node.lineno - 1
    end_line = class_node.end_lineno

    if class_node.decorator_list:
        first_decorator = min(d.lineno for d in class_node.decorator_list)
        start_line = first_decorator - 1

    return ''.join(source_lines[start_line:end_line])


def extract_imports_and_header(source_lines, tree):
    """Extract imports and module docstring."""
    result = {
        'docstring': '',
        'imports': [],
    }

    # Extract module docstring
    if (tree.body and
        isinstance(tree.body[0], ast.Expr) and
        isinstance(tree.body[0].value, ast.Constant) and
        isinstance(tree.body[0].value.value, str)):
        result['docstring'] = tree.body[0].value.value

    # Extract imports
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            import_lines = source_lines[node.lineno-1:node.end_lineno]
            result['imports'].append(''.join(import_lines))

    return result


def parse_views_file():
    """Parse the views.py file with AST."""
    print_step(1, "Parsing admin dashboard views.py with AST...")

    try:
        with open(VIEWS_FILE, 'r', encoding='utf-8') as f:
            source = f.read()
            source_lines = source.splitlines(keepends=True)

        tree = ast.parse(source)
        print_success(f"Successfully parsed {len(source_lines)} lines")

        header_info = extract_imports_and_header(source_lines, tree)
        module_classes = defaultdict(list)

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
                    print_success(f"  Found class: {class_name} -> {module_name}.py")
                else:
                    print_warning(f"  Class not mapped: {class_name}")

        return {
            'header': header_info,
            'module_classes': dict(module_classes),
            'source_lines': source_lines
        }

    except Exception as e:
        print_error(f"Failed to parse views.py: {e}")
        return None


# =============================================================================
# Module Generation Functions
# =============================================================================

def generate_module_imports(module_name):
    """Generate appropriate imports for each module."""

    if module_name == 'permissions':
        return '''from rest_framework import permissions
'''

    if module_name == 'dashboard':
        return '''from typing import Any, Dict
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from apps.invitations.models import Order, Invitation
from ..models import AdminNotification
from .permissions import IsAdminUser

User = get_user_model()
'''

    if module_name == 'approvals':
        return '''from typing import Dict, Optional
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from apps.invitations.models import Order
from apps.accounts.models import UserActivityLog
from ..models import UserApprovalLog, AdminNotification
from ..services import NotificationService
from .permissions import IsAdminUser

User = get_user_model()
'''

    if module_name == 'users':
        return '''from typing import Any, Dict
from django.db.models import Q, Count, Sum
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.accounts.models import UserActivityLog
from apps.invitations.models import Order
from .permissions import IsAdminUser

User = get_user_model()
'''

    if module_name == 'notifications':
        return '''from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ..models import AdminNotification
from .permissions import IsAdminUser
'''

    return ''


def create_module_file(module_name, parsed_data):
    """Create a module file with extracted classes."""
    print_success(f"  Creating {module_name}.py...")

    module_path = VIEWS_DIR / f"{module_name}.py"
    info = MODULE_INFO.get(module_name, {})

    # Build file content
    content = f'''"""
{info.get('description', 'Admin dashboard views module')}.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

'''

    # Add imports
    content += generate_module_imports(module_name)

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
Admin dashboard views package.

This package organizes admin dashboard views into focused modules:
- permissions: Admin permission classes
- dashboard: Dashboard statistics and overview
- approvals: Approval workflow views
- users: User management views
- notifications: Notification management views

Generated automatically by refactor_admin_dashboard_views.py
"""

'''

    # Add imports
    for module_name, info in MODULE_INFO.items():
        exports = info.get('classes', [])
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
    print_header("Admin Dashboard Views Refactoring (AST-based)")

    # Validate environment
    if not ADMIN_APP_PATH.exists():
        print_error(f"Admin dashboard app directory not found: {ADMIN_APP_PATH}")
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
    print_header("[SUCCESS] Refactoring Complete!")

    print("Summary:")
    print(f"  • Created {len(MODULE_INFO)} module files")
    print(f"  • Extracted {sum(len(v) for v in parsed_data['module_classes'].values())} classes")
    print(f"  • Created views/ directory at: {VIEWS_DIR}")
    print(f"  • Backup saved: {BACKUP_FILE.name}")

    print("\nNext steps:")
    print("  1. Verify imports: python -c 'from apps.admin_dashboard.views import DashboardStatsView'")
    print("  2. Run checks: cd apps/backend && python src/manage.py check")
    print("  3. Test admin endpoints")
    print("  4. Remove old views.py after verification")

    print("\nRollback if needed:")
    print(f"  cp {BACKUP_FILE} views.py && rm -rf views/")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[WARN] Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
