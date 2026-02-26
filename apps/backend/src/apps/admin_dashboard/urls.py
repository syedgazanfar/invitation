"""
URL configuration for admin dashboard app

This module defines all API endpoints for the admin dashboard,
including user management, order management, notifications, and
real-time WebSocket connections.
"""
from django.urls import path
from . import views


urlpatterns = [
    # Dashboard Statistics
    path('dashboard/', views.DashboardStatsView.as_view(), name='admin_dashboard_stats'),
    
    # Pending Approvals
    path('approvals/pending/', views.PendingApprovalsView.as_view(), name='admin_pending_approvals'),
    path('approvals/recent/', views.RecentApprovalsView.as_view(), name='admin_recent_approvals'),
    
    # User Management
    path('users/', views.AllUsersListView.as_view(), name='admin_all_users'),
    path('users/pending/', views.PendingUsersListView.as_view(), name='admin_pending_users'),
    path('users/<uuid:user_id>/', views.UserDetailView.as_view(), name='admin_user_detail'),
    path('users/<uuid:user_id>/approve/', views.ApproveUserPlanView.as_view(), name='admin_approve_user'),
    path('users/<uuid:user_id>/reject/', views.RejectUserPlanView.as_view(), name='admin_reject_user'),
    path('users/<uuid:user_id>/notes/', views.UpdateUserNotesView.as_view(), name='admin_update_notes'),
    path('users/<uuid:user_id>/grant-links/', views.GrantAdditionalLinksView.as_view(), name='admin_grant_links'),
    
    # Legacy endpoints (for backward compatibility)
    path('users/<uuid:user_id>/legacy-approve/', views.ApproveUserView.as_view(), name='admin_legacy_approve'),
    path('users/<uuid:user_id>/legacy-reject/', views.RejectUserView.as_view(), name='admin_legacy_reject'),
    
    # Notifications
    path('notifications/', views.NotificationsListView.as_view(), name='admin_notifications'),
    path('notifications/<uuid:notification_id>/read/', views.MarkNotificationReadView.as_view(), name='admin_mark_read'),
]
