"""
Admin configuration for invitations app
"""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Order, Invitation, Guest, InvitationViewLog


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'user', 'plan', 'event_type', 'status',
        'payment_status', 'created_at', 'approved_by'
    ]
    list_filter = ['status', 'payment_status', 'plan', 'created_at']
    search_fields = ['order_number', 'user__phone', 'user__full_name']
    list_select_related = ['user', 'plan', 'approved_by']
    date_hierarchy = 'created_at'
    
    fieldsets = [
        ('Order Info', {
            'fields': ('order_number', 'user', 'plan', 'event_type', 'event_type_name')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Payment', {
            'fields': ('payment_amount', 'payment_method', 'payment_status', 'payment_notes', 'payment_received_at')
        }),
        ('Approval', {
            'fields': ('approved_by', 'approved_at', 'admin_notes')
        }),
        ('Link Grants', {
            'fields': ('granted_regular_links', 'granted_test_links')
        }),
    ]
    
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    actions = ['approve_orders', 'reject_orders', 'mark_payment_received']
    
    def approve_orders(self, request, queryset):
        """Bulk approve orders"""
        for order in queryset.filter(status='PENDING_APPROVAL'):
            order.approve(request.user, 'Bulk approved via admin')
    approve_orders.short_description = "Approve selected orders"
    
    def reject_orders(self, request, queryset):
        """Bulk reject orders"""
        for order in queryset:
            order.reject(request.user, 'Bulk rejected via admin')
    reject_orders.short_description = "Reject selected orders"
    
    def mark_payment_received(self, request, queryset):
        """Mark payment as received"""
        queryset.filter(payment_status='PENDING').update(
            payment_status='RECEIVED',
            payment_received_at=timezone.now()
        )
    mark_payment_received.short_description = "Mark payment as received"


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        'event_title', 'slug', 'user', 'template', 'is_active',
        'is_expired', 'link_expires_at', 'unique_guests', 'preview_link'
    ]
    list_filter = ['is_active', 'is_expired', 'template__category', 'created_at']
    search_fields = ['event_title', 'slug', 'user__phone', 'host_name']
    list_select_related = ['user', 'template', 'order']
    readonly_fields = ['slug', 'share_url', 'created_at', 'updated_at']
    
    fieldsets = [
        ('Basic Info', {
            'fields': ('order', 'user', 'template', 'slug', 'share_url')
        }),
        ('Event Details', {
            'fields': ('event_title', 'event_date', 'event_venue', 'event_address', 'event_map_link')
        }),
        ('Host Info', {
            'fields': ('host_name', 'host_phone', 'custom_message')
        }),
        ('Media', {
            'fields': ('banner_image', 'gallery_images', 'background_music')
        }),
        ('Status', {
            'fields': ('is_active', 'is_expired', 'link_expires_at')
        }),
        ('Usage Stats', {
            'fields': ('regular_links_used', 'test_links_used', 'total_views', 'unique_guests')
        }),
    ]
    
    actions = ['activate_invitations', 'expire_invitations', 'extend_validity']
    
    def preview_link(self, obj):
        return format_html('<a href="{}" target="_blank">View</a>', obj.share_url)
    preview_link.short_description = 'Preview'
    
    def activate_invitations(self, request, queryset):
        for inv in queryset:
            inv.activate()
    activate_invitations.short_description = "Activate selected invitations"
    
    def expire_invitations(self, request, queryset):
        for inv in queryset:
            inv.expire()
    expire_invitations.short_description = "Expire selected invitations"
    
    def extend_validity(self, request, queryset):
        """Extend validity by 15 days"""
        from datetime import timedelta
        for inv in queryset:
            if inv.link_expires_at:
                inv.link_expires_at += timedelta(days=15)
            else:
                inv.link_expires_at = timezone.now() + timedelta(days=15)
            inv.is_expired = False
            inv.save()
    extend_validity.short_description = "Extend validity by 15 days"


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ['name', 'invitation', 'phone', 'viewed_at', 'device_type', 'is_test_link']
    list_filter = ['is_test_link', 'device_type', 'viewed_at']
    search_fields = ['name', 'phone', 'invitation__event_title']
    list_select_related = ['invitation']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'


@admin.register(InvitationViewLog)
class InvitationViewLogAdmin(admin.ModelAdmin):
    list_display = ['invitation', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['invitation__slug', 'ip_address']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'
