"""
How real visitors break the enquiry endpoint (server side).
"""
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.enquiries.models import Enquiry

WA = dict(
    WA_AKG_BASE_URL='http://wa-gateway:3000/api',
    WA_AKG_API_KEY='wag_test',
    WA_AKG_SESSION_ID='main',
    WA_AKG_ADMIN_NUMBERS=['+919923928181'],
)
URL = '/api/v1/enquiries/'


def _ok():
    r = mock.Mock(status_code=200)
    r.json.return_value = {'status': True}
    return r


@override_settings(**WA)
class RetryAfterDroppedConnectionTest(TestCase):
    """
    Break #4 (server half): the request reached us but the phone lost signal
    before the response arrived, so the visitor taps "Send" again; or they had
    the page open in two tabs. One person must not become two enquiries and
    the owner must not get the same WhatsApp alert twice.
    """

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok())
    def test_same_number_again_within_minutes_is_one_enquiry_and_one_alert(self, post):
        body = {'name': 'Asha Patil', 'phone': '+919876543210', 'event_date': None, 'website': ''}
        with self.captureOnCommitCallbacks(execute=True):
            first = self.client.post(URL, body, format='json')
        messages_after_first = post.call_count  # admin alert + customer confirmation
        with self.captureOnCommitCallbacks(execute=True):
            second = self.client.post(URL, {**body, 'phone': '98765 43210'}, format='json')  # retyped differently

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)  # the visitor still sees success
        self.assertEqual(Enquiry.objects.count(), 1)
        self.assertEqual(first.json()['data']['id'], second.json()['data']['id'])
        self.assertGreater(messages_after_first, 0)
        self.assertEqual(post.call_count, messages_after_first)  # the retry sends no WhatsApp at all

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok())
    def test_retry_fills_in_a_date_the_first_attempt_missed(self, post):
        self.client.post(URL, {'name': 'Asha', 'phone': '+919876543210', 'event_date': None}, format='json')
        date = (timezone.localdate() + timedelta(days=40)).isoformat()
        self.client.post(URL, {'name': 'Asha', 'phone': '+919876543210', 'event_date': date}, format='json')
        self.assertEqual(Enquiry.objects.get().event_date.isoformat(), date)

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok())
    def test_same_number_a_day_later_is_a_new_enquiry(self, post):
        self.client.post(URL, {'name': 'Asha', 'phone': '+919876543210'}, format='json')
        Enquiry.objects.update(created_at=timezone.now() - timedelta(days=1))
        self.client.post(URL, {'name': 'Asha', 'phone': '+919876543210'}, format='json')
        self.assertEqual(Enquiry.objects.count(), 2)

    @mock.patch('apps.enquiries.services.whatsapp_service.requests.post', return_value=_ok())
    def test_different_people_at_the_same_time_are_separate(self, post):
        self.client.post(URL, {'name': 'Asha', 'phone': '+919876543210'}, format='json')
        self.client.post(URL, {'name': 'Ravi', 'phone': '+919812345678'}, format='json')
        self.assertEqual(Enquiry.objects.count(), 2)


class PhoneFormatsRealPeopleTypeTest(TestCase):
    """Break #2 (server half): the formats people actually type must all land as the same E.164 number."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()

    def test_common_indian_formats_normalise_to_e164(self):
        for i, typed in enumerate(['098765 43210', '+91-98765-43210', '91 98765 43210', '(+91) 9876543210']):
            r = self.client.post(URL, {'name': f'Person {i}', 'phone': typed}, format='json')
            self.assertEqual(r.status_code, 201, (typed, r.content))
            self.assertEqual(Enquiry.objects.get(id=r.json()['data']['id']).phone, '+919876543210', typed)
            Enquiry.objects.all().delete()  # avoid the duplicate-retry merge between formats
