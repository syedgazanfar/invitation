from django.contrib import admin, messages

from .models import Enquiry
from .tasks import send_enquiry_notifications


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'phone', 'event_type', 'event_date', 'status',
        'whatsapp_admin_notified', 'whatsapp_customer_notified', 'created_at',
    ]
    list_filter = ['status', 'event_type', 'whatsapp_admin_notified', 'whatsapp_customer_notified', 'created_at']
    list_editable = ['status']
    search_fields = ['name', 'phone', 'email', 'message']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'id', 'whatsapp_admin_notified', 'whatsapp_customer_notified', 'whatsapp_error',
        'source_ip', 'user_agent', 'created_at', 'updated_at',
    ]
    fieldsets = [
        ('Enquiry', {'fields': ('id', 'name', 'phone', 'email', 'event_type', 'event_date', 'message')}),
        ('Follow-up', {'fields': ('status', 'admin_notes')}),
        ('WhatsApp', {'fields': ('whatsapp_admin_notified', 'whatsapp_customer_notified', 'whatsapp_error')}),
        ('Meta', {'fields': ('source_ip', 'user_agent', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    ]
    actions = ['resend_whatsapp']

    @admin.action(description='Re-send pending WhatsApp notifications')
    def resend_whatsapp(self, request, queryset):
        for enquiry in queryset:
            send_enquiry_notifications.delay(str(enquiry.id))
        self.message_user(request, f'Queued WhatsApp notifications for {queryset.count()} enquiries.', messages.SUCCESS)
