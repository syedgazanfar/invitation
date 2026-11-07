"""
Celery tasks for enquiries.
"""
import logging

from celery import shared_task

from .models import Enquiry
from .services import EnquiryService, WhatsAppError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_enquiry_notifications(self, enquiry_id: str):
    try:
        enquiry = Enquiry.objects.get(id=enquiry_id)
    except Enquiry.DoesNotExist:
        logger.error('Enquiry %s not found for WhatsApp notification', enquiry_id)
        return

    try:
        EnquiryService.notify(enquiry)
    except WhatsAppError as exc:
        logger.warning('WhatsApp notify failed for enquiry %s: %s', enquiry_id, exc)
        if self.request.is_eager:
            return  # don't raise into the HTTP request in synchronous (dev/test) mode
        raise self.retry(exc=exc)
