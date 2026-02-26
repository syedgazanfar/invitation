"""
Unit tests for PhoneVerificationService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from apps.accounts.services import PhoneVerificationService
from apps.accounts.models import PhoneOTP

User = get_user_model()


class PhoneVerificationServiceTest(TestCase):
    """Test cases for PhoneVerificationService."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone='+911234567890',
            is_phone_verified=False
        )

    def test_generate_otp(self):
        """Test generating OTP."""
        otp = PhoneVerificationService.generate_otp()

        self.assertIsNotNone(otp)
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_generate_otp_custom_length(self):
        """Test generating OTP with custom length."""
        otp = PhoneVerificationService.generate_otp(length=4)

        self.assertEqual(len(otp), 4)
        self.assertTrue(otp.isdigit())

    @patch('apps.accounts.services.phone_verification_service.send_sms')
    def test_send_otp_success(self, mock_send_sms):
        """Test sending OTP successfully."""
        mock_send_sms.return_value = True

        success, otp_id, error = PhoneVerificationService.send_otp(
            phone=self.user.phone,
            user=self.user
        )

        self.assertTrue(success)
        self.assertIsNotNone(otp_id)
        self.assertIsNone(error)

        # Check OTP record created
        otp_record = PhoneOTP.objects.filter(user=self.user).first()
        self.assertIsNotNone(otp_record)
        self.assertFalse(otp_record.is_verified)

    def test_verify_otp_success(self):
        """Test verifying OTP successfully."""
        # Create OTP record
        otp_code = '123456'
        otp_record = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp=otp_code,
            is_verified=False
        )

        success, error = PhoneVerificationService.verify_otp(
            user=self.user,
            otp=otp_code
        )

        self.assertTrue(success)
        self.assertIsNone(error)

        # Check OTP marked as verified
        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_verified)

        # Check user phone marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_phone_verified)

    def test_verify_otp_wrong_code(self):
        """Test verifying OTP with wrong code."""
        # Create OTP record
        otp_record = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=False
        )

        success, error = PhoneVerificationService.verify_otp(
            user=self.user,
            otp='654321'  # Wrong OTP
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn('Invalid', error)

    def test_verify_otp_expired(self):
        """Test verifying expired OTP."""
        from django.utils import timezone
        from datetime import timedelta

        # Create expired OTP record
        otp_record = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=False,
            created_at=timezone.now() - timedelta(minutes=15)  # Expired
        )

        success, error = PhoneVerificationService.verify_otp(
            user=self.user,
            otp='123456'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn('expired', error.lower())

    def test_verify_otp_already_verified(self):
        """Test verifying already verified OTP."""
        # Create already verified OTP record
        otp_record = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=True
        )

        success, error = PhoneVerificationService.verify_otp(
            user=self.user,
            otp='123456'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_is_otp_valid_time(self):
        """Test checking OTP validity time."""
        from django.utils import timezone
        from datetime import timedelta

        # Recent OTP
        recent_otp = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=False
        )

        is_valid = PhoneVerificationService.is_otp_valid(recent_otp)
        self.assertTrue(is_valid)

        # Expired OTP
        expired_otp = PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='654321',
            is_verified=False,
            created_at=timezone.now() - timedelta(minutes=15)
        )

        is_valid = PhoneVerificationService.is_otp_valid(expired_otp)
        self.assertFalse(is_valid)

    def test_resend_otp(self):
        """Test resending OTP."""
        # Create initial OTP
        PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=False
        )

        with patch('apps.accounts.services.phone_verification_service.send_sms') as mock_send_sms:
            mock_send_sms.return_value = True

            success, otp_id, error = PhoneVerificationService.resend_otp(
                user=self.user
            )

            self.assertTrue(success)
            self.assertIsNotNone(otp_id)

            # Check new OTP created
            otp_count = PhoneOTP.objects.filter(user=self.user).count()
            self.assertGreater(otp_count, 1)

    def test_get_otp_attempts(self):
        """Test getting OTP attempt count."""
        from django.utils import timezone
        from datetime import timedelta

        # Create multiple OTP attempts
        for i in range(3):
            PhoneOTP.objects.create(
                user=self.user,
                phone=self.user.phone,
                otp=f'12345{i}',
                is_verified=False
            )

        attempts = PhoneVerificationService.get_otp_attempts(
            user=self.user,
            timeframe_minutes=60
        )

        self.assertEqual(attempts, 3)

    def test_is_rate_limited(self):
        """Test OTP rate limiting."""
        # Create multiple OTP attempts
        for i in range(5):
            PhoneOTP.objects.create(
                user=self.user,
                phone=self.user.phone,
                otp=f'12345{i}',
                is_verified=False
            )

        is_limited = PhoneVerificationService.is_rate_limited(
            user=self.user,
            max_attempts=3,
            timeframe_minutes=60
        )

        self.assertTrue(is_limited)

    def test_clear_old_otps(self):
        """Test clearing old OTP records."""
        from django.utils import timezone
        from datetime import timedelta

        # Create old OTP
        PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='123456',
            is_verified=False,
            created_at=timezone.now() - timedelta(days=8)
        )

        # Create recent OTP
        PhoneOTP.objects.create(
            user=self.user,
            phone=self.user.phone,
            otp='654321',
            is_verified=False
        )

        deleted_count = PhoneVerificationService.clear_old_otps(days=7)

        self.assertGreater(deleted_count, 0)
        # Recent OTP should still exist
        self.assertTrue(
            PhoneOTP.objects.filter(user=self.user, otp='654321').exists()
        )
