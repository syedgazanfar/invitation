"""
WhatsApp messaging through the WA-AKG gateway (apps/wa-gateway).

API: POST {WA_AKG_BASE_URL}/messages/{session}/{jid}/send
     Header X-API-Key, body {"message": {"text": "..."}}
"""
import logging
from urllib.parse import quote

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class WhatsAppError(Exception):
    """Raised when the WA-AKG gateway rejects or fails a send."""


class WhatsAppService:

    @staticmethod
    def is_configured() -> bool:
        return bool(
            getattr(settings, 'WA_AKG_BASE_URL', '')
            and getattr(settings, 'WA_AKG_API_KEY', '')
            and getattr(settings, 'WA_AKG_SESSION_ID', '')
        )

    @staticmethod
    def phone_to_jid(phone: str) -> str:
        """'+91 98765-43210' -> '919876543210@s.whatsapp.net'. Bare 10-digit numbers get India's 91."""
        digits = ''.join(ch for ch in str(phone) if ch.isdigit())
        if len(digits) == 10:
            digits = '91' + digits
        if len(digits) < 11:
            raise WhatsAppError(f'Invalid phone number for WhatsApp: {phone!r}')
        return f'{digits}@s.whatsapp.net'

    @staticmethod
    def send_text(phone: str, text: str) -> dict:
        if not WhatsAppService.is_configured():
            raise WhatsAppError('WA-AKG gateway is not configured (WA_AKG_BASE_URL / API_KEY / SESSION_ID)')

        jid = WhatsAppService.phone_to_jid(phone)
        base = settings.WA_AKG_BASE_URL.rstrip('/')
        session = quote(settings.WA_AKG_SESSION_ID, safe='')
        url = f'{base}/messages/{session}/{quote(jid, safe="")}/send'

        try:
            resp = requests.post(
                url,
                json={'message': {'text': text}},
                headers={'X-API-Key': settings.WA_AKG_API_KEY},
                timeout=getattr(settings, 'WA_AKG_TIMEOUT', 15),
            )
        except requests.RequestException as exc:
            raise WhatsAppError(f'WA-AKG request failed: {exc}') from exc

        try:
            data = resp.json()
        except ValueError:
            data = {}

        if resp.status_code >= 400 or data.get('status') is False:
            detail = data.get('message') or data.get('error') or resp.text[:300]
            raise WhatsAppError(f'WA-AKG error {resp.status_code}: {detail}')

        logger.info('WhatsApp message sent to %s', jid)
        return data
