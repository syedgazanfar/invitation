"""
Serializers for Plans and Templates
"""
from rest_framework import serializers
from .models import Plan, Template, InvitationCategory


class PlanSerializer(serializers.ModelSerializer):
    """Serializer for Plan model"""
    display_price = serializers.CharField(read_only=True)
    
    class Meta:
        model = Plan
        fields = [
            'id', 'code', 'name', 'description', 'regular_links',
            'test_links', 'price_inr', 'display_price', 'features',
            'is_active', 'sort_order'
        ]


class InvitationCategorySerializer(serializers.ModelSerializer):
    """Serializer for InvitationCategory"""
    
    class Meta:
        model = InvitationCategory
        fields = ['id', 'code', 'name', 'description', 'icon', 'is_active']


class TemplateListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for template listing"""
    plan_code = serializers.CharField(source='plan.code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'thumbnail',
            'plan_code', 'category_name', 'animation_type',
            'supports_gallery', 'supports_music', 'supports_video',
            'is_premium', 'use_count'
        ]


class TemplateDetailSerializer(serializers.ModelSerializer):
    """Full serializer for template details"""
    plan = PlanSerializer(read_only=True)
    category = InvitationCategorySerializer(read_only=True)
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'description', 'thumbnail', 'preview_url',
            'plan', 'category', 'animation_type', 'animation_config',
            'theme_colors', 'supports_gallery', 'supports_music',
            'supports_video', 'supports_rsvp', 'use_count'
        ]


class TemplatePreviewSerializer(serializers.ModelSerializer):
    """Serializer for template preview"""
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'thumbnail', 'animation_type',
            'theme_colors', 'preview_url'
        ]
