"""
Tests for the authentication module.

Run with:
    docker-compose exec backend python src/manage.py test apps.authentication
or locally:
    python src/manage.py test apps.authentication --settings=config.settings_local
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

DEFAULT_PASSWORD = 'SecurePass123!'


def _make_user(**kwargs) -> User:
    """Create and save a test user with sensible defaults."""
    defaults = {
        'phone':             '+919876543210',
        'username':          'testuser',
        'email':             'test@example.com',
        'full_name':         'Test User',
        'is_approved':       True,
        'is_staff':          False,
        'is_superuser':      False,
        'is_blocked':        False,
    }
    defaults.update(kwargs)
    password = defaults.pop('password', DEFAULT_PASSWORD)
    user = User(**defaults)
    user.set_password(password)
    user.save()
    return user


# ---------------------------------------------------------------------------
# Service-layer tests (no HTTP)
# ---------------------------------------------------------------------------

class NormalizePhoneTests(TestCase):
    """Unit tests for _normalize_phone helper."""

    def _normalize(self, value):
        from apps.authentication.services import _normalize_phone
        return _normalize_phone(value)

    def test_10_digit(self):
        self.assertEqual(self._normalize('9876543210'), '+919876543210')

    def test_11_digit_with_leading_zero(self):
        self.assertEqual(self._normalize('09876543210'), '+919876543210')

    def test_12_digit_with_91(self):
        self.assertEqual(self._normalize('919876543210'), '+919876543210')

    def test_already_e164(self):
        self.assertEqual(self._normalize('+919876543210'), '+919876543210')

    def test_with_spaces(self):
        self.assertEqual(self._normalize('98765 43210'), '+919876543210')

    def test_with_dashes(self):
        self.assertEqual(self._normalize('98765-43210'), '+919876543210')


class UserLoginServiceTests(TestCase):

    def setUp(self):
        self.user = _make_user()

    def test_login_with_username_succeeds(self):
        from apps.authentication.services import LoginService
        ok, data, code, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')
        self.assertIn('access', data)
        self.assertIn('refresh', data)
        self.assertIn('user', data)

    def test_login_with_phone_succeeds(self):
        from apps.authentication.services import LoginService
        ok, data, code, _ = LoginService.user_login('+919876543210', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')

    def test_login_with_10_digit_phone_succeeds(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.user_login('9876543210', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')

    def test_wrong_password_returns_invalid_credentials(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.user_login('testuser', 'WrongPass!')
        self.assertFalse(ok)
        self.assertEqual(code, 'INVALID_CREDENTIALS')

    def test_nonexistent_user_returns_invalid_credentials(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.user_login('nobody', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'INVALID_CREDENTIALS')

    def test_blank_identifier_returns_invalid_credentials(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.user_login('', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'INVALID_CREDENTIALS')

    def test_blocked_user_returns_account_blocked(self):
        from apps.authentication.services import LoginService
        self.user.is_blocked = True
        self.user.save(update_fields=['is_blocked'])
        ok, _, code, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'ACCOUNT_BLOCKED')

    def test_unapproved_user_returns_pending_approval(self):
        from apps.authentication.services import LoginService
        self.user.is_approved = False
        self.user.save(update_fields=['is_approved'])
        ok, _, code, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'PENDING_APPROVAL')

    def test_staff_user_bypasses_approval_check(self):
        from apps.authentication.services import LoginService
        self.user.is_approved = False
        self.user.is_staff = True
        self.user.save(update_fields=['is_approved', 'is_staff'])
        ok, _, code, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')

    def test_superuser_bypasses_approval_check(self):
        from apps.authentication.services import LoginService
        self.user.is_approved = False
        self.user.is_superuser = True
        self.user.save(update_fields=['is_approved', 'is_superuser'])
        ok, _, code, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')

    def test_response_contains_user_fields(self):
        from apps.authentication.services import LoginService
        _, data, _, _ = LoginService.user_login('testuser', DEFAULT_PASSWORD)
        user_data = data['user']
        for field in ('id', 'username', 'phone', 'email', 'full_name',
                      'is_approved', 'is_phone_verified', 'is_staff', 'is_superuser'):
            self.assertIn(field, user_data)


class AdminLoginServiceTests(TestCase):

    def setUp(self):
        self.admin = _make_user(
            phone='+919000000001',
            username='admin',
            is_staff=True,
            is_approved=True,
        )
        self.regular = _make_user(
            phone='+919000000002',
            username='regular',
            is_staff=False,
            is_approved=True,
        )

    def test_admin_login_succeeds(self):
        from apps.authentication.services import LoginService
        ok, data, code, _ = LoginService.admin_login('admin', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')
        self.assertIn('permissions', data['user'])

    def test_non_admin_returns_not_admin(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.admin_login('regular', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'NOT_ADMIN')

    def test_admin_bypasses_approval_check(self):
        from apps.authentication.services import LoginService
        self.admin.is_approved = False
        self.admin.save(update_fields=['is_approved'])
        ok, _, code, _ = LoginService.admin_login('admin', DEFAULT_PASSWORD)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGIN_SUCCESS')

    def test_blocked_admin_returns_account_blocked(self):
        from apps.authentication.services import LoginService
        self.admin.is_blocked = True
        self.admin.save(update_fields=['is_blocked'])
        ok, _, code, _ = LoginService.admin_login('admin', DEFAULT_PASSWORD)
        self.assertFalse(ok)
        self.assertEqual(code, 'ACCOUNT_BLOCKED')

    def test_wrong_password_returns_invalid_credentials(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.admin_login('admin', 'WrongPass!')
        self.assertFalse(ok)
        self.assertEqual(code, 'INVALID_CREDENTIALS')

    def test_admin_payload_contains_permissions(self):
        from apps.authentication.services import LoginService
        _, data, _, _ = LoginService.admin_login('admin', DEFAULT_PASSWORD)
        self.assertIn('permissions', data['user'])
        self.assertTrue(data['user']['permissions']['is_staff'])


class LogoutServiceTests(TestCase):

    def setUp(self):
        self.user = _make_user()

    def _get_tokens(self):
        from apps.authentication.services import _generate_tokens
        return _generate_tokens(self.user)

    def test_logout_success(self):
        from apps.authentication.services import LoginService
        tokens = self._get_tokens()
        ok, code, _ = LoginService.logout(tokens['refresh'], self.user)
        self.assertTrue(ok)
        self.assertEqual(code, 'LOGOUT_SUCCESS')

    def test_empty_token_returns_validation_error(self):
        from apps.authentication.services import LoginService
        ok, code, _ = LoginService.logout('', self.user)
        self.assertFalse(ok)
        self.assertEqual(code, 'VALIDATION_ERROR')

    def test_double_logout_returns_token_invalid(self):
        from apps.authentication.services import LoginService
        tokens = self._get_tokens()
        LoginService.logout(tokens['refresh'], self.user)
        ok, code, _ = LoginService.logout(tokens['refresh'], self.user)
        self.assertFalse(ok)
        self.assertEqual(code, 'TOKEN_INVALID')

    def test_garbage_token_returns_token_invalid(self):
        from apps.authentication.services import LoginService
        ok, code, _ = LoginService.logout('not.a.valid.token', self.user)
        self.assertFalse(ok)
        self.assertEqual(code, 'TOKEN_INVALID')


class TokenRefreshServiceTests(TestCase):

    def setUp(self):
        self.user = _make_user()

    def _get_tokens(self):
        from apps.authentication.services import _generate_tokens
        return _generate_tokens(self.user)

    def test_refresh_returns_new_access_token(self):
        from apps.authentication.services import LoginService
        tokens = self._get_tokens()
        ok, access, code, _ = LoginService.refresh_access_token(tokens['refresh'])
        self.assertTrue(ok)
        self.assertEqual(code, 'TOKEN_REFRESHED')
        self.assertIsNotNone(access)
        self.assertNotEqual(access, tokens['access'])

    def test_empty_token_returns_validation_error(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.refresh_access_token('')
        self.assertFalse(ok)
        self.assertEqual(code, 'VALIDATION_ERROR')

    def test_invalid_token_returns_token_invalid(self):
        from apps.authentication.services import LoginService
        ok, _, code, _ = LoginService.refresh_access_token('not.a.real.token')
        self.assertFalse(ok)
        self.assertEqual(code, 'TOKEN_INVALID')


# ---------------------------------------------------------------------------
# API (HTTP) tests
# ---------------------------------------------------------------------------

class UserLoginAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        self.url = '/api/v1/auth/login/'

    def test_successful_login_returns_200(self):
        res = self.client.post(
            self.url, {'identifier': 'testuser', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])
        self.assertIn('access', res.data['data'])
        self.assertIn('refresh', res.data['data'])

    def test_missing_identifier_returns_400(self):
        res = self.client.post(self.url, {'password': DEFAULT_PASSWORD})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.data['success'])
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')

    def test_missing_password_returns_400(self):
        res = self.client.post(self.url, {'identifier': 'testuser'})
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.data['success'])

    def test_wrong_password_returns_401(self):
        res = self.client.post(
            self.url, {'identifier': 'testuser', 'password': 'WrongPass!'}
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data['code'], 'INVALID_CREDENTIALS')

    def test_blocked_user_returns_403(self):
        self.user.is_blocked = True
        self.user.save(update_fields=['is_blocked'])
        res = self.client.post(
            self.url, {'identifier': 'testuser', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'ACCOUNT_BLOCKED')

    def test_unapproved_user_returns_403(self):
        self.user.is_approved = False
        self.user.save(update_fields=['is_approved'])
        res = self.client.post(
            self.url, {'identifier': 'testuser', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'PENDING_APPROVAL')

    def test_login_with_phone_returns_200(self):
        res = self.client.post(
            self.url, {'identifier': '9876543210', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])

    def test_empty_body_returns_400(self):
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)


class AdminLoginAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.admin = _make_user(
            phone='+919000000001',
            username='admin',
            is_staff=True,
        )
        self.regular = _make_user(
            phone='+919000000002',
            username='regular',
            is_staff=False,
        )
        self.url = '/api/v1/auth/admin/login/'

    def test_admin_login_returns_200(self):
        res = self.client.post(
            self.url, {'identifier': 'admin', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])
        self.assertIn('permissions', res.data['data']['user'])

    def test_non_admin_returns_403(self):
        res = self.client.post(
            self.url, {'identifier': 'regular', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'NOT_ADMIN')

    def test_wrong_password_returns_401(self):
        res = self.client.post(
            self.url, {'identifier': 'admin', 'password': 'WrongPass!'}
        )
        self.assertEqual(res.status_code, 401)

    def test_unapproved_admin_still_succeeds(self):
        self.admin.is_approved = False
        self.admin.save(update_fields=['is_approved'])
        res = self.client.post(
            self.url, {'identifier': 'admin', 'password': DEFAULT_PASSWORD}
        )
        self.assertEqual(res.status_code, 200)

    def test_empty_body_returns_400(self):
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)


class LogoutAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        self.url = '/api/v1/auth/logout/'

    def _login(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'identifier': 'testuser', 'password': DEFAULT_PASSWORD},
        )
        return res.data['data']

    def test_logout_requires_authentication(self):
        res = self.client.post(self.url, {'refresh': 'dummy'})
        self.assertEqual(res.status_code, 401)

    def test_logout_succeeds(self):
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        res = self.client.post(self.url, {'refresh': tokens['refresh']})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data['success'])

    def test_double_logout_rejected(self):
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        self.client.post(self.url, {'refresh': tokens['refresh']})
        res = self.client.post(self.url, {'refresh': tokens['refresh']})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data['code'], 'TOKEN_INVALID')

    def test_missing_refresh_returns_400(self):
        tokens = self._login()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + tokens['access'])
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)


class TokenRefreshAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = _make_user()
        self.url = '/api/v1/auth/token/refresh/'

    def _get_refresh_token(self):
        res = self.client.post(
            '/api/v1/auth/login/',
            {'identifier': 'testuser', 'password': DEFAULT_PASSWORD},
        )
        return res.data['data']['refresh']

    def test_refresh_returns_new_access_token(self):
        refresh = self._get_refresh_token()
        res = self.client.post(self.url, {'refresh': refresh})
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data['data'])

    def test_invalid_token_returns_401(self):
        res = self.client.post(self.url, {'refresh': 'not.a.real.token'})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data['code'], 'TOKEN_INVALID')

    def test_missing_token_returns_400(self):
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)
