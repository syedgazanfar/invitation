"""
Admin permission classes.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    
    Checks if the user is authenticated and has is_staff flag set.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


