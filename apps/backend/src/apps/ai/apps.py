from django.apps import AppConfig


class AIConfig(AppConfig):
    """Configuration for the AI app."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai'
    label = 'ai'
    verbose_name = 'AI Features'

    def ready(self):
        """Import signal handlers when the app is ready."""
        import apps.ai.signals  # noqa
