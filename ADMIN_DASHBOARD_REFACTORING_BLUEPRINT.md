# Admin Dashboard Views Refactoring Blueprint

**File:** `apps/backend/src/apps/admin_dashboard/views.py` (821 lines)
**Goal:** Split into focused modules of ~150-250 lines each

## Current Structure Analysis

**Total Classes:** 15 classes (1 permission class + 14 view classes)

### Class List with Line Numbers:
1. `IsAdminUser` (28-39) - Permission class
2. `DashboardStatsView` (42-113) - Dashboard statistics
3. `PendingApprovalsView` (114-167) - Pending approvals list
4. `ApproveUserPlanView` (168-274) - Approve user plan/order
5. `RejectUserPlanView` (275-391) - Reject user plan/order
6. `PendingUsersListView` (392-436) - List pending users
7. `AllUsersListView` (437-507) - List all users
8. `UserDetailView` (508-620) - User detail view
9. `ApproveUserView` (621-631) - Quick user approval
10. `RejectUserView` (632-642) - Quick user rejection
11. `NotificationsListView` (643-679) - List notifications
12. `MarkNotificationReadView` (680-701) - Mark notification as read
13. `UpdateUserNotesView` (702-724) - Update user notes
14. `GrantAdditionalLinksView` (725-779) - Grant additional links
15. `RecentApprovalsView` (780-821) - Recent approvals

## New Structure

```
apps/backend/src/apps/admin_dashboard/
├── views/
│   ├── __init__.py           # Export all views
│   ├── permissions.py        # IsAdminUser permission (~30 lines)
│   ├── dashboard.py          # Dashboard stats, recent approvals (~150 lines)
│   ├── approvals.py          # Approval workflow views (~250 lines)
│   ├── users.py              # User management views (~300 lines)
│   └── notifications.py      # Notification views (~100 lines)
└── views.py                  # Original (will be backed up)
```

## Module Breakdown

### Module 1: `permissions.py` (~30 lines)

**Classes:**
- `IsAdminUser` (lines 28-39) - Admin permission check

**Purpose:** Centralized permission classes for admin dashboard

**Imports:**
```python
from rest_framework import permissions
```

---

### Module 2: `dashboard.py` (~150 lines)

**Classes:**
- `DashboardStatsView` (lines 42-113) - Main dashboard statistics
- `RecentApprovalsView` (lines 780-821) - Recent approvals widget

**Purpose:** Dashboard overview and statistics

**Imports:**
```python
from typing import Any, Dict
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.invitations.models import Order, Invitation
from apps.accounts.models import User
from ..models import AdminNotification
from .permissions import IsAdminUser
```

**Dependencies:**
- Order, Invitation models
- User model
- AdminNotification model
- IsAdminUser permission

---

### Module 3: `approvals.py` (~300 lines)

**Classes:**
- `PendingApprovalsView` (lines 114-167) - List pending approvals
- `ApproveUserPlanView` (lines 168-274) - Approve order/plan
- `RejectUserPlanView` (lines 275-391) - Reject order/plan
- `ApproveUserView` (lines 621-631) - Quick approve user
- `RejectUserView` (lines 632-642) - Quick reject user
- `GrantAdditionalLinksView` (lines 725-779) - Grant extra links

**Purpose:** Complete approval workflow management

**Imports:**
```python
from typing import Dict, Optional
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.invitations.models import Order
from apps.accounts.models import User, UserActivityLog
from ..models import UserApprovalLog, AdminNotification
from ..services import NotificationService
from .permissions import IsAdminUser
```

**Dependencies:**
- Order model
- User, UserActivityLog models
- UserApprovalLog, AdminNotification models
- NotificationService
- IsAdminUser permission

**Business Logic:**
- Order approval/rejection workflow
- User approval/rejection
- Link grant management
- Activity logging
- Notification sending

---

### Module 4: `users.py` (~300 lines)

**Classes:**
- `PendingUsersListView` (lines 392-436) - List pending users
- `AllUsersListView` (lines 437-507) - List all users
- `UserDetailView` (lines 508-620) - User details with stats
- `UpdateUserNotesView` (lines 702-724) - Update admin notes

**Purpose:** User management and information views

**Imports:**
```python
from typing import Any, Dict
from django.db.models import Q, Count, Sum
from rest_framework import generics
from rest_framework.response import Response

from apps.accounts.models import User, UserActivityLog
from apps.invitations.models import Order
from .permissions import IsAdminUser
```

**Dependencies:**
- User, UserActivityLog models
- Order model (for user stats)
- IsAdminUser permission

**Features:**
- User listing with filtering
- User search functionality
- Detailed user statistics
- Admin notes management

---

### Module 5: `notifications.py` (~100 lines)

**Classes:**
- `NotificationsListView` (lines 643-679) - List notifications
- `MarkNotificationReadView` (lines 680-701) - Mark as read

**Purpose:** Admin notification management

**Imports:**
```python
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ..models import AdminNotification
from .permissions import IsAdminUser
```

**Dependencies:**
- AdminNotification model
- IsAdminUser permission

**Features:**
- Notification listing
- Read/unread management
- Filtering by type and status

---

### Module 6: `__init__.py` (Export all views)

```python
"""
Admin dashboard views package.

This package organizes admin dashboard views into focused modules:
- permissions: Admin permission classes
- dashboard: Dashboard statistics and overview
- approvals: Approval workflow views
- users: User management views
- notifications: Notification management views

Generated automatically by refactor_admin_dashboard_views.py
"""

from .permissions import IsAdminUser

from .dashboard import (
    DashboardStatsView,
    RecentApprovalsView,
)

from .approvals import (
    PendingApprovalsView,
    ApproveUserPlanView,
    RejectUserPlanView,
    ApproveUserView,
    RejectUserView,
    GrantAdditionalLinksView,
)

from .users import (
    PendingUsersListView,
    AllUsersListView,
    UserDetailView,
    UpdateUserNotesView,
)

from .notifications import (
    NotificationsListView,
    MarkNotificationReadView,
)

__all__ = [
    # Permissions
    'IsAdminUser',
    # Dashboard
    'DashboardStatsView',
    'RecentApprovalsView',
    # Approvals
    'PendingApprovalsView',
    'ApproveUserPlanView',
    'RejectUserPlanView',
    'ApproveUserView',
    'RejectUserView',
    'GrantAdditionalLinksView',
    # Users
    'PendingUsersListView',
    'AllUsersListView',
    'UserDetailView',
    'UpdateUserNotesView',
    # Notifications
    'NotificationsListView',
    'MarkNotificationReadView',
]
```

---

## URL Configuration Changes

**Current:** `apps/backend/src/apps/admin_dashboard/urls.py`
```python
from .views import DashboardStatsView, ...
```

**After Refactoring:**
```python
from .views import (
    DashboardStatsView,
    PendingApprovalsView,
    # ... all other imports stay the same
)
# OR
from . import views
# Then use: views.DashboardStatsView
```

**No URL pattern changes needed** - imports resolve through `__init__.py`

---

## Class to Module Mapping

```python
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
```

---

## Migration Strategy

### Phase 1: Create New Structure
1. ✅ Create `views/` directory
2. ⏳ Create `views/permissions.py`
3. ⏳ Create `views/dashboard.py`
4. ⏳ Create `views/approvals.py`
5. ⏳ Create `views/users.py`
6. ⏳ Create `views/notifications.py`
7. ⏳ Create `views/__init__.py`

### Phase 2: Update Imports
8. Update `urls.py` to import from `views` package
9. Update any other files importing from `views.py`

### Phase 3: Testing
10. Run Django checks
11. Test admin dashboard endpoints
12. Verify approval workflow
13. Test user management

### Phase 4: Cleanup
14. Backup `views.py` to `views_backup.py`
15. Remove old `views.py` after verification

---

## Benefits

### Before:
- ❌ Single 821-line file
- ❌ 15 classes mixed together
- ❌ Hard to find specific functionality
- ❌ Approval logic mixed with user management
- ❌ No clear separation of concerns

### After:
- ✅ 5 focused modules (30-300 lines each)
- ✅ Logical grouping by functionality
- ✅ Clear module responsibilities
- ✅ Approval workflow centralized
- ✅ Easy to understand and maintain
- ✅ Better testability

---

## Testing Checklist

After refactoring, verify:

**Dashboard:**
- [ ] GET /api/admin/dashboard/stats/
- [ ] GET /api/admin/dashboard/recent-approvals/

**Approvals:**
- [ ] GET /api/admin/approvals/pending/
- [ ] POST /api/admin/approvals/approve-plan/{id}/
- [ ] POST /api/admin/approvals/reject-plan/{id}/
- [ ] POST /api/admin/users/{id}/approve/
- [ ] POST /api/admin/users/{id}/reject/
- [ ] POST /api/admin/approvals/grant-links/{id}/

**Users:**
- [ ] GET /api/admin/users/pending/
- [ ] GET /api/admin/users/all/
- [ ] GET /api/admin/users/{id}/
- [ ] PUT /api/admin/users/{id}/notes/

**Notifications:**
- [ ] GET /api/admin/notifications/
- [ ] POST /api/admin/notifications/{id}/mark-read/

---

## Risk Mitigation

**Risk:** Breaking approval workflow
**Mitigation:**
- Thoroughly test approval/rejection flows
- Keep backup file
- Test with staging data first

**Risk:** Import errors
**Mitigation:**
- Careful dependency management
- Test imports before deployment
- Use relative imports within package

**Risk:** Permission issues
**Mitigation:**
- Test permission class in all views
- Verify IsAdminUser works correctly
- Test unauthorized access

---

## Implementation Status

- [ ] Create `views/` directory
- [ ] Create `views/permissions.py`
- [ ] Create `views/dashboard.py`
- [ ] Create `views/approvals.py`
- [ ] Create `views/users.py`
- [ ] Create `views/notifications.py`
- [ ] Create `views/__init__.py`
- [ ] Update imports
- [ ] Test endpoints
- [ ] Remove old file

---

**Next Action:** Create automated refactoring script for admin dashboard views
