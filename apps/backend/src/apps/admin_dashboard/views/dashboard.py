"""
Dashboard statistics and overview.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

from typing import Any, Dict
from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from apps.invitations.models import Order, Invitation
from ..models import AdminNotification
from .permissions import IsAdminUser

User = get_user_model()

class DashboardStatsView(APIView):
    """
    Get comprehensive dashboard statistics.
    
    Returns:
        - User counts (total, new today, pending approval)
        - Order counts (total, pending, approved)
        - Invitation and link statistics
        - Unread notification count
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request) -> Response:
        """Handle GET request for dashboard statistics."""
        today = timezone.now().date()
        
        # Calculate link statistics
        approved_orders = Order.objects.filter(status='APPROVED')
        total_granted_links = sum(
            order.granted_regular_links for order in approved_orders
        )
        total_used_links = sum(
            order.used_links_count for order in approved_orders
        )
        
        stats = {
            'users': {
                'total': User.objects.filter(is_staff=False).count(),
                'new_today': User.objects.filter(
                    is_staff=False,
                    created_at__date=today
                ).count(),
                'pending_approval': User.objects.filter(
                    is_staff=False,
                    is_approved=False
                ).count(),
            },
            'orders': {
                'total': Order.objects.count(),
                'pending_payment': Order.objects.filter(
                    status='PENDING_PAYMENT'
                ).count(),
                'pending_approval': Order.objects.filter(
                    status='PENDING_APPROVAL'
                ).count(),
                'approved': Order.objects.filter(status='APPROVED').count(),
                'rejected': Order.objects.filter(status='REJECTED').count(),
            },
            'invitations': {
                'total': Invitation.objects.count(),
                'active': Invitation.objects.filter(
                    is_active=True, is_expired=False
                ).count(),
                'expired': Invitation.objects.filter(is_expired=True).count(),
            },
            'links': {
                'total_granted': total_granted_links,
                'total_used': total_used_links,
                'total_remaining': total_granted_links - total_used_links,
            },
            'notifications': {
                'unread': AdminNotification.objects.filter(is_read=False).count(),
                'total': AdminNotification.objects.count(),
            }
        }
        
        return Response({
            'success': True,
            'data': stats
        })



class RecentApprovalsView(APIView):
    """
    Get recent approval actions for the activity feed.
    
    Returns the most recent approval/rejection actions.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request) -> Response:
        """Handle GET request for recent approvals."""
        limit = int(request.query_params.get('limit', 10))
        
        logs = UserApprovalLog.objects.select_related(
            'user', 'approved_by'
        ).order_by('-created_at')[:limit]
        
        data = []
        for log in logs:
            data.append({
                'id': str(log.id),
                'action': log.action,
                'user': {
                    'id': str(log.user.id),
                    'username': log.user.username,
                    'full_name': log.user.full_name,
                    'phone': log.user.phone
                },
                'performed_by': {
                    'id': str(log.approved_by.id),
                    'username': log.approved_by.username
                } if log.approved_by else None,
                'notes': log.notes,
                'payment_amount': float(log.payment_amount) if log.payment_amount else None,
                'payment_method': log.payment_method,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return Response({
            'success': True,
            'count': len(data),
            'data': data
        })


