"""
Admin configuration for plans app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Plan, Template, InvitationCategory


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'regular_links', 'test_links', 'price_inr', 'is_active', 'sort_order']
    list_filter = ['is_active', 'code']
    search_fields = ['name', 'description']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']
    
    fieldsets = [
        (None, {
            'fields': ('code', 'name', 'description', 'sort_order')
        }),
        ('Pricing & Limits', {
            'fields': ('regular_links', 'test_links', 'price_inr')
        }),
        ('Features', {
            'fields': ('features', 'is_active')
        }),
    ]


@admin.register(InvitationCategory)
class InvitationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'sort_order']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active', 'sort_order']
    ordering = ['sort_order']


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan', 'category', 'animation_type', 'is_active', 'use_count', 'thumbnail_preview']
    list_filter = ['plan', 'category', 'animation_type', 'is_active', 'is_premium']
    search_fields = ['name', 'description']
    list_select_related = ['plan', 'category']
    
    fieldsets = [
        (None, {
            'fields': ('name', 'description', 'thumbnail', 'plan', 'category')
        }),
        ('Animation & Theme', {
            'fields': ('animation_type', 'animation_config', 'theme_colors')
        }),
        ('Features', {
            'fields': ('supports_gallery', 'supports_music', 'supports_video', 'supports_rsvp')
        }),
        ('Status & Stats', {
            'fields': ('is_active', 'is_premium', 'sort_order', 'use_count', 'preview_url')
        }),
    ]
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.thumbnail.url)
        return "No image"
    thumbnail_preview.short_description = 'Preview'
