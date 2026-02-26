"""
Approval workflow views.

This module is part of the refactored admin dashboard views structure.
Generated automatically by refactor_admin_dashboard_views.py
"""

from typing import Dict, Optional
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from apps.invitations.models import Order
from apps.accounts.models import UserActivityLog
from ..models import UserApprovalLog, AdminNotification
from ..services import NotificationService
from .permissions import IsAdminUser

User = get_user_model()

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


