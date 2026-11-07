"""
Business logic for enquiries.
"""
import logging
from typing import Optional

from django.conf import settings
from django.db import transaction

from ..models import Enquiry
from .whatsapp_service import WhatsAppService, WhatsAppError

logger = logging.getLogger(__name__)


class EnquiryService:

    @staticmethod
    def create_enquiry(data: dict, source_ip: Optional[str] = None, user_agent: str = '') -> Enquiry:
        enquiry = Enquiry.objects.create(
            **data,
            source_ip=source_ip,
            user_agent=(user_agent or '')[:500],
        )
        from ..tasks import send_enquiry_notifications
        transaction.on_commit(lambda: send_enquiry_notifications.delay(str(enquiry.id)))
        return enquiry

    @staticmethod
    def build_admin_message(enquiry: Enquiry) -> str:
        lines = [
            '*New enquiry received*',
            f'Name: {enquiry.name}',
            f'Phone: {enquiry.phone}',
        ]
        if enquiry.email:
            lines.append(f'Email: {enquiry.email}')
        lines.append(f'Event: {enquiry.get_event_type_display()}')
        if enquiry.event_date:
            lines.append(f'Event date: {enquiry.event_date:%d %b %Y}')
        if enquiry.message:
            lines.append(f'Message: {enquiry.message}')
        return '\n'.join(lines)

    @staticmethod
    def build_customer_message(enquiry: Enquiry) -> str:
        brand = getattr(settings, 'ENQUIRY_BRAND_NAME', 'Our team')
        return (
            f'Hi {enquiry.name}, thank you for your enquiry about your '
            f'{enquiry.get_event_type_display().lower()} invitation. '
            f'{brand} will get back to you shortly on this number.'
        )

    @staticmethod
    def notify(enquiry: Enquiry) -> Enquiry:
        """
        Send WhatsApp notifications. Each send is tracked separately, so a retry
        only re-sends what hasn't gone out yet. Raises WhatsAppError if anything
        failed (so the Celery task can retry).
        """
        if not WhatsAppService.is_configured():
            logger.warning('WA-AKG not configured; skipping WhatsApp for enquiry %s', enquiry.id)
            return enquiry

        errors = []

        if not enquiry.whatsapp_admin_notified:
            admin_numbers = getattr(settings, 'WA_AKG_ADMIN_NUMBERS', [])
            if admin_numbers:
                text = EnquiryService.build_admin_message(enquiry)
                sent_any = False
                for number in admin_numbers:
                    try:
                        WhatsAppService.send_text(number, text)
                        sent_any = True
                    except WhatsAppError as exc:
                        errors.append(f'admin {number}: {exc}')
                enquiry.whatsapp_admin_notified = sent_any
            else:
                logger.warning('WA_AKG_ADMIN_NUMBERS is empty; no admin WhatsApp sent for %s', enquiry.id)

        if (getattr(settings, 'WA_AKG_SEND_CUSTOMER_CONFIRMATION', True)
                and not enquiry.whatsapp_customer_notified):
            try:
                WhatsAppService.send_text(enquiry.phone, EnquiryService.build_customer_message(enquiry))
                enquiry.whatsapp_customer_notified = True
            except WhatsAppError as exc:
                errors.append(f'customer: {exc}')

        enquiry.whatsapp_error = '\n'.join(errors)
        enquiry.save(update_fields=[
            'whatsapp_admin_notified', 'whatsapp_customer_notified', 'whatsapp_error', 'updated_at',
        ])

        if errors:
            raise WhatsAppError('; '.join(errors))
        return enquiry
