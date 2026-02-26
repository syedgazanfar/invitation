"""
User management views.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

from typing import Any, Dict
from django.db.models import Q, Count, Sum
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model

from apps.accounts.models import UserActivityLog
from apps.invitations.models import Order
from .permissions import IsAdminUser

User = get_user_model()

class PendingUsersListView(generics.ListAPIView):
    """List users pending approval (alias for compatibility)."""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return User.objects.filter(
            is_staff=False,
            is_approved=False
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        users = []
        
        for user in queryset:
            latest_order = user.orders.order_by('-created_at').first()
            
            user_data = {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'phone': user.phone,
                'email': user.email,
                'created_at': user.created_at,
                'signup_ip': user.signup_ip,
                'has_order': user.orders.exists(),
                'order_count': user.orders.count(),
                'selected_plan': {
                    'code': latest_order.plan.code,
                    'name': latest_order.plan.name,
                    'price': float(latest_order.plan.price_inr),
                    'regular_links': latest_order.plan.regular_links,
                    'test_links': latest_order.plan.test_links,
                } if latest_order else None,
                'order_status': latest_order.status if latest_order else None,
                'order_id': str(latest_order.id) if latest_order else None,
            }
            users.append(user_data)
        
        return Response({
            'success': True,
            'data': users
        })



class AllUsersListView(generics.ListAPIView):
    """List all users with filters and search."""
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.filter(is_staff=False)
        
        # Filter by approval status
        status_filter = self.request.query_params.get('status')
        if status_filter == 'pending':
            queryset = queryset.filter(is_approved=False)
        elif status_filter == 'approved':
            queryset = queryset.filter(is_approved=True)
        elif status_filter == 'blocked':
            queryset = queryset.filter(is_blocked=True)
        
        # Filter by plan
        plan = self.request.query_params.get('plan')
        if plan:
            queryset = queryset.filter(current_plan__code=plan.upper())
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(full_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        users = []
        
        for user in queryset:
            latest_order = user.orders.first()
            users.append({
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'phone': user.phone,
                'email': user.email,
                'is_approved': user.is_approved,
                'payment_verified': user.payment_verified,
                'is_blocked': user.is_blocked,
                'current_plan': {
                    'code': user.current_plan.code,
                    'name': user.current_plan.name
                } if user.current_plan else None,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'approved_at': user.approved_at.isoformat() if user.approved_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'signup_ip': user.signup_ip,
                'notes': user.notes,
                'latest_order': {
                    'id': str(latest_order.id),
                    'status': latest_order.status,
                    'amount': float(latest_order.payment_amount)
                } if latest_order else None
            })
        
        return Response({
            'success': True,
            'count': len(users),
            'data': users
        })



class UserDetailView(generics.GenericAPIView):
    """Get detailed user information."""
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id: str) -> Response:
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get orders
        orders = []
        for order in user.orders.all():
            orders.append({
                'id': str(order.id),
                'order_number': order.order_number,
                'plan': {
                    'code': order.plan.code,
                    'name': order.plan.name,
                    'regular_links': order.plan.regular_links,
                    'test_links': order.plan.test_links,
                },
                'status': order.status,
                'payment_amount': float(order.payment_amount),
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'granted_regular_links': order.granted_regular_links,
                'granted_test_links': order.granted_test_links,
                'used_links': order.used_links_count,
                'remaining_links': order.remaining_links,
                'created_at': order.created_at.isoformat() if order.created_at else None
            })
        
        # Get latest order
        latest_order = user.orders.order_by('-created_at').first()
        
        # Get invitations
        invitations = []
        for inv in user.invitations.all():
            invitations.append({
                'id': str(inv.id),
                'slug': inv.slug,
                'title': inv.event_title,
                'event_type': inv.event_type,
                'is_active': inv.is_active,
                'is_expired': inv.is_expired,
                'total_views': inv.total_views,
                'unique_guests': inv.unique_guests,
                'created_at': inv.created_at.isoformat() if inv.created_at else None
            })
        
        # Get activity logs
        activity_logs = []
        for log in UserActivityLog.objects.filter(user=user).order_by('-created_at')[:10]:
            activity_logs.append({
                'activity_type': log.activity_type,
                'description': log.description,
                'ip_address': log.ip_address,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        # Get approval logs
        approval_logs = []
        for log in UserApprovalLog.objects.filter(user=user).order_by('-created_at'):
            approval_logs.append({
                'action': log.action,
                'notes': log.notes,
                'performed_by': log.approved_by.username if log.approved_by else 'System',
                'created_at': log.created_at.isoformat() if log.created_at else None,
                'payment_method': log.payment_method,
                'payment_amount': float(log.payment_amount) if log.payment_amount else None
            })
        
        return Response({
            'success': True,
            'data': {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'phone': user.phone,
                'email': user.email,
                'is_approved': user.is_approved,
                'payment_verified': user.payment_verified,
                'is_blocked': user.is_blocked,
                'block_reason': user.block_reason,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'approved_at': user.approved_at.isoformat() if user.approved_at else None,
                'approved_by': user.approved_by.username if user.approved_by else None,
                'current_plan': {
                    'code': user.current_plan.code,
                    'name': user.current_plan.name,
                    'price_inr': float(user.current_plan.price_inr),
                    'features': user.current_plan.features
                } if user.current_plan else None,
                'plan_change_requested': user.plan_change_requested,
                'notes': user.notes,
                'link_summary': {
                    'granted_regular': latest_order.granted_regular_links if latest_order else 0,
                    'granted_test': latest_order.granted_test_links if latest_order else 0,
                    'used': latest_order.used_links_count if latest_order else 0,
                    'remaining': latest_order.remaining_links if latest_order else 0,
                } if latest_order else None,
                'orders': orders,
                'invitations': invitations,
                'activity_logs': activity_logs,
                'approval_logs': approval_logs
            }
        })



class UpdateUserNotesView(generics.GenericAPIView):
    """Update admin notes for a user."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        notes = request.data.get('notes', '')
        user.notes = notes
        user.save()
        
        return Response({
            'success': True,
            'message': 'Notes updated successfully'
        })


