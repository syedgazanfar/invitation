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

from .permissions import (
    IsAdminUser,
)

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
    'AllUsersListView',
    'ApproveUserPlanView',
    'ApproveUserView',
    'DashboardStatsView',
    'GrantAdditionalLinksView',
    'IsAdminUser',
    'MarkNotificationReadView',
    'NotificationsListView',
    'PendingApprovalsView',
    'PendingUsersListView',
    'RecentApprovalsView',
    'RejectUserPlanView',
    'RejectUserView',
    'UpdateUserNotesView',
    'UserDetailView',
]
