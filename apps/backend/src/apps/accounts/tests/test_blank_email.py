"""
Regression: User.email is unique but optional. A blank email must be stored as
NULL (NULLs never collide), not '' — otherwise every user after the first one
who signs up without an email hits accounts_user_email_key and gets a 500.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

User = get_user_model()


def _payload(n, **extra):
    data = {
        'phone': f'+91900000000{n}',
        'username': f'blankemail{n}',
        'password': 'SmokeTest!2026',
        'password_confirm': 'SmokeTest!2026',
    }
    data.update(extra)
    return data


class BlankEmailTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_two_signups_without_email_both_succeed(self):
        r1 = self.client.post('/api/v1/auth/register/', _payload(1), format='json')
        r2 = self.client.post('/api/v1/auth/register/', _payload(2), format='json')
        self.assertEqual(r1.status_code, 201, r1.content)
        self.assertEqual(r2.status_code, 201, r2.content)
        self.assertEqual(User.objects.filter(email__isnull=True).count(), 2)

    def test_explicit_empty_email_is_stored_as_null(self):
        self.client.post('/api/v1/auth/register/', _payload(3), format='json')
        r = self.client.post('/api/v1/auth/register/', _payload(4, email=''), format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIsNone(User.objects.get(username='blankemail4').email)

    def test_create_user_without_email_stores_null(self):
        User.objects.create_user(username='a', phone='+919000000101', password='x')
        User.objects.create_user(username='b', phone='+919000000102', password='x')
        self.assertEqual(User.objects.filter(email__isnull=True).count(), 2)

    def test_duplicate_real_email_is_still_rejected(self):
        self.client.post('/api/v1/auth/register/', _payload(5, email='same@example.com'), format='json')
        r = self.client.post('/api/v1/auth/register/', _payload(6, email='same@example.com'), format='json')
        self.assertEqual(r.status_code, 400, r.content)
        self.assertIn('email', r.json())
