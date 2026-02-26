"""
Serializers for Invitations, Orders, and Guests
"""
from rest_framework import serializers
from django.utils import timezone
from .models import Order, Invitation, Guest, InvitationViewLog
from apps.plans.serializers import PlanSerializer, TemplateListSerializer


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listing"""
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    has_invitation = serializers.SerializerMethodField()
    invitation_slug = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'plan_name', 'event_type', 'event_type_name',
            'status', 'payment_status', 'approved_at', 'created_at',
            'has_invitation', 'invitation_slug', 'granted_regular_links',
            'granted_test_links'
        ]
    
    def get_has_invitation(self, obj):
        return hasattr(obj, 'invitation')
    
    def get_invitation_slug(self, obj):
        if hasattr(obj, 'invitation'):
            return obj.invitation.slug
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    """Detailed order serializer"""
    plan = PlanSerializer(read_only=True)
    invitation_data = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'plan', 'event_type', 'event_type_name',
            'status', 'payment_amount', 'payment_method', 'payment_status',
            'payment_notes', 'payment_received_at', 'approved_by', 'approved_at',
            'admin_notes', 'granted_regular_links', 'granted_test_links',
            'created_at', 'updated_at', 'invitation_data'
        ]
    
    def get_invitation_data(self, obj):
        if hasattr(obj, 'invitation'):
            inv = obj.invitation
            return {
                'id': str(inv.id),
                'slug': inv.slug,
                'event_title': inv.event_title,
                'is_active': inv.is_active,
                'is_expired': inv.is_expired,
                'link_expires_at': inv.link_expires_at,
                'share_url': inv.share_url,
                'remaining_regular_links': inv.remaining_regular_links,
                'remaining_test_links': inv.remaining_test_links,
                'regular_links_used': inv.regular_links_used,
                'test_links_used': inv.test_links_used,
                'total_views': inv.total_views,
                'unique_guests': inv.unique_guests
            }
        return None


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    plan_code = serializers.CharField(write_only=True)
    
    class Meta:
        model = Order
        fields = ['plan_code', 'event_type', 'event_type_name']
    
    def validate_plan_code(self, value):
        from apps.plans.models import Plan
        try:
            plan = Plan.objects.get(code=value.upper(), is_active=True)
            return plan
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan code")
    
    def create(self, validated_data):
        plan = validated_data.pop('plan_code')
        user = self.context['request'].user
        
        order = Order.objects.create(
            user=user,
            plan=plan,
            payment_amount=plan.price_inr,
            granted_regular_links=plan.regular_links,
            granted_test_links=plan.test_links,
            status='PENDING_PAYMENT',
            **validated_data
        )
        return order


class GuestSerializer(serializers.ModelSerializer):
    """Serializer for guest data"""
    
    class Meta:
        model = Guest
        fields = [
            'id', 'name', 'phone', 'message', 'attending',
            'device_type', 'browser', 'os', 'viewed_at'
        ]


class InvitationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invitation listing"""
    template_name = serializers.CharField(source='template.name', read_only=True)
    template_thumbnail = serializers.ImageField(source='template.thumbnail', read_only=True)
    order_status = serializers.CharField(source='order.status', read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'slug', 'event_title', 'event_date', 'template_name',
            'template_thumbnail', 'order_status', 'is_active', 'is_expired',
            'link_expires_at', 'total_views', 'unique_guests'
        ]


class InvitationDetailSerializer(serializers.ModelSerializer):
    """Full invitation details"""
    template = TemplateListSerializer(read_only=True)
    remaining_regular_links = serializers.IntegerField(read_only=True)
    remaining_test_links = serializers.IntegerField(read_only=True)
    share_url = serializers.CharField(read_only=True)
    guests = GuestSerializer(many=True, read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'id', 'slug', 'template', 'event_title', 'event_date',
            'event_venue', 'event_address', 'event_map_link',
            'host_name', 'host_phone', 'custom_message',
            'banner_image', 'gallery_images', 'background_music',
            'is_active', 'is_expired', 'link_expires_at', 'share_url',
            'remaining_regular_links', 'remaining_test_links',
            'regular_links_used', 'test_links_used',
            'total_views', 'unique_guests', 'guests',
            'created_at', 'updated_at'
        ]


class InvitationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invitations"""
    order_id = serializers.UUIDField(write_only=True)
    template_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'order_id', 'template_id', 'event_title', 'event_date',
            'event_venue', 'event_address', 'event_map_link',
            'host_name', 'host_phone', 'custom_message',
            'banner_image', 'gallery_images'
        ]
    
    def validate_order_id(self, value):
        try:
            order = Order.objects.get(id=value, user=self.context['request'].user)
            if not order.can_create_invitation:
                raise serializers.ValidationError("Order is not approved for creating invitation")
            if hasattr(order, 'invitation'):
                raise serializers.ValidationError("Invitation already exists for this order")
            return order
        except Order.DoesNotExist:
            raise serializers.ValidationError("Invalid order")
    
    def validate_template_id(self, value):
        from apps.plans.models import Template
        try:
            return Template.objects.get(id=value, is_active=True)
        except Template.DoesNotExist:
            raise serializers.ValidationError("Invalid template")
    
    def create(self, validated_data):
        order = validated_data.pop('order_id')
        template = validated_data.pop('template_id')
        
        invitation = Invitation.objects.create(
            order=order,
            user=self.context['request'].user,
            template=template,
            is_active=order.is_approved,
            link_expires_at=timezone.now() + timezone.timedelta(days=15) if order.is_approved else None,
            **validated_data
        )
        return invitation


class InvitationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating invitations"""
    
    class Meta:
        model = Invitation
        fields = [
            'event_title', 'event_date', 'event_venue', 'event_address',
            'event_map_link', 'host_name', 'host_phone', 'custom_message',
            'gallery_images'
        ]


class GuestRegistrationSerializer(serializers.Serializer):
    """Serializer for guest registration"""
    name = serializers.CharField(max_length=200, required=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    attending = serializers.BooleanField(required=False, allow_null=True)
    
    # Device fingerprinting data
    fingerprint = serializers.CharField(required=True, write_only=True)
    screen_resolution = serializers.CharField(required=False, allow_blank=True)
    timezone_offset = serializers.CharField(required=False, allow_blank=True)
    languages = serializers.CharField(required=False, allow_blank=True)
    canvas_hash = serializers.CharField(required=False, allow_blank=True)
    
    # Session data
    session_id = serializers.CharField(required=False, allow_blank=True)
    is_test = serializers.BooleanField(default=False)


class GuestCheckSerializer(serializers.Serializer):
    """Serializer for checking if guest already registered"""
    fingerprint = serializers.CharField(required=True)


class PublicInvitationSerializer(serializers.ModelSerializer):
    """Public serializer for invitation viewing (no sensitive data)"""
    template_animation = serializers.CharField(source='template.animation_type', read_only=True)
    template_theme = serializers.JSONField(source='template.theme_colors', read_only=True)
    template_config = serializers.JSONField(source='template.animation_config', read_only=True)
    
    class Meta:
        model = Invitation
        fields = [
            'event_title', 'event_date', 'event_venue', 'event_address',
            'event_map_link', 'host_name', 'custom_message', 'banner_image',
            'gallery_images', 'background_music', 'template_animation',
            'template_theme', 'template_config'
        ]


class InvitationStatsSerializer(serializers.Serializer):
    """Serializer for invitation statistics"""
    total_views = serializers.IntegerField()
    unique_guests = serializers.IntegerField()
    regular_links_used = serializers.IntegerField()
    test_links_used = serializers.IntegerField()
    remaining_regular_links = serializers.IntegerField()
    remaining_test_links = serializers.IntegerField()
    is_link_valid = serializers.BooleanField()
    expires_in_days = serializers.IntegerField()


class ExportGuestsSerializer(serializers.Serializer):
    """Serializer for exporting guest data"""
    format = serializers.ChoiceField(choices=['csv', 'excel'], default='csv')
