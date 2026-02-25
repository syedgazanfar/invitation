"""
WebSocket Routing Configuration for Admin Dashboard

This module defines WebSocket URL patterns for real-time admin features.
"""
from django.urls import re_path
from . import consumers


websocket_urlpatterns = [
    # Admin dashboard real-time updates
    re_path(
        r'ws/admin/dashboard/$',
        consumers.AdminDashboardConsumer.as_asgi()
    ),
]
