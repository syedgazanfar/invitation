"""
User Account Models
"""
import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with phone number and additional fields
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Phone number with validation for Indian numbers
    phone_regex = RegexValidator(
        regex=r'^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$',
        message="Phone number must be a valid Indian number"
    )
    phone = models.CharField(
        max_length=15,
        validators=[phone_regex],
        unique=True,
        help_text="Indian mobile number with or without +91"
    )
    
    # Profile fields
    full_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    
    # Verification status
    is_phone_verified = models.BooleanField(default=False)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Account status
    is_blocked = models.BooleanField(
        default=False,
        help_text="If true, user cannot access the platform"
    )
    blocked_at = models.DateTimeField(null=True, blank=True)
    block_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Metadata
    signup_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Current Plan (locked - can only be changed by admin)
    current_plan = models.ForeignKey(
        'plans.Plan',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribed_users',
        help_text="User's current locked plan. Can only be changed by admin."
    )
    plan_change_requested = models.BooleanField(
        default=False,
        help_text='User has requested a plan change'
    )
    plan_change_requested_at = models.DateTimeField(null=True, blank=True)
    
    # Admin approval workflow
    is_approved = models.BooleanField(
        default=False,
        help_text='User account approved by admin after payment verification'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_users',
        help_text='Admin who approved this user'
    )
    payment_verified = models.BooleanField(
        default=False,
        help_text='Payment has been verified by admin'
    )
    notes = models.TextField(
        blank=True,
        help_text='Admin notes about this user'
    )
    
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username', 'email']
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone} - {self.full_name or self.username}"
    
    @property
    def active_orders_count(self):
        """Count of active orders for this user"""
        return self.orders.filter(
            status__in=['PENDING_PAYMENT', 'PENDING_APPROVAL', 'APPROVED']
        ).count()
    
    @property
    def total_invitations(self):
        """Count of total invitations created"""
        return self.invitations.count()
    
    def request_plan_change(self):
        """Request a plan change - requires admin approval"""
        self.plan_change_requested = True
        self.plan_change_requested_at = timezone.now()
        self.save(update_fields=['plan_change_requested', 'plan_change_requested_at'])
    
    def can_access_plan(self, plan_code):
        """Check if user can access templates for a given plan"""
        if not self.current_plan:
            return plan_code == 'BASIC'  # Default to BASIC if no plan
        
        # User can access their current plan and lower tier plans
        plan_hierarchy = {'BASIC': 1, 'PREMIUM': 2, 'LUXURY': 3}
        user_tier = plan_hierarchy.get(self.current_plan.code, 1)
        target_tier = plan_hierarchy.get(plan_code, 1)
        
        return target_tier <= user_tier


class PhoneVerification(models.Model):
    """
    Store OTP for phone verification
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()
    
    class Meta:
        verbose_name = 'Phone Verification'
        verbose_name_plural = 'Phone Verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.phone}"


class UserActivityLog(models.Model):
    """
    Track user activities for security and analytics
    """
    class ActivityType(models.TextChoices):
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Change'
        PROFILE_UPDATE = 'PROFILE_UPDATE', 'Profile Update'
        ORDER_CREATED = 'ORDER_CREATED', 'Order Created'
        INVITATION_CREATED = 'INVITATION_CREATED', 'Invitation Created'
        INVITATION_SHARED = 'INVITATION_SHARED', 'Invitation Shared'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'User Activity Log'
        verbose_name_plural = 'User Activity Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.phone} - {self.activity_type}"
