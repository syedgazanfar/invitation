"""
Enquiry model: public "contact us / get a quote" submissions.
"""
import uuid
from django.db import models


class Enquiry(models.Model):
    class EventType(models.TextChoices):
        WEDDING = 'WEDDING', 'Wedding'
        ENGAGEMENT = 'ENGAGEMENT', 'Engagement'
        BIRTHDAY = 'BIRTHDAY', 'Birthday'
        PARTY = 'PARTY', 'Party'
        RELIGIOUS = 'RELIGIOUS', 'Religious / Festival'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        NEW = 'NEW', 'New'
        CONTACTED = 'CONTACTED', 'Contacted'
        CONVERTED = 'CONVERTED', 'Converted'
        CLOSED = 'CLOSED', 'Closed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, help_text='E.164 format, e.g. +919876543210')
    email = models.EmailField(blank=True)
    event_type = models.CharField(max_length=20, choices=EventType.choices, default=EventType.WEDDING)
    event_date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True, max_length=2000)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    admin_notes = models.TextField(blank=True)

    # WhatsApp delivery tracking (via WA-AKG gateway)
    whatsapp_admin_notified = models.BooleanField(default=False)
    whatsapp_customer_notified = models.BooleanField(default=False)
    whatsapp_error = models.TextField(blank=True)

    source_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Enquiries'
        indexes = [
            models.Index(fields=['status', '-created_at'], name='enquiry_status_created_idx'),
            models.Index(fields=['phone'], name='enquiry_phone_idx'),
        ]

    def __str__(self):
        return f'{self.name} ({self.phone}) - {self.get_event_type_display()}'
