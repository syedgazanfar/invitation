"""
Integration tests for user registration and verification flow.

This tests the complete workflow:
1. User signs up with email and password
2. System sends email verification
3. User verifies email
4. User adds phone number
5. System sends OTP
6. User verifies phone with OTP
7. User profile is complete
"""
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from apps.accounts.models import PhoneOTP, UserActivity
from apps.accounts.services import (
    AuthenticationService,
    UserProfileService,
    PhoneVerificationService,
    ActivityService
)
from apps.plans.models import Plan

User = get_user_model()


class UserRegistrationFlowIntegrationTest(TransactionTestCase):
    """Integration tests for complete user registration flow."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

    def test_complete_registration_and_verification_flow(self):
        """Test complete user registration and verification flow."""

        request = self.factory.post('/register/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        # Step 1: User registers
        success, user, error = AuthenticationService.register_user(
            email='newuser@example.com',
            password='SecurePass123!',
            full_name='New User',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.is_verified)  # Email not verified yet
        self.assertFalse(user.is_phone_verified)  # Phone not verified yet

        # Verify registration activity logged
        activity_count = UserActivity.objects.filter(
            user=user,
            activity_type='REGISTRATION'
        ).count()
        self.assertGreater(activity_count, 0)

        # Step 2: User logs in
        success, authenticated_user, error = AuthenticationService.authenticate_user(
            email='newuser@example.com',
            password='SecurePass123!',
            request=request
        )

        self.assertTrue(success)
        self.assertEqual(authenticated_user.id, user.id)

        # Log the login
        AuthenticationService.login_user(user, request)

        # Verify login activity logged
        login_activity = UserActivity.objects.filter(
            user=user,
            activity_type='LOGIN'
        ).first()
        self.assertIsNotNone(login_activity)

        # Step 3: Verify email
        success, error = AuthenticationService.verify_email(user)
        self.assertTrue(success)

        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        # Step 4: Send phone OTP
        with patch('apps.accounts.services.phone_verification_service.send_sms') as mock_sms:
            mock_sms.return_value = True

            success, otp_id, error = PhoneVerificationService.send_otp(
                phone=user.phone,
                user=user
            )

            self.assertTrue(success)
            self.assertIsNotNone(otp_id)

        # Verify OTP record created
        otp_record = PhoneOTP.objects.filter(user=user).first()
        self.assertIsNotNone(otp_record)
        self.assertEqual(len(otp_record.otp), 6)

        # Step 5: Verify phone with OTP
        success, error = PhoneVerificationService.verify_otp(
            user=user,
            otp=otp_record.otp
        )

        self.assertTrue(success)
        user.refresh_from_db()
        self.assertTrue(user.is_phone_verified)

        # Step 6: Check profile completion
        is_complete, missing_fields = UserProfileService.is_profile_complete(user)
        self.assertTrue(is_complete)
        self.assertEqual(len(missing_fields), 0)

        # Step 7: Get profile completion percentage
        completion = UserProfileService.get_profile_completion_percentage(user)
        self.assertEqual(completion, 100)

    def test_registration_with_duplicate_email(self):
        """Test registration fails with duplicate email."""

        request = self.factory.post('/register/')

        # First registration
        success, user1, error = AuthenticationService.register_user(
            email='duplicate@example.com',
            password='Pass123!',
            full_name='User One',
            request=request
        )

        self.assertTrue(success)

        # Try to register with same email
        success, user2, error = AuthenticationService.register_user(
            email='duplicate@example.com',
            password='Pass456!',
            full_name='User Two',
            request=request
        )

        self.assertFalse(success)
        self.assertIsNone(user2)
        self.assertIsNotNone(error)

    def test_password_change_flow(self):
        """Test complete password change flow."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='passchange@example.com',
            password='OldPass123!',
            full_name='Test User',
            request=request
        )

        self.assertTrue(success)

        # Change password
        success, error = AuthenticationService.change_password(
            user=user,
            old_password='OldPass123!',
            new_password='NewPass456!'
        )

        self.assertTrue(success)

        # Verify old password doesn't work
        success, auth_user, error = AuthenticationService.authenticate_user(
            email='passchange@example.com',
            password='OldPass123!',
            request=request
        )

        self.assertFalse(success)

        # Verify new password works
        success, auth_user, error = AuthenticationService.authenticate_user(
            email='passchange@example.com',
            password='NewPass456!',
            request=request
        )

        self.assertTrue(success)

    def test_password_reset_flow(self):
        """Test password reset flow with token."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='resetpass@example.com',
            password='OldPass123!',
            full_name='Test User',
            request=request
        )

        self.assertTrue(success)

        # Generate reset token
        success, token, error = AuthenticationService.generate_password_reset_token(
            user
        )

        self.assertTrue(success)
        self.assertIsNotNone(token)

        # Reset password with token
        success, error = AuthenticationService.reset_password_with_token(
            token=token,
            new_password='ResetPass789!'
        )

        self.assertTrue(success)

        # Verify new password works
        success, auth_user, error = AuthenticationService.authenticate_user(
            email='resetpass@example.com',
            password='ResetPass789!',
            request=request
        )

        self.assertTrue(success)

    def test_profile_update_flow(self):
        """Test user profile update flow."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='updateprofile@example.com',
            password='Pass123!',
            full_name='Original Name',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)

        # Update profile
        success, error = UserProfileService.update_profile(
            user=user,
            full_name='Updated Name',
            phone='+911234567890'
        )

        self.assertTrue(success)

        user.refresh_from_db()
        self.assertEqual(user.full_name, 'Updated Name')
        self.assertEqual(user.phone, '+911234567890')

        # Phone verification should be reset
        self.assertFalse(user.is_phone_verified)

    def test_email_change_flow(self):
        """Test email change flow."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='oldemail@example.com',
            password='Pass123!',
            full_name='Test User',
            request=request
        )

        self.assertTrue(success)

        # Verify email
        AuthenticationService.verify_email(user)
        user.refresh_from_db()
        self.assertTrue(user.is_verified)

        # Change email
        success, error = UserProfileService.update_email(
            user=user,
            new_email='newemail@example.com'
        )

        self.assertTrue(success)

        user.refresh_from_db()
        self.assertEqual(user.email, 'newemail@example.com')
        # Email verification should be reset
        self.assertFalse(user.is_verified)

    def test_otp_resend_flow(self):
        """Test OTP resend flow."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='otpresend@example.com',
            password='Pass123!',
            full_name='Test User',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)

        with patch('apps.accounts.services.phone_verification_service.send_sms') as mock_sms:
            mock_sms.return_value = True

            # Send initial OTP
            success, otp_id1, error = PhoneVerificationService.send_otp(
                phone=user.phone,
                user=user
            )

            self.assertTrue(success)

            # Resend OTP
            success, otp_id2, error = PhoneVerificationService.resend_otp(user)

            self.assertTrue(success)
            self.assertIsNotNone(otp_id2)

        # Should have 2 OTP records
        otp_count = PhoneOTP.objects.filter(user=user).count()
        self.assertGreaterEqual(otp_count, 2)

    def test_otp_rate_limiting(self):
        """Test OTP rate limiting."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='ratelimit@example.com',
            password='Pass123!',
            full_name='Test User',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)

        # Create multiple OTP attempts
        for i in range(5):
            PhoneOTP.objects.create(
                user=user,
                phone=user.phone,
                otp=f'12345{i}'
            )

        # Check rate limit
        is_limited = PhoneVerificationService.is_rate_limited(
            user=user,
            max_attempts=3,
            timeframe_minutes=60
        )

        self.assertTrue(is_limited)

    def test_account_deactivation_flow(self):
        """Test account deactivation and reactivation."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='deactivate@example.com',
            password='Pass123!',
            full_name='Test User',
            request=request
        )

        self.assertTrue(success)
        self.assertTrue(user.is_active)

        # Deactivate account
        success, error = AuthenticationService.deactivate_user(user)
        self.assertTrue(success)

        user.refresh_from_db()
        self.assertFalse(user.is_active)

        # Reactivate account
        success, error = AuthenticationService.reactivate_user(user)
        self.assertTrue(success)

        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_account_deletion_flow(self):
        """Test account deletion flow."""

        request = self.factory.post('/register/')

        # Register user
        success, user, error = AuthenticationService.register_user(
            email='delete@example.com',
            password='Pass123!',
            full_name='Test User',
            request=request
        )

        self.assertTrue(success)
        user_id = user.id

        # Delete account
        success, error = UserProfileService.delete_account(
            user,
            password='Pass123!'
        )

        self.assertTrue(success)

        # Verify user deleted
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_activity_logging_throughout_flow(self):
        """Test activity is logged throughout user journey."""

        request = self.factory.post('/test/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        # Register
        success, user, error = AuthenticationService.register_user(
            email='activity@example.com',
            password='Pass123!',
            full_name='Test User',
            request=request
        )

        # Login
        AuthenticationService.login_user(user, request)

        # Profile update
        ActivityService.log_activity(
            user=user,
            activity_type='PROFILE_UPDATE',
            description='Updated phone number',
            request=request
        )

        # Password change
        ActivityService.log_activity(
            user=user,
            activity_type='PASSWORD_CHANGE',
            request=request
        )

        # Logout
        AuthenticationService.logout_user(user, request)

        # Check activities logged
        activity_count = ActivityService.get_activity_count(user)
        self.assertGreaterEqual(activity_count, 4)

        # Get activity summary
        summary = ActivityService.get_activity_summary(user)
        self.assertIn('total_activities', summary)
        self.assertGreater(summary['total_activities'], 0)

    def test_user_data_export_flow(self):
        """Test exporting user data."""

        request = self.factory.post('/register/')

        # Register user with complete profile
        success, user, error = AuthenticationService.register_user(
            email='export@example.com',
            password='Pass123!',
            full_name='Export User',
            phone='+919876543210',
            request=request
        )

        self.assertTrue(success)

        # Export user data
        data = UserProfileService.export_user_data(user)

        self.assertIn('profile', data)
        self.assertIn('account_info', data)
        self.assertEqual(data['profile']['email'], 'export@example.com')
