"""
Notification management views.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status

from ..models import AdminNotification
from .permissions import IsAdminUser

class NotificationsListView(generics.ListAPIView):
    """List admin notifications."""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return AdminNotification.objects.all().order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread_only = request.query_params.get('unread') == 'true'
        
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        notifications = []
        for notif in queryset[:50]:  # Limit to 50 most recent
            notifications.append({
                'id': str(notif.id),
                'type': notif.notification_type,
                'title': notif.title,
                'message': notif.message,
                'is_read': notif.is_read,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
                'user': {
                    'id': str(notif.user.id),
                    'username': notif.user.username
                } if notif.user else None,
                'metadata': notif.metadata
            })
        
        return Response({
            'success': True,
            'unread_count': AdminNotification.objects.filter(is_read=False).count(),
            'data': notifications
        })



class MarkNotificationReadView(generics.GenericAPIView):
    """Mark a notification as read."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, notification_id: str) -> Response:
        try:
            notification = AdminNotification.objects.get(id=notification_id)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            
            return Response({
                'success': True,
                'message': 'Notification marked as read'
            })
        except AdminNotification.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Notification not found'
            }, status=status.HTTP_404_NOT_FOUND)


