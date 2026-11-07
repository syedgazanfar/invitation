"""
Tests for the enquiry form and WA-AKG WhatsApp integration.
"""
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.enquiries.models import Enquiry
from apps.enquiries.services import EnquiryService, WhatsAppService, WhatsAppError

WA_SETTINGS = dict(
    WA_AKG_BASE_URL='http://wa-gateway:3000/api',
    WA_AKG_API_KEY='wag_test',
    WA_AKG_SESSION_ID='main',
    WA_AKG_ADMIN_NUMBERS=['+919000000001'],
    WA_AKG_SEND_CUSTOMER_CONFIRMATION=True,
)


def _ok_response():
    resp = mock.Mock(status_code=200)
    resp.json.return_value = {'status': True, 'message': 'sent'}
    return resp


class PhoneToJidTest(TestCase):
    def test_e164(self):
        self.assertEqual(WhatsAppService.phone_to_jid('+919876543210'), '919876543210@s.whatsapp.net')

    def test_ten_digit_gets_india_prefix(self):
        self.assertEqual(WhatsAppService.phone_to_jid('98765 43210'), '919876543210@s.whatsapp.net')

    def test_too_short(self):
        with self.assertRaises(WhatsAppError):
            WhatsAppService.phone_to_jid('12345')


@override_settings(**WA_SETTINGS)
class SendTextTest(TestCase):
    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok_response())
    def test_posts_to_wa_akg(self, post):
        WhatsAppService.send_text('+919876543210', 'hello')
        url = post.call_args.args[0]
        self.assertEqual(url, 'http://wa-gateway:3000/api/messages/main/919876543210%40s.whatsapp.net/send')
        self.assertEqual(post.call_args.kwargs['json'], {'message': {'text': 'hello'}})
        self.assertEqual(post.call_args.kwargs['headers'], {'X-API-Key': 'wag_test'})

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post')
    def test_status_false_raises(self, post):
        resp = mock.Mock(status_code=200)
        resp.json.return_value = {'status': False, 'message': 'Session not connected'}
        post.return_value = resp
        with self.assertRaisesMessage(WhatsAppError, 'Session not connected'):
            WhatsAppService.send_text('+919876543210', 'hello')

    @override_settings(WA_AKG_API_KEY='')
    def test_not_configured(self):
        self.assertFalse(WhatsAppService.is_configured())


@override_settings(**WA_SETTINGS)
class NotifyTest(TestCase):
    def setUp(self):
        self.enquiry = Enquiry.objects.create(name='Asha', phone='+919876543210', event_type='WEDDING')

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok_response())
    def test_sends_admin_and_customer(self, post):
        EnquiryService.notify(self.enquiry)
        self.enquiry.refresh_from_db()
        self.assertTrue(self.enquiry.whatsapp_admin_notified)
        self.assertTrue(self.enquiry.whatsapp_customer_notified)
        self.assertEqual(post.call_count, 2)
        admin_text = post.call_args_list[0].kwargs['json']['message']['text']
        self.assertIn('Asha', admin_text)
        self.assertIn('+919876543210', admin_text)

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post')
    def test_retry_only_resends_failed_part(self, post):
        fail = mock.Mock(status_code=500, text='boom')
        fail.json.return_value = {}
        post.side_effect = [_ok_response(), fail]
        with self.assertRaises(WhatsAppError):
            EnquiryService.notify(self.enquiry)
        self.enquiry.refresh_from_db()
        self.assertTrue(self.enquiry.whatsapp_admin_notified)
        self.assertFalse(self.enquiry.whatsapp_customer_notified)
        self.assertIn('customer', self.enquiry.whatsapp_error)

        post.side_effect = None
        post.return_value = _ok_response()
        post.reset_mock()
        EnquiryService.notify(self.enquiry)
        self.assertEqual(post.call_count, 1)  # only the customer message
        self.enquiry.refresh_from_db()
        self.assertTrue(self.enquiry.whatsapp_customer_notified)
        self.assertEqual(self.enquiry.whatsapp_error, '')

    @override_settings(WA_AKG_BASE_URL='')
    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post')
    def test_skips_when_not_configured(self, post):
        EnquiryService.notify(self.enquiry)
        post.assert_not_called()


@override_settings(**WA_SETTINGS)
class EnquiryApiTest(TestCase):
    url = '/api/v1/enquiries/'

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def _payload(self, **overrides):
        data = {
            'name': 'Ravi Kumar',
            'phone': '98765 43210',
            'email': 'ravi@example.com',
            'event_type': 'WEDDING',
            'event_date': (timezone.localdate() + timedelta(days=30)).isoformat(),
            'message': 'Need a Telugu wedding invite',
        }
        data.update(overrides)
        return data

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok_response())
    def test_create_enquiry_and_notify(self, post):
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertTrue(resp.data['success'])
        enquiry = Enquiry.objects.get()
        self.assertEqual(enquiry.phone, '+919876543210')  # normalised to E.164
        self.assertTrue(enquiry.whatsapp_admin_notified)
        self.assertTrue(enquiry.whatsapp_customer_notified)
        self.assertEqual(post.call_count, 2)

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post')
    def test_whatsapp_failure_still_saves_enquiry(self, post):
        import requests
        post.side_effect = requests.ConnectionError('gateway down')
        with self.captureOnCommitCallbacks(execute=True):
            resp = self.client.post(self.url, self._payload(), format='json')
        self.assertEqual(resp.status_code, 201)
        enquiry = Enquiry.objects.get()
        self.assertFalse(enquiry.whatsapp_admin_notified)
        self.assertIn('gateway down', enquiry.whatsapp_error)

    def test_invalid_phone(self):
        resp = self.client.post(self.url, self._payload(phone='123'), format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('phone', resp.data['errors'])

    def test_past_event_date(self):
        past = (timezone.localdate() - timedelta(days=1)).isoformat()
        resp = self.client.post(self.url, self._payload(event_date=past), format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('event_date', resp.data['errors'])

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post')
    def test_honeypot_drops_silently(self, post):
        resp = self.client.post(self.url, self._payload(website='http://spam'), format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(Enquiry.objects.count(), 0)
        post.assert_not_called()

    def test_options(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        values = [o['value'] for o in resp.data['data']['event_types']]
        self.assertIn('WEDDING', values)

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok_response())
    def test_rate_limited(self, post):
        from rest_framework.settings import api_settings
        limit = int(api_settings.DEFAULT_THROTTLE_RATES['enquiry'].split('/')[0])
        for _ in range(limit):
            self.assertEqual(self.client.post(self.url, self._payload(), format='json').status_code, 201)
        self.assertEqual(self.client.post(self.url, self._payload(), format='json').status_code, 429)
