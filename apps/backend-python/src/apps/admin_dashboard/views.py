"""
Admin Dashboard Views

This module provides API endpoints for the admin dashboard, including:
- Dashboard statistics
- User management (list, detail, approve, reject)
- Order management
- Real-time notifications
- Pending approvals tracking
"""
from typing import Any, Dict, Optional, List
from django.db.models import Q, Count, Sum
from django.utils import timezone
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from apps.invitations.models import Order, Invitation
from apps.accounts.models import UserActivityLog
from .models import AdminNotification, UserApprovalLog
from .services import NotificationService

User = get_user_model()


class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to only allow admin users.
    
    Checks if the user is authenticated and has is_staff flag set.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )


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


class PendingApprovalsView(APIView):
    """
    Get list of pending approvals for admin dashboard.
    
    Returns a count and list of users awaiting approval.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request) -> Response:
        """Handle GET request for pending approvals."""
        # Get pending users with related data
        pending_users = User.objects.filter(
            is_staff=False,
            is_approved=False
        ).select_related('current_plan').order_by('-created_at')
        
        # Build response data
        users_data = []
        for user in pending_users:
            # Get latest order
            latest_order = user.orders.select_related('plan').first()
            
            user_data = {
                'id': str(user.id),
                'username': user.username,
                'full_name': user.full_name,
                'phone': user.phone,
                'email': user.email,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'signup_ip': user.signup_ip,
                'current_plan': {
                    'code': user.current_plan.code,
                    'name': user.current_plan.name,
                    'price_inr': float(user.current_plan.price_inr),
                    'regular_links': user.current_plan.regular_links,
                    'test_links': user.current_plan.test_links,
                } if user.current_plan else None,
                'latest_order': {
                    'id': str(latest_order.id),
                    'order_number': latest_order.order_number,
                    'status': latest_order.status,
                    'payment_amount': float(latest_order.payment_amount),
                    'payment_method': latest_order.payment_method,
                } if latest_order else None,
            }
            users_data.append(user_data)
        
        return Response({
            'success': True,
            'count': len(users_data),
            'data': users_data
        })


class ApproveUserPlanView(APIView):
    """
    Approve a user's plan - admin only.
    
    POST /api/v1/admin-dashboard/users/<user_id>/approve/
    
    Body:
        - notes: Optional approval notes
        - payment_method: Payment method used
        - payment_amount: Payment amount received
        - granted_regular_links: Override regular links (optional)
        - granted_test_links: Override test links (optional)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        """Handle POST request to approve a user."""
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_approved:
            return Response({
                'success': False,
                'message': 'User is already approved'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get optional parameters
        notes = request.data.get('notes', '')
        payment_method = request.data.get('payment_method', '')
        payment_amount = request.data.get('payment_amount')
        
        # Get or create order
        latest_order = user.orders.order_by('-created_at').first()
        
        if latest_order:
            # Admin can modify granted links
            regular_links = request.data.get('granted_regular_links')
            test_links = request.data.get('granted_test_links')
            
            if regular_links is not None:
                latest_order.granted_regular_links = int(regular_links)
            if test_links is not None:
                latest_order.granted_test_links = int(test_links)
            
            # Update order status
            latest_order.status = 'APPROVED'
            latest_order.approved_by = request.user
            latest_order.approved_at = timezone.now()
            if payment_method:
                latest_order.payment_method = payment_method
            latest_order.save()
        
        # Approve user
        user.is_approved = True
        user.approved_at = timezone.now()
        user.approved_by = request.user
        user.payment_verified = True
        if notes:
            user.notes = notes
        user.save()
        
        # Create approval log
        UserApprovalLog.objects.create(
            user=user,
            approved_by=request.user,
            action='APPROVED',
            notes=notes,
            payment_method=payment_method,
            payment_amount=payment_amount
        )
        
        # Send notification to user
        try:
            NotificationService.notify_user_approved(user, request.user)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send approval notification: {e}")
        
        # Mark related notification as read
        AdminNotification.objects.filter(
            user=user,
            notification_type=AdminNotification.NotificationType.NEW_USER,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            'success': True,
            'message': f'User {user.username} has been approved successfully',
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'approved_at': user.approved_at.isoformat() if user.approved_at else None,
                'approved_by': request.user.username,
                'granted_links': {
                    'regular': latest_order.granted_regular_links if latest_order else 0,
                    'test': latest_order.granted_test_links if latest_order else 0
                } if latest_order else None
            }
        })


class RejectUserPlanView(APIView):
    """
    Reject a user's plan - admin only.
    
    POST /api/v1/admin-dashboard/users/<user_id>/reject/
    
    Body:
        - reason: Required rejection reason
        - block_user: Whether to block the user (default: True)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        """Handle POST request to reject a user."""
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        reason = request.data.get('reason', '')
        block_user = request.data.get('block_user', True)
        
        if not reason:
            return Response({
                'success': False,
                'message': 'Rejection reason is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update latest order if exists
        latest_order = user.orders.order_by('-created_at').first()
        if latest_order:
            latest_order.status = 'REJECTED'
            latest_order.approved_by = request.user
            latest_order.approved_at = timezone.now()
            latest_order.admin_notes = reason
            latest_order.save()
        
        # Create rejection log
        UserApprovalLog.objects.create(
            user=user,
            approved_by=request.user,
            action='REJECTED',
            notes=reason
        )
        
        # Optionally block user
        if block_user:
            user.is_blocked = True
            user.block_reason = reason
            user.save()
        
        # Send rejection email to user
        try:
            self._send_rejection_email(user, reason)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send rejection email: {e}")
        
        return Response({
            'success': True,
            'message': f'User {user.username} has been rejected',
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'reason': reason,
                'blocked': block_user
            }
        })
    
    def _send_rejection_email(self, user: User, reason: str) -> None:
        """Send rejection email to user."""
        from django.core.mail import send_mail
        from django.conf import settings
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        
        subject = 'Update on Your InviteMe Account'
        
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #dc3545;">Account Update</h2>
                
                <p>Hello {user.full_name or user.username},</p>
                
                <p>We regret to inform you that your account request has not been approved at this time.</p>
                
                <div style="background: #f8d7da; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Reason:</strong></p>
                    <p>{reason}</p>
                </div>
                
                <p>If you believe this is an error or have any questions, please contact our support team at {settings.ADMIN_SETTINGS['SUPPORT_EMAIL']}</p>
                
                <p>Best regards,<br>Team InviteMe</p>
            </div>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email] if user.email else [],
            html_message=html_message,
            fail_silently=True
        )


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


class ApproveUserView(generics.GenericAPIView):
    """Approve a user after payment verification (legacy endpoint)."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        # Delegate to the new view
        view = ApproveUserPlanView()
        view.request = request
        return view.post(request, user_id)


class RejectUserView(generics.GenericAPIView):
    """Reject a user registration (legacy endpoint)."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        # Delegate to the new view
        view = RejectUserPlanView()
        view.request = request
        return view.post(request, user_id)


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


class GrantAdditionalLinksView(generics.GenericAPIView):
    """Grant additional invitation links to a user."""
    permission_classes = [IsAdminUser]
    
    def post(self, request, user_id: str) -> Response:
        try:
            user = User.objects.get(id=user_id, is_staff=False)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        regular_links = int(request.data.get('regular_links', 0))
        test_links = int(request.data.get('test_links', 0))
        reason = request.data.get('reason', '')
        
        if regular_links <= 0 and test_links <= 0:
            return Response({
                'success': False,
                'message': 'Please specify number of links to grant'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create order
        order = user.orders.filter(
            status__in=['APPROVED', 'PENDING_APPROVAL']
        ).order_by('-created_at').first()
        
        if not order:
            return Response({
                'success': False,
                'message': 'User has no order. Please ask user to select a plan first.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Grant links
        order.grant_additional_links(
            regular=regular_links,
            test=test_links,
            admin_user=request.user
        )
        
        return Response({
            'success': True,
            'message': f'Granted {regular_links} regular and {test_links} test links to {user.username}',
            'data': {
                'user_id': str(user.id),
                'username': user.username,
                'total_regular_links': order.granted_regular_links,
                'total_test_links': order.granted_test_links,
                'remaining_links': order.remaining_links,
                'reason': reason
            }
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
