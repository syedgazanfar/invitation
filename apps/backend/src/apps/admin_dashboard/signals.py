"""
Django Signals for Admin Dashboard Real-time Updates

This module contains signals that trigger WebSocket broadcasts
when important events occur in the system.
"""
from typing import Optional
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.accounts.models import User
from apps.invitations.models import Order
from apps.admin_dashboard.models import AdminNotification, UserApprovalLog
from apps.admin_dashboard.consumers import AdminDashboardConsumer


# Get channel layer for broadcasting
channel_layer = get_channel_layer()


@receiver(post_save, sender=User)
def user_approval_changed(sender, instance: User, created: bool, **kwargs):
    """
    Signal handler for User model changes.
    
    Triggers real-time updates when:
    - A new user registers (requires approval)
    - A user's approval status changes
    - A user's plan changes
    
    Args:
        sender: User model class
        instance: The user instance that was saved
        created: Whether this is a new user
    """
    if not channel_layer:
        return
    
    # New user registered - broadcast to admins
    if created and not instance.is_staff:
        user_data = {
            'id': str(instance.id),
            'username': instance.username,
            'full_name': instance.full_name,
            'phone': instance.phone,
            'email': instance.email,
            'created_at': instance.created_at.isoformat() if instance.created_at else None
        }
        
        try:
            async_to_sync(AdminDashboardConsumer.broadcast_new_user)(user_data)
            async_to_sync(AdminDashboardConsumer.broadcast_pending_count_update)(
                count=get_pending_approvals_count(),
                change=+1
            )
        except Exception as e:
            # Log error but don't break the request
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to broadcast new user: {e}")
    
    # Check if approval status changed (not new user)
    elif not created and not instance.is_staff:
        # Get the previous state from the database
        try:
            previous = User.objects.get(pk=instance.pk)
            
            # Approval status changed
            if previous.is_approved != instance.is_approved:
                action = 'approved' if instance.is_approved else 'rejected'
                
                user_data = {
                    'id': str(instance.id),
                    'username': instance.username,
                    'full_name': instance.full_name,
                    'phone': instance.phone,
                    'email': instance.email,
                    'is_approved': instance.is_approved,
                    'payment_verified': instance.payment_verified,
                    'approved_at': instance.approved_at.isoformat() if instance.approved_at else None,
                    'current_plan': {
                        'code': instance.current_plan.code,
                        'name': instance.current_plan.name
                    } if instance.current_plan else None
                }
                
                performed_by = None
                if instance.approved_by:
                    performed_by = {
                        'id': str(instance.approved_by.id),
                        'username': instance.approved_by.username
                    }
                
                try:
                    async_to_sync(AdminDashboardConsumer.broadcast_approval_update)(
                        user_data=user_data,
                        action=action,
                        performed_by=performed_by,
                        notes=instance.notes
                    )
                    
                    # Update pending count
                    if instance.is_approved:
                        async_to_sync(AdminDashboardConsumer.broadcast_pending_count_update)(
                            count=get_pending_approvals_count(),
                            change=-1
                        )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to broadcast approval update: {e}")
        
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=Order)
def order_status_changed(sender, instance: Order, created: bool, **kwargs):
    """
    Signal handler for Order model changes.
    
    Triggers real-time updates when:
    - A new order is created
    - An order status changes
    
    Args:
        sender: Order model class
        instance: The order instance that was saved
        created: Whether this is a new order
    """
    if not channel_layer:
        return
    
    # New order created
    if created:
        try:
            async_to_sync(AdminDashboardConsumer.broadcast_order_update)(
                order_id=str(instance.id),
                status=instance.status,
                previous_status=None
            )
            
            # Update pending count if order needs approval
            if instance.status in ['PENDING_PAYMENT', 'PENDING_APPROVAL']:
                async_to_sync(AdminDashboardConsumer.broadcast_pending_count_update)(
                    count=get_pending_approvals_count(),
                    change=0  # Just refresh, don't increment
                )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to broadcast order update: {e}")
    
    else:
        # Check if status changed
        try:
            previous = Order.objects.get(pk=instance.pk)
            if previous.status != instance.status:
                try:
                    async_to_sync(AdminDashboardConsumer.broadcast_order_update)(
                        order_id=str(instance.id),
                        status=instance.status,
                        previous_status=previous.status
                    )
                    
                    # Update pending count if moving to/from pending
                    if previous.status in ['PENDING_PAYMENT', 'PENDING_APPROVAL'] or \
                       instance.status in ['PENDING_PAYMENT', 'PENDING_APPROVAL']:
                        async_to_sync(AdminDashboardConsumer.broadcast_pending_count_update)(
                            count=get_pending_approvals_count(),
                            change=0
                        )
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to broadcast order status update: {e}")
        except Order.DoesNotExist:
            pass


@receiver(post_save, sender=AdminNotification)
def admin_notification_created(sender, instance: AdminNotification, created: bool, **kwargs):
    """
    Signal handler for AdminNotification model.
    
    Triggers real-time updates when a new admin notification is created.
    
    Args:
        sender: AdminNotification model class
        instance: The notification instance that was saved
        created: Whether this is a new notification
    """
    if not channel_layer or not created:
        return
    
    # Only broadcast certain notification types
    broadcast_types = [
        AdminNotification.NotificationType.NEW_USER,
        AdminNotification.NotificationType.PLAN_CHANGE_REQUEST,
        AdminNotification.NotificationType.PAYMENT_RECEIVED,
    ]
    
    if instance.notification_type in broadcast_types:
        try:
            notification_data = {
                'id': str(instance.id),
                'type': instance.notification_type,
                'title': instance.title,
                'message': instance.message,
                'created_at': instance.created_at.isoformat() if instance.created_at else None,
                'metadata': instance.metadata
            }
            
            async_to_sync(channel_layer.group_send)(
                AdminDashboardConsumer.ADMIN_GROUP,
                {
                    'type': 'new_notification',
                    'notification': notification_data
                }
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to broadcast notification: {e}")


@receiver(post_save, sender=UserApprovalLog)
def approval_log_created(sender, instance: UserApprovalLog, created: bool, **kwargs):
    """
    Signal handler for UserApprovalLog model.
    
    Creates an audit entry and optionally broadcasts to admins.
    
    Args:
        sender: UserApprovalLog model class
        instance: The approval log instance that was saved
        created: Whether this is a new log entry
    """
    if not created:
        return
    
    # Log the approval action
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"User approval action: {instance.action} - "
        f"User: {instance.user.username} - "
        f"By: {instance.approved_by.username if instance.approved_by else 'System'}"
    )


def get_pending_approvals_count() -> int:
    """
    Get the current count of pending approvals.
    
    Returns:
        Number of users awaiting approval
    """
    User = get_user_model()
    return User.objects.filter(is_staff=False, is_approved=False).count()


def get_pending_orders_count() -> int:
    """
    Get the current count of pending orders.
    
    Returns:
        Number of orders awaiting payment or approval
    """
    return Order.objects.filter(
        status__in=['PENDING_PAYMENT', 'PENDING_APPROVAL']
    ).count()
