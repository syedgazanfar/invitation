"""
Main URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def api_root(request):
    """API root view showing all available endpoints."""
    return JsonResponse({
        "name": "Wedding Invitations Platform API",
        "version": "v1",
        "status": "operational",
        "endpoints": {
            "auth": "/api/v1/auth/",
            "plans": "/api/v1/plans/",
            "invitations": "/api/v1/invitations/",
            "admin_dashboard": "/api/v1/admin-dashboard/",
            "ai": "/api/v1/ai/",
            "invite": "/api/invite/",
        },
        "documentation": {
            "admin": "/admin/",
        }
    })


urlpatterns = [
    # API Root
    path('api/v1/', api_root),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/plans/', include('apps.plans.urls')),
    path('api/v1/invitations/', include('apps.invitations.urls')),
    path('api/v1/admin-dashboard/', include('apps.admin_dashboard.urls')),
    path('api/v1/ai/', include('apps.ai.urls')),
    
    # Public invitation endpoint (no version prefix)
    path('api/invite/', include('apps.invitations.public_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
