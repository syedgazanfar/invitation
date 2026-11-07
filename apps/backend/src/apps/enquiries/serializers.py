import phonenumbers
from django.utils import timezone
from rest_framework import serializers

from .models import Enquiry


class EnquiryCreateSerializer(serializers.ModelSerializer):
    # Honeypot: real users never see or fill this field.
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Enquiry
        fields = ['id', 'name', 'phone', 'email', 'event_type', 'event_date', 'message', 'website', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError('Please enter your name.')
        return value

    def validate_phone(self, value):
        try:
            parsed = phonenumbers.parse(value, 'IN')
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError('Enter a valid phone number.')
        if not phonenumbers.is_valid_number(parsed):
            raise serializers.ValidationError('Enter a valid phone number.')
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    def validate_event_date(self, value):
        if value and value < timezone.localdate():
            raise serializers.ValidationError('Event date cannot be in the past.')
        return value
