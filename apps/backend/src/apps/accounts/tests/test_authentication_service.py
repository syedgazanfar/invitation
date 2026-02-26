"""
Unit tests for AuthenticationService.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.services import AuthenticationService
from apps.accounts.models import UserActivity

User = get_user_model()


class AuthenticationServiceTest(TestCase):
    """Test cases for AuthenticationService."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone='+911234567890'
        )

    def test_register_user_success(self):
        """Test user registration successfully."""
        request = self.factory.post('/register/')

        success, user, error = AuthenticationService.register_user(
            email='newuser@example.com',
            password='newpass123',
            full_name='New User',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.full_name, 'New User')
        self.assertFalse(user.is_verified)

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        request = self.factory.post('/register/')

        success, user, error = AuthenticationService.register_user(
            email='test@example.com',  # Already exists
            password='newpass123',
            full_name='Duplicate User',
            request=request
        )

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIsNotNone(error)
        self.assertIn('already exists', error.lower())

    def test_register_user_invalid_email(self):
        """Test registration with invalid email."""
        request = self.factory.post('/register/')

        success, user, error = AuthenticationService.register_user(
            email='invalid-email',
            password='testpass123',
            full_name='Test User',
            request=request
        )

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIsNotNone(error)

    def test_authenticate_user_success(self):
        """Test user authentication successfully."""
        request = self.factory.post('/login/')

        success, user, error = AuthenticationService.authenticate_user(
            email='test@example.com',
            password='testpass123',
            request=request
        )

        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertIsNone(error)
        self.assertEqual(user.email, 'test@example.com')

    def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        request = self.factory.post('/login/')

        success, user, error = AuthenticationService.authenticate_user(
            email='test@example.com',
            password='wrongpassword',
            request=request
        )

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIsNotNone(error)
        self.assertIn('Invalid', error)

    def test_authenticate_user_nonexistent_email(self):
        """Test authentication with non-existent email."""
        request = self.factory.post('/login/')

        success, user, error = AuthenticationService.authenticate_user(
            email='nonexistent@example.com',
            password='testpass123',
            request=request
        )

        self.assertFalse(success)
        self.assertIsNone(user)
        self.assertIsNotNone(error)

    def test_login_user_creates_activity_log(self):
        """Test login creates activity log."""
        request = self.factory.post('/login/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        AuthenticationService.login_user(self.user, request)

        # Check activity log created
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='LOGIN'
        ).first()

        self.assertIsNotNone(activity)

    def test_logout_user_creates_activity_log(self):
        """Test logout creates activity log."""
        request = self.factory.post('/logout/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'

        AuthenticationService.logout_user(self.user, request)

        # Check activity log created
        activity = UserActivity.objects.filter(
            user=self.user,
            activity_type='LOGOUT'
        ).first()

        self.assertIsNotNone(activity)

    def test_validate_password_strength_weak(self):
        """Test password strength validation with weak password."""
        is_valid, error = AuthenticationService.validate_password_strength('12345')

        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_password_strength_strong(self):
        """Test password strength validation with strong password."""
        is_valid, error = AuthenticationService.validate_password_strength('StrongPass123!')

        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_change_password_success(self):
        """Test changing password successfully."""
        success, error = AuthenticationService.change_password(
            user=self.user,
            old_password='testpass123',
            new_password='NewPass456!'
        )

        self.assertTrue(success)
        self.assertIsNone(error)

        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPass456!'))

    def test_change_password_wrong_old_password(self):
        """Test changing password with wrong old password."""
        success, error = AuthenticationService.change_password(
            user=self.user,
            old_password='wrongpassword',
            new_password='NewPass456!'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_change_password_weak_new_password(self):
        """Test changing password with weak new password."""
        success, error = AuthenticationService.change_password(
            user=self.user,
            old_password='testpass123',
            new_password='weak'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_verify_email_success(self):
        """Test email verification successfully."""
        self.user.is_verified = False
        self.user.save()

        success, error = AuthenticationService.verify_email(self.user)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_is_user_authenticated(self):
        """Test checking if user is authenticated."""
        self.assertTrue(AuthenticationService.is_user_authenticated(self.user))

    def test_is_user_verified(self):
        """Test checking if user is verified."""
        # Initially not verified
        self.user.is_verified = False
        self.user.save()
        self.assertFalse(AuthenticationService.is_user_verified(self.user))

        # After verification
        self.user.is_verified = True
        self.user.save()
        self.assertTrue(AuthenticationService.is_user_verified(self.user))

    def test_deactivate_user(self):
        """Test deactivating user account."""
        success, error = AuthenticationService.deactivate_user(self.user)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_reactivate_user(self):
        """Test reactivating user account."""
        self.user.is_active = False
        self.user.save()

        success, error = AuthenticationService.reactivate_user(self.user)

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_check_user_status(self):
        """Test checking user account status."""
        status = AuthenticationService.check_user_status(self.user)

        self.assertIn('is_active', status)
        self.assertIn('is_verified', status)
        self.assertIn('is_staff', status)
        self.assertTrue(status['is_active'])

    def test_generate_password_reset_token(self):
        """Test generating password reset token."""
        success, token, error = AuthenticationService.generate_password_reset_token(
            self.user
        )

        self.assertTrue(success)
        self.assertIsNotNone(token)
        self.assertIsNone(error)

    def test_reset_password_with_token(self):
        """Test resetting password with token."""
        # Generate token
        success, token, _ = AuthenticationService.generate_password_reset_token(
            self.user
        )

        # Reset password
        success, error = AuthenticationService.reset_password_with_token(
            token=token,
            new_password='NewResetPass123!'
        )

        self.assertTrue(success)
        self.assertIsNone(error)

        # Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewResetPass123!'))
