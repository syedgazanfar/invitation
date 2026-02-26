"""
ASGI config for invitation platform project.

This module exposes the ASGI callable as a module-level variable named ``application``.
It includes both HTTP and WebSocket support using Django Channels.
"""
import os
from django.core.asgi import get_asgi_application

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import channels components after Django setup
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Import WebSocket URL patterns
from apps.admin_dashboard import routing as admin_routing


# ASGI application with WebSocket support
application = ProtocolTypeRouter({
    # HTTP requests
    'http': django_asgi_app,
    
    # WebSocket requests
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                admin_routing.websocket_urlpatterns
            )
        )
    ),
})
