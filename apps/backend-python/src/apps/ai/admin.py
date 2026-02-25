"""
Admin configuration for the AI app.
"""

from django.contrib import admin
from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog


@admin.register(PhotoAnalysis)
class PhotoAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for PhotoAnalysis model."""
    
    list_display = [
        'id',
        'user',
        'event_link',
        'image_url_short',
        'primary_colors_preview',
        'created_at',
    ]
    list_filter = [
        'created_at',
        'updated_at',
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'event__title',
        'image_url',
    ]
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'event', 'image_url')
        }),
        ('Analysis Results', {
            'fields': ('primary_colors', 'mood', 'style_recommendations'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def event_link(self, obj):
        """Display event as a link."""
        if obj.event:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:invitations_event_change', args=[obj.event.id])
            return format_html('<a href="{}">{}</a>', url, obj.event.title)
        return '-'
    event_link.short_description = 'Event'
    
    def image_url_short(self, obj):
        """Display shortened image URL."""
        if len(obj.image_url) > 50:
            return obj.image_url[:50] + '...'
        return obj.image_url
    image_url_short.short_description = 'Image URL'
    
    def primary_colors_preview(self, obj):
        """Display primary colors preview."""
        if obj.primary_colors and 'colors' in obj.primary_colors:
            colors = obj.primary_colors['colors']
            if colors:
                from django.utils.html import format_html
                color_boxes = ''.join([
                    f'<span style="display:inline-block;width:20px;height:20px;'
                    f'background:{c.get("hex", "#ccc")};margin-right:5px;'
                    f'border:1px solid #ddd;" title="{c.get("hex", "")}"></span>'
                    for c in colors[:5]
                ])
                return format_html(color_boxes)
        return '-'
    primary_colors_preview.short_description = 'Colors'


@admin.register(GeneratedMessage)
class GeneratedMessageAdmin(admin.ModelAdmin):
    """Admin interface for GeneratedMessage model."""
    
    list_display = [
        'id',
        'user',
        'event_link',
        'context_summary',
        'style_used',
        'tokens_used',
        'options_count',
        'created_at',
    ]
    list_filter = [
        'style_used',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'event__title',
        'context__bride_name',
        'context__groom_name',
    ]
    readonly_fields = [
        'id',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'event', 'style_used', 'tokens_used')
        }),
        ('Context', {
            'fields': ('context',),
            'classes': ('collapse',)
        }),
        ('Generated Options', {
            'fields': ('generated_options',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def event_link(self, obj):
        """Display event as a link."""
        if obj.event:
            from django.urls import reverse
            from django.utils.html import format_html
            url = reverse('admin:invitations_event_change', args=[obj.event.id])
            return format_html('<a href="{}">{}</a>', url, obj.event.title)
        return '-'
    event_link.short_description = 'Event'
    
    def context_summary(self, obj):
        """Display context summary."""
        return obj.get_context_summary()
    context_summary.short_description = 'Couple'
    
    def options_count(self, obj):
        """Display number of generated options."""
        if obj.generated_options:
            return len(obj.generated_options)
        return 0
    options_count.short_description = 'Options'


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    """Admin interface for AIUsageLog model."""
    
    list_display = [
        'id',
        'user',
        'feature_type',
        'tokens_used',
        'success',
        'processing_time_ms',
        'created_at',
    ]
    list_filter = [
        'feature_type',
        'success',
        'created_at',
    ]
    search_fields = [
        'user__email',
        'user__first_name',
        'user__last_name',
        'error_message',
    ]
    readonly_fields = [
        'id',
        'created_at',
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'feature_type', 'success', 'tokens_used', 'processing_time_ms')
        }),
        ('Request/Response Data', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual creation of usage logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing of usage logs."""
        return False
