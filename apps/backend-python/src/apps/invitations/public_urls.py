"""
URL configuration for public invitation routes (no authentication)
"""
from django.urls import path
from . import public_views

urlpatterns = [
    # Public invitation viewing
    path('<slug:slug>/', public_views.get_public_invitation, name='public_invitation'),
    path('<slug:slug>/check/', public_views.check_guest_status, name='check_guest'),
    path('<slug:slug>/register/', public_views.register_guest, name='register_guest'),
    path('<slug:slug>/rsvp/', public_views.update_rsvp, name='update_rsvp'),
]
