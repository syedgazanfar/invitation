"""
Plans and Templates Models
"""
import uuid
from django.db import models


class Plan(models.Model):
    """
    Pricing plans for invitations
    """
    class PlanCode(models.TextChoices):
        BASIC = 'BASIC', 'Basic'
        PREMIUM = 'PREMIUM', 'Premium'
        LUXURY = 'LUXURY', 'Luxury'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(
        max_length=20,
        choices=PlanCode.choices,
        unique=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Link limits
    regular_links = models.IntegerField(
        help_text="Number of regular invitation links"
    )
    test_links = models.IntegerField(
        default=5,
        help_text="Number of test links for demo"
    )
    
    # Pricing (India only for now)
    price_inr = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in Indian Rupees"
    )
    
    # Features
    features = models.JSONField(
        default=list,
        help_text="List of features included in this plan"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'
        ordering = ['sort_order', 'price_inr']
    
    def __str__(self):
        return f"{self.name} - INR {self.price_inr}"
    
    @property
    def display_price(self):
        return f"Rs. {int(self.price_inr)}"


class InvitationCategory(models.Model):
    """
    Categories of invitations (Wedding, Birthday, etc.)
    """
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text="Material-UI icon name"
    )
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Invitation Category'
        verbose_name_plural = 'Invitation Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Template(models.Model):
    """
    Invitation templates with animations
    """
    class AnimationType(models.TextChoices):
        ELEGANT = 'elegant', 'Elegant'
        FUN = 'fun', 'Fun & Playful'
        TRADITIONAL = 'traditional', 'Traditional'
        MODERN = 'modern', 'Modern'
        MINIMAL = 'minimal', 'Minimal'
        BOLLYWOOD = 'bollywood', 'Bollywood Style'
        FLORAL = 'floral', 'Floral'
        ROYAL = 'royal', 'Royal'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    plan = models.ForeignKey(
        Plan,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    category = models.ForeignKey(
        InvitationCategory,
        on_delete=models.CASCADE,
        related_name='templates'
    )
    
    # Basic info
    name = models.CharField(max_length=100)
    description = models.TextField()
    thumbnail = models.ImageField(
        upload_to='templates/thumbnails/',
        help_text="Template preview image"
    )
    
    # Animation configuration
    animation_type = models.CharField(
        max_length=20,
        choices=AnimationType.choices,
        default=AnimationType.ELEGANT
    )
    animation_config = models.JSONField(
        default=dict,
        help_text="JSON configuration for animations"
    )
    
    # Theme colors
    theme_colors = models.JSONField(
        default=dict,
        help_text="JSON with primary, secondary, accent, background colors"
    )
    
    # Template preview/demo URL
    preview_url = models.URLField(blank=True)
    
    # Features this template supports
    supports_gallery = models.BooleanField(default=True)
    supports_music = models.BooleanField(default=False)
    supports_video = models.BooleanField(default=False)
    supports_rsvp = models.BooleanField(default=False)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_premium = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    
    # Usage stats
    use_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Template'
        verbose_name_plural = 'Templates'
        ordering = ['sort_order', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.plan.code})"
    
    def increment_use_count(self):
        self.use_count += 1
        self.save(update_fields=['use_count'])
