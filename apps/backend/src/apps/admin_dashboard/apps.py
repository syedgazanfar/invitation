"""
Admin Dashboard App Configuration
"""
from django.apps import AppConfig


class AdminDashboardConfig(AppConfig):
    """Configuration for the admin dashboard app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.admin_dashboard'
    verbose_name = 'Admin Dashboard'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        
        This ensures that the signal handlers are registered
        when Django starts up.
        """
        import apps.admin_dashboard.signals  # noqa: F401
