"""
URL configuration for accounts app.

Login, logout, and token refresh have been moved to apps.authentication.
This module handles registration and authenticated account management only.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Registration (public)
    path('register/', views.RegisterView.as_view(), name='register'),

    # Profile management (authenticated)
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change_password'),

    # Phone verification (authenticated)
    path('send-otp/', views.SendOTPView.as_view(), name='send_otp'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify_otp'),

    # Plan management (authenticated)
    path('my-plan/', views.MyPlanView.as_view(), name='my_plan'),
    path('request-plan-change/', views.RequestPlanChangeView.as_view(), name='request_plan_change'),
]
