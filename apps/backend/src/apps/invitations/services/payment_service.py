"""
Payment processing service with Razorpay integration.

This service handles payment creation, verification, and webhook processing.
"""
import json
import logging
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
from django.utils import timezone

from ..models import Order, OrderStatus

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for Razorpay payment processing."""

    @staticmethod
    def get_razorpay_client():
        """
        Get initialized Razorpay client.

        Returns:
            Razorpay Client instance

        Raises:
            ImportError: If razorpay SDK not installed
            ValueError: If credentials not configured
        """
        try:
            import razorpay
        except ImportError:
            raise ImportError("Razorpay SDK not installed. Install with: pip install razorpay")

        key_id = getattr(settings, 'RAZORPAY_KEY_ID', None)
        key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', None)

        if not key_id or not key_secret:
            raise ValueError("Razorpay credentials not configured in settings")

        return razorpay.Client(auth=(key_id, key_secret))

    @staticmethod
    def create_razorpay_order(order: Order, user) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Create a Razorpay order for payment.

        Args:
            order: Order to create payment for
            user: User making the payment

        Returns:
            Tuple of (success, payment_data, error_message)
            payment_data contains: order_id, amount, currency, key_id, prefill
        """
        try:
            # Validate order status
            if order.status not in [OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT]:
                return False, None, "Order cannot be paid for at this stage"

            # Get Razorpay client
            client = PaymentService.get_razorpay_client()

            # Create Razorpay order
            razorpay_order = client.order.create({
                'amount': int(order.payment_amount * 100),  # Convert to paise
                'currency': 'INR',
                'receipt': order.order_number,
                'notes': {
                    'order_id': str(order.id),
                    'user_id': str(user.id),
                    'plan': order.plan.name,
                }
            })

            # Prepare response data
            payment_data = {
                'order_id': razorpay_order['id'],
                'amount': float(order.payment_amount),
                'currency': 'INR',
                'key_id': settings.RAZORPAY_KEY_ID,
                'prefill': PaymentService.prepare_payment_prefill(user)
            }

            logger.info(f"Razorpay order created for {order.order_number}: {razorpay_order['id']}")
            return True, payment_data, None

        except Exception as e:
            logger.error(f"Error creating Razorpay order: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def prepare_payment_prefill(user) -> Dict[str, str]:
        """
        Prepare user data for payment checkout prefill.

        Args:
            user: User making payment

        Returns:
            Dictionary with name, email, contact
        """
        return {
            'name': user.full_name or user.username,
            'email': user.email or '',
            'contact': user.phone
        }

    @staticmethod
    def verify_payment_signature(
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify payment signature from frontend.

        Args:
            razorpay_order_id: Razorpay order ID
            razorpay_payment_id: Razorpay payment ID
            razorpay_signature: Payment signature

        Returns:
            Tuple of (success, error_message)
        """
        try:
            client = PaymentService.get_razorpay_client()

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }

            client.utility.verify_payment_signature(params_dict)

            logger.info(f"Payment signature verified: {razorpay_payment_id}")
            return True, None

        except Exception as e:
            logger.error(f"Payment signature verification failed: {e}", exc_info=True)
            return False, "Invalid payment signature"

    @staticmethod
    def process_payment_success(
        order: Order,
        payment_id: str,
        payment_method: str = 'RAZORPAY'
    ) -> Tuple[bool, Optional[str]]:
        """
        Process successful payment.

        Updates order status to PENDING_APPROVAL.

        Args:
            order: Order that was paid for
            payment_id: Payment ID from gateway
            payment_method: Payment method used

        Returns:
            Tuple of (success, error_message)
        """
        try:
            order.payment_status = 'RECEIVED'
            order.payment_method = payment_method
            order.payment_notes = f"Payment ID: {payment_id}"
            order.payment_received_at = timezone.now()
            order.status = OrderStatus.PENDING_APPROVAL
            order.save()

            # TODO: Send notification to admin
            logger.info(f"Payment processed for order {order.order_number}: {payment_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error processing payment success: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def verify_webhook_signature(body: str, signature: str) -> Tuple[bool, Optional[str]]:
        """
        Verify Razorpay webhook signature.

        Args:
            body: Webhook request body
            signature: X-Razorpay-Signature header

        Returns:
            Tuple of (valid, error_message)
        """
        try:
            client = PaymentService.get_razorpay_client()
            webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', '')

            if not webhook_secret:
                logger.error("Razorpay webhook secret not configured")
                return False, "Webhook not configured"

            client.utility.verify_webhook_signature(body, signature, webhook_secret)

            return True, None

        except Exception as e:
            logger.error(f"Webhook signature verification failed: {e}", exc_info=True)
            return False, "Invalid webhook signature"

    @staticmethod
    def process_webhook_payment(webhook_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Process payment webhook from Razorpay.

        Args:
            webhook_data: Parsed webhook payload

        Returns:
            Tuple of (success, error_message)
        """
        try:
            event = webhook_data.get('event')

            if event == 'payment.captured':
                payment = webhook_data.get('payload', {}).get('payment', {}).get('entity', {})
                order_notes = payment.get('notes', {})
                order_id = order_notes.get('order_id')

                if not order_id:
                    logger.warning("No order_id in webhook payment notes")
                    return True, None  # Still return success to acknowledge webhook

                try:
                    order = Order.objects.get(id=order_id)
                    PaymentService.process_payment_success(
                        order=order,
                        payment_id=payment.get('id'),
                        payment_method='RAZORPAY'
                    )

                    logger.info(f"Webhook payment processed for order {order.order_number}")
                except Order.DoesNotExist:
                    logger.error(f"Order not found for webhook: {order_id}")

            return True, None

        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_payment_status(order: Order) -> Dict[str, Any]:
        """
        Get payment status for an order.

        Args:
            order: Order to check payment status for

        Returns:
            Dictionary with payment status information
        """
        return {
            'payment_required': order.status in [OrderStatus.DRAFT, OrderStatus.PENDING_PAYMENT],
            'payment_status': order.payment_status,
            'payment_method': order.payment_method,
            'payment_amount': float(order.payment_amount),
            'payment_received_at': order.payment_received_at.isoformat() if order.payment_received_at else None,
            'order_status': order.status
        }
