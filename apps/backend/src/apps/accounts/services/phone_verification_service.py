"""
Phone verification service for OTP generation and verification.

This service handles OTP-based phone number verification workflow.
"""
import random
import logging
from datetime import timedelta
from typing import Tuple, Optional, Dict, Any
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from ..models import PhoneVerification
from .utils import normalize_phone, get_client_ip

# Import SMS service
try:
    from utils.sms_service import SMSService
except ImportError:
    SMSService = None

logger = logging.getLogger(__name__)
User = get_user_model()


class PhoneVerificationService:
    """Service for phone number verification via OTP."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10

    @staticmethod
    def generate_otp() -> str:
        """
        Generate a random 6-digit OTP.

        Returns:
            6-digit OTP as string
        """
        return ''.join([str(random.randint(0, 9)) for _ in range(PhoneVerificationService.OTP_LENGTH)])

    @staticmethod
    def create_otp_record(user: User, otp: str, phone: str, request = None) -> PhoneVerification:
        """
        Create an OTP verification record.

        Args:
            user: User for whom OTP is being generated
            otp: Generated OTP
            phone: Phone number (already normalized)
            request: Django request object (for IP)

        Returns:
            PhoneVerification object
        """
        expires_at = timezone.now() + timedelta(minutes=PhoneVerificationService.OTP_EXPIRY_MINUTES)

        verification = PhoneVerification.objects.create(
            user=user,
            otp=otp,
            expires_at=expires_at,
            ip_address=get_client_ip(request) or '0.0.0.0'
        )

        return verification

    @staticmethod
    def send_otp(user: User, phone: str, request = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate and send OTP to phone number.

        Args:
            user: User requesting OTP
            phone: Phone number (will be normalized)
            request: Django request object

        Returns:
            Tuple of (success, otp, error_message)
            - success: Boolean indicating if OTP was sent
            - otp: The OTP (only in dev mode without SMS service)
            - error_message: Error message if failed
        """
        try:
            # Normalize phone
            normalized_phone = normalize_phone(phone)

            # Generate OTP
            otp = PhoneVerificationService.generate_otp()

            # Create OTP record
            with transaction.atomic():
                verification = PhoneVerificationService.create_otp_record(
                    user=user,
                    otp=otp,
                    phone=normalized_phone,
                    request=request
                )

                # Send SMS
                if SMSService:
                    sms_sent = SMSService.send_otp_sms(normalized_phone, otp)
                    if not sms_sent:
                        logger.error(f"Failed to send OTP SMS to {normalized_phone}")
                        return False, None, "Failed to send OTP. Please try again."
                else:
                    # Development mode - no SMS service
                    logger.info(f"Development mode: OTP for {normalized_phone} is {otp}")

            # Return OTP only in development mode (when SMSService is not configured)
            return_otp = otp if not SMSService or not hasattr(SMSService, 'MSG91_AUTH_KEY') else None

            return True, return_otp, None

        except Exception as e:
            logger.error(f"Error in send_otp: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def verify_otp(phone: str, otp: str) -> Tuple[bool, Optional[User], Optional[str]]:
        """
        Verify OTP for a phone number.

        Args:
            phone: Phone number (will be normalized)
            otp: OTP to verify

        Returns:
            Tuple of (success, user, error_message)
            - success: Boolean indicating if OTP is valid
            - user: User object if verification successful
            - error_message: Error message if failed
        """
        try:
            # Normalize phone
            normalized_phone = normalize_phone(phone)

            # Get user
            try:
                user = User.objects.get(phone=normalized_phone)
            except User.DoesNotExist:
                return False, None, "User not found"

            # Get latest unused OTP
            try:
                verification = PhoneVerification.objects.filter(
                    user=user,
                    otp=otp,
                    is_used=False,
                    expires_at__gt=timezone.now()
                ).latest('created_at')
            except PhoneVerification.DoesNotExist:
                return False, None, "Invalid or expired OTP"

            # Mark OTP as used and verify phone
            with transaction.atomic():
                verification.is_used = True
                verification.save(update_fields=['is_used'])

                PhoneVerificationService.mark_phone_verified(user)

            return True, user, None

        except Exception as e:
            logger.error(f"Error in verify_otp: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def mark_phone_verified(user: User) -> None:
        """
        Mark user's phone as verified.

        Args:
            user: User whose phone should be marked verified
        """
        if not user.is_phone_verified:
            user.is_phone_verified = True
            user.phone_verified_at = timezone.now()
            user.save(update_fields=['is_phone_verified', 'phone_verified_at'])

    @staticmethod
    def get_otp_status(user: User) -> Dict[str, Any]:
        """
        Get OTP status for a user.

        Args:
            user: User to check OTP status for

        Returns:
            Dictionary with OTP status information
        """
        # Get latest OTP
        latest_otp = PhoneVerification.objects.filter(
            user=user
        ).order_by('-created_at').first()

        if not latest_otp:
            return {
                'has_pending_otp': False,
                'is_phone_verified': user.is_phone_verified
            }

        is_expired = latest_otp.expires_at <= timezone.now()
        is_active = not latest_otp.is_used and not is_expired

        return {
            'has_pending_otp': is_active,
            'otp_expires_at': latest_otp.expires_at.isoformat() if is_active else None,
            'is_phone_verified': user.is_phone_verified,
            'phone_verified_at': user.phone_verified_at.isoformat() if user.phone_verified_at else None
        }
