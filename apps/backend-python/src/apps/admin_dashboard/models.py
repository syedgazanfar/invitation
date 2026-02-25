"""
Admin Dashboard Models - Notifications and Activity Log
"""
import uuid
from django.db import models
from django.conf import settings


class AdminNotification(models.Model):
    """Notifications for admin users"""
    class NotificationType(models.TextChoices):
        NEW_USER = 'NEW_USER', 'New User Registered'
        PLAN_CHANGE_REQUEST = 'PLAN_CHANGE', 'Plan Change Request'
        PAYMENT_RECEIVED = 'PAYMENT', 'Payment Received'
        ORDER_APPROVED = 'ORDER_APPROVED', 'Order Approved'
        SUPPORT_REQUEST = 'SUPPORT', 'Support Request'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Related objects
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admin_notifications',
        null=True, blank=True
    )
    order = models.ForeignKey(
        'invitations.Order',
        on_delete=models.CASCADE,
        related_name='admin_notifications',
        null=True, blank=True
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Notification'
        verbose_name_plural = 'Admin Notifications'
    
    def __str__(self):
        return f"{self.notification_type}: {self.title}"


class UserApprovalLog(models.Model):
    """Log of user approval actions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='approval_logs'
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='users_approved',
        null=True
    )
    
    action = models.CharField(max_length=20, choices=[
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('PENDING', 'Pending'),
    ])
    
    notes = models.TextField(blank=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Approval Log'
        verbose_name_plural = 'User Approval Logs'
