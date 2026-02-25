"""
Invitations, Orders, and Guest Tracking Models
"""
import uuid
import hashlib
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator

from apps.plans.models import Plan, Template


def generate_slug():
    """Generate a unique 10-character slug"""
    import nanoid
    return nanoid.generate(size=10)


class OrderStatus(models.TextChoices):
    """Order status choices"""
    DRAFT = 'DRAFT', 'Draft'
    PENDING_PAYMENT = 'PENDING_PAYMENT', 'Pending Payment'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    REJECTED = 'REJECTED', 'Rejected'
    EXPIRED = 'EXPIRED', 'Expired'
    CANCELLED = 'CANCELLED', 'Cancelled'


class Order(models.Model):
    """
    Order model representing a user's purchase request
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='orders'
    )
    
    # Event Type (Wedding, Birthday, etc.)
    event_type = models.CharField(max_length=50)
    event_type_name = models.CharField(max_length=100)
    
    # Order Status Workflow
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.DRAFT
    )
    
    # Payment Information (Manual for now)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('UPI', 'UPI'),
            ('BANK_TRANSFER', 'Bank Transfer'),
            ('CASH', 'Cash'),
            ('PENDING', 'Pending')
        ],
        default='PENDING'
    )
    payment_status = models.CharField(
        max_length=20,
        default='PENDING',
        choices=[
            ('PENDING', 'Pending'),
            ('RECEIVED', 'Received'),
            ('VERIFIED', 'Verified'),
            ('REFUNDED', 'Refunded')
        ]
    )
    payment_notes = models.TextField(blank=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)
    
    # Admin Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_orders'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    # Granted Link Counts (Admin can modify these)
    granted_regular_links = models.IntegerField(
        help_text="Number of regular links granted (can be modified by admin)"
    )
    granted_test_links = models.IntegerField(
        default=5,
        help_text="Number of test links granted"
    )
    
    # Order metadata
    order_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.phone} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Generate unique order number"""
        prefix = 'ORD'
        timestamp = timezone.now().strftime('%Y%m%d')
        random_str = uuid.uuid4().hex[:6].upper()
        return f"{prefix}-{timestamp}-{random_str}"
    
    def approve(self, admin_user, notes=''):
        """Approve the order"""
        self.status = OrderStatus.APPROVED
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        if notes:
            self.admin_notes = notes
        self.save()
        
        # Update invitation link expiry
        if hasattr(self, 'invitation'):
            self.invitation.activate()
    
    def reject(self, admin_user, reason=''):
        """Reject the order"""
        self.status = OrderStatus.REJECTED
        self.approved_by = admin_user
        self.approved_at = timezone.now()
        self.admin_notes = reason
        self.save()
    
    def grant_additional_links(self, regular=0, test=0, admin_user=None):
        """Grant additional links (for demo/testing or admin bonus)"""
        if regular > 0:
            self.granted_regular_links += regular
        if test > 0:
            self.granted_test_links += test
        self.save()
        
        # Log the action
        if admin_user:
            from apps.accounts.models import UserActivityLog
            UserActivityLog.objects.create(
                user=self.user,
                activity_type='LINKS_GRANTED',
                description=f'Admin granted {regular} regular and {test} test links',
                metadata={
                    'admin_id': str(admin_user.id),
                    'regular_links': regular,
                    'test_links': test
                }
            )
    
    @property
    def used_links_count(self):
        """Count of invitations created (each invitation = 1 link)"""
        if hasattr(self, 'invitation') and self.invitation:
            return 1  # One order = One invitation currently
        return 0
    
    @property
    def remaining_links(self):
        """Remaining invitation links"""
        return max(0, self.granted_regular_links - self.used_links_count)
    
    @property
    def can_create_invitation(self):
        """Check if user can create more invitations"""
        return self.remaining_links > 0 and self.status == 'APPROVED'
        if test > 0:
            self.granted_test_links += test
        
        if admin_user:
            self.admin_notes += f"\n[{timezone.now()}] Granted {regular} regular and {test} test links by {admin_user.username}"
        
        self.save()
    
    @property
    def is_approved(self):
        return self.status == OrderStatus.APPROVED
    
    @property
    def can_create_invitation(self):
        """Check if user can create invitation"""
        return self.status in [OrderStatus.APPROVED, OrderStatus.PENDING_APPROVAL]


class Invitation(models.Model):
    """
    Invitation model - the actual digital invitation
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    order = models.OneToOneField(
        Order,
        on_delete=models.CASCADE,
        related_name='invitation'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    template = models.ForeignKey(
        Template,
        on_delete=models.PROTECT,
        related_name='invitations'
    )
    
    # Unique sharing link
    slug = models.CharField(
        max_length=20,
        unique=True,
        default=generate_slug,
        db_index=True
    )
    
    # Event Details
    event_title = models.CharField(max_length=200)
    event_date = models.DateTimeField()
    event_venue = models.TextField()
    event_address = models.TextField(blank=True)
    event_map_link = models.URLField(blank=True)
    
    # Host Information
    host_name = models.CharField(max_length=200)
    host_phone = models.CharField(max_length=15, blank=True)
    custom_message = models.TextField(blank=True)
    
    # Media
    banner_image = models.ImageField(
        upload_to='invitations/banners/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        help_text="Main banner image for the invitation"
    )
    gallery_images = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of gallery image URLs (max 10)"
    )
    
    # Music (optional)
    background_music = models.FileField(
        upload_to='invitations/music/%Y/%m/',
        validators=[FileExtensionValidator(allowed_extensions=['mp3'])],
        blank=True,
        null=True
    )
    
    # Link validity
    link_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=False)
    is_expired = models.BooleanField(default=False)
    expired_at = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    regular_links_used = models.IntegerField(default=0)
    test_links_used = models.IntegerField(default=0)
    total_views = models.IntegerField(default=0)
    unique_guests = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Invitation'
        verbose_name_plural = 'Invitations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'is_expired']),
        ]
    
    def __str__(self):
        return f"{self.event_title} ({self.slug})"
    
    @property
    def share_url(self):
        """Get the full shareable URL"""
        from django.conf import settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        return f"{frontend_url}/invite/{self.slug}"
    
    @property
    def remaining_regular_links(self):
        """Calculate remaining regular links"""
        return max(0, self.order.granted_regular_links - self.regular_links_used)
    
    @property
    def remaining_test_links(self):
        """Calculate remaining test links"""
        return max(0, self.order.granted_test_links - self.test_links_used)
    
    @property
    def is_link_valid(self):
        """Check if the sharing link is still valid"""
        if not self.is_active or self.is_expired:
            return False
        if self.link_expires_at and timezone.now() > self.link_expires_at:
            return False
        return True
    
    def activate(self):
        """Activate the invitation after approval"""
        from django.conf import settings
        validity_days = settings.INVITATION_SETTINGS.get('LINK_VALIDITY_DAYS', 15)
        
        self.is_active = True
        self.link_expires_at = timezone.now() + timedelta(days=validity_days)
        self.save()
    
    def expire(self):
        """Mark invitation as expired"""
        self.is_expired = True
        self.expired_at = timezone.now()
        self.save()
    
    def increment_view(self):
        """Increment total views"""
        self.total_views += 1
        self.save(update_fields=['total_views'])
    
    def can_accept_guest(self, is_test=False):
        """Check if invitation can accept a new guest"""
        if not self.is_link_valid:
            return False
        
        if is_test:
            return self.remaining_test_links > 0
        return self.remaining_regular_links > 0
    
    def record_guest(self, is_test=False):
        """Record a new guest entry"""
        if is_test:
            self.test_links_used += 1
        else:
            self.regular_links_used += 1
        self.unique_guests += 1
        self.save(update_fields=['regular_links_used', 'test_links_used', 'unique_guests'])


class Guest(models.Model):
    """
    Guest model with device fingerprinting for anti-fraud
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    invitation = models.ForeignKey(
        Invitation,
        on_delete=models.CASCADE,
        related_name='guests'
    )
    
    # Guest Information
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField(blank=True)
    attending = models.BooleanField(null=True, blank=True)  # RSVP status
    
    # Anti-fraud tracking
    device_fingerprint = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Unique device fingerprint hash"
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    user_agent_hash = models.CharField(
        max_length=64,
        help_text="Hash of user agent string"
    )
    session_id = models.CharField(max_length=64, blank=True)
    
    # Device info (for analytics)
    device_type = models.CharField(max_length=50, blank=True)
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    # Link type
    is_test_link = models.BooleanField(default=False)
    
    # Timestamps
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Guest'
        verbose_name_plural = 'Guests'
        ordering = ['-viewed_at']
        unique_together = ['invitation', 'device_fingerprint']
        indexes = [
            models.Index(fields=['invitation', 'device_fingerprint']),
            models.Index(fields=['ip_address', 'viewed_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.invitation.event_title}"
    
    @classmethod
    def generate_fingerprint(cls, user_agent, screen_resolution, 
                            timezone_offset, languages, canvas_hash=''):
        """
        Generate a device fingerprint from browser data
        
        This combines multiple browser characteristics to create
        a unique fingerprint for device identification.
        """
        fingerprint_data = f"{user_agent}|{screen_resolution}|{timezone_offset}|{languages}|{canvas_hash}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    @classmethod
    def check_existing_guest(cls, invitation_id, fingerprint, ip_address):
        """
        Check if a guest with same fingerprint or IP already exists
        Returns the existing guest if found, None otherwise
        """
        # First check by fingerprint (most reliable)
        try:
            return cls.objects.get(
                invitation_id=invitation_id,
                device_fingerprint=fingerprint
            )
        except cls.DoesNotExist:
            pass
        
        # Then check by IP + User Agent (backup method)
        # Only consider recent entries (within last 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        existing = cls.objects.filter(
            invitation_id=invitation_id,
            ip_address=ip_address,
            viewed_at__gte=cutoff_date
        ).first()
        
        return existing
    
    @classmethod
    def register_guest(cls, invitation, name, phone='', message='',
                      fingerprint='', ip_address='', user_agent='',
                      session_id='', device_info=None, is_test=False):
        """
        Register a new guest with anti-fraud checks
        
        Returns tuple: (guest, created, message)
        - guest: Guest object
        - created: True if new guest, False if existing
        - message: Status message
        """
        from user_agents import parse
        
        # Check if invitation can accept guests
        if not invitation.can_accept_guest(is_test):
            return None, False, "Link limit reached or invitation expired"
        
        # Check for existing guest
        existing = cls.check_existing_guest(invitation.id, fingerprint, ip_address)
        if existing:
            # Update name if provided and different
            if name and name != existing.name:
                existing.name = name
                existing.save(update_fields=['name'])
            return existing, False, "Welcome back"
        
        # Parse user agent
        try:
            ua = parse(user_agent)
            device_type = 'mobile' if ua.is_mobile else 'tablet' if ua.is_tablet else 'desktop'
            browser = f"{ua.browser.family} {ua.browser.version_string}"
            os_name = f"{ua.os.family} {ua.os.version_string}"
        except Exception:
            device_type = 'unknown'
            browser = 'unknown'
            os_name = 'unknown'
        
        # Create user agent hash
        ua_hash = hashlib.sha256(user_agent.encode()).hexdigest()
        
        # Create guest
        guest = cls.objects.create(
            invitation=invitation,
            name=name,
            phone=phone,
            message=message,
            device_fingerprint=fingerprint,
            ip_address=ip_address,
            user_agent=user_agent,
            user_agent_hash=ua_hash,
            session_id=session_id,
            device_type=device_type,
            browser=browser,
            os=os_name,
            is_test_link=is_test
        )
        
        # Update invitation counters
        invitation.record_guest(is_test)
        
        return guest, True, "Successfully registered"


class InvitationViewLog(models.Model):
    """
    Log every view of an invitation for analytics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invitation = models.ForeignKey(
        Invitation,
        on_delete=models.CASCADE,
        related_name='view_logs'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Invitation View Log'
        verbose_name_plural = 'Invitation View Logs'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"View of {self.invitation.slug} at {self.viewed_at}"
