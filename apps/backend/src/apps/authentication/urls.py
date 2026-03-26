"""
URL patterns for the authentication module.

All routes mount under the /api/v1/auth/ prefix defined in config/urls.py.
"""
from django.urls import path

from .views import AdminLoginView, LogoutView, TokenRefreshView, UserLoginView

app_name = 'authentication'

urlpatterns = [
    # User login
    path('login/',          UserLoginView.as_view(),  name='user-login'),

    # Admin login (separate endpoint — requires is_staff=True)
    path('admin/login/',    AdminLoginView.as_view(), name='admin-login'),

    # Logout (blacklist refresh token)
    path('logout/',         LogoutView.as_view(),     name='logout'),

    # Token refresh
    path('token/refresh/',  TokenRefreshView.as_view(), name='token-refresh'),
]
