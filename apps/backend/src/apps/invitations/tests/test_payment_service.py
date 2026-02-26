"""
Unit tests for PaymentService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
from apps.invitations.models import Order
from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.services import PaymentService

User = get_user_model()


class PaymentServiceTest(TestCase):
    """Test cases for PaymentService."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create test plan
        self.plan = Plan.objects.create(
            code='PREMIUM',
            name='Premium Plan',
            price=499.00,
            is_active=True
        )

        # Create category and template
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            is_active=True
        )
        self.template = Template.objects.create(
            name='Test Template',
            description='Test',
            plan=self.plan,
            category=self.category,
            animation_type='elegant',
            is_active=True
        )

        # Create test order
        self.order = Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )

    @patch('apps.invitations.services.payment_service.razorpay.Client')
    def test_create_razorpay_order_success(self, mock_razorpay):
        """Test creating Razorpay order successfully."""
        # Mock Razorpay client
        mock_client = MagicMock()
        mock_client.order.create.return_value = {
            'id': 'order_test123',
            'amount': 49900,
            'currency': 'INR',
            'status': 'created'
        }
        mock_razorpay.return_value = mock_client

        success, payment_data, error = PaymentService.create_razorpay_order(
            self.order,
            self.user
        )

        self.assertTrue(success)
        self.assertIsNotNone(payment_data)
        self.assertIsNone(error)
        self.assertIn('razorpay_order_id', payment_data)
        self.assertEqual(payment_data['amount'], 49900)

    @patch('apps.invitations.services.payment_service.razorpay.Client')
    def test_verify_payment_signature_success(self, mock_razorpay):
        """Test verifying payment signature successfully."""
        # Mock Razorpay client
        mock_client = MagicMock()
        mock_client.utility.verify_payment_signature.return_value = True
        mock_razorpay.return_value = mock_client

        payment_data = {
            'razorpay_order_id': 'order_test123',
            'razorpay_payment_id': 'pay_test456',
            'razorpay_signature': 'signature_test789'
        }

        is_valid = PaymentService.verify_payment_signature(payment_data)
        self.assertTrue(is_valid)

    @patch('apps.invitations.services.payment_service.razorpay.Client')
    def test_verify_payment_signature_failure(self, mock_razorpay):
        """Test verifying payment signature with invalid signature."""
        # Mock Razorpay client to raise exception
        mock_client = MagicMock()
        mock_client.utility.verify_payment_signature.side_effect = Exception('Invalid signature')
        mock_razorpay.return_value = mock_client

        payment_data = {
            'razorpay_order_id': 'order_test123',
            'razorpay_payment_id': 'pay_test456',
            'razorpay_signature': 'invalid_signature'
        }

        is_valid = PaymentService.verify_payment_signature(payment_data)
        self.assertFalse(is_valid)

    def test_process_successful_payment(self):
        """Test processing successful payment."""
        self.order.status = 'PENDING_PAYMENT'
        self.order.save()

        success, error = PaymentService.process_successful_payment(
            order=self.order,
            payment_id='pay_test123',
            razorpay_order_id='order_test456',
            razorpay_signature='signature_test789'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PENDING_APPROVAL')
        self.assertEqual(self.order.payment_id, 'pay_test123')
        self.assertIsNotNone(self.order.paid_at)

    def test_process_failed_payment(self):
        """Test processing failed payment."""
        self.order.status = 'PENDING_PAYMENT'
        self.order.save()

        success, error = PaymentService.process_failed_payment(
            order=self.order,
            error_code='BAD_REQUEST_ERROR',
            error_description='Payment declined by bank'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PAYMENT_FAILED')
        self.assertIn('Payment declined', self.order.notes)

    def test_handle_payment_webhook_success(self):
        """Test handling successful payment webhook."""
        self.order.status = 'PENDING_PAYMENT'
        self.order.razorpay_order_id = 'order_test123'
        self.order.save()

        webhook_data = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test456',
                        'order_id': 'order_test123',
                        'status': 'captured',
                        'amount': 49900
                    }
                }
            }
        }

        success, error = PaymentService.handle_payment_webhook(webhook_data)

        self.assertTrue(success)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PENDING_APPROVAL')

    def test_handle_payment_webhook_failure(self):
        """Test handling failed payment webhook."""
        self.order.status = 'PENDING_PAYMENT'
        self.order.razorpay_order_id = 'order_test123'
        self.order.save()

        webhook_data = {
            'event': 'payment.failed',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_test456',
                        'order_id': 'order_test123',
                        'status': 'failed',
                        'error_code': 'BAD_REQUEST_ERROR',
                        'error_description': 'Payment failed'
                    }
                }
            }
        }

        success, error = PaymentService.handle_payment_webhook(webhook_data)

        self.assertTrue(success)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'PAYMENT_FAILED')

    def test_get_payment_status(self):
        """Test getting payment status."""
        self.order.status = 'PENDING_APPROVAL'
        self.order.payment_id = 'pay_test123'
        self.order.save()

        status = PaymentService.get_payment_status(self.order)

        self.assertEqual(status['status'], 'PENDING_APPROVAL')
        self.assertEqual(status['payment_id'], 'pay_test123')
        self.assertIn('payment_amount', status)

    def test_refund_payment_success(self):
        """Test refunding payment successfully."""
        self.order.status = 'APPROVED'
        self.order.payment_id = 'pay_test123'
        self.order.save()

        with patch('apps.invitations.services.payment_service.razorpay.Client') as mock_razorpay:
            mock_client = MagicMock()
            mock_client.payment.refund.return_value = {
                'id': 'rfnd_test123',
                'amount': 49900,
                'status': 'processed'
            }
            mock_razorpay.return_value = mock_client

            success, refund_id, error = PaymentService.refund_payment(
                self.order,
                amount=Decimal('499.00'),
                reason='Customer request'
            )

            self.assertTrue(success)
            self.assertEqual(refund_id, 'rfnd_test123')
            self.assertIsNone(error)

    def test_calculate_payment_amount(self):
        """Test calculating payment amount."""
        amount = PaymentService.calculate_payment_amount(
            plan_price=Decimal('499.00'),
            discount=Decimal('50.00')
        )
        self.assertEqual(amount, Decimal('449.00'))

    def test_calculate_payment_amount_with_percentage_discount(self):
        """Test calculating payment amount with percentage discount."""
        amount = PaymentService.calculate_payment_amount(
            plan_price=Decimal('500.00'),
            discount_percentage=10
        )
        self.assertEqual(amount, Decimal('450.00'))

    def test_validate_payment_amount(self):
        """Test validating payment amount."""
        is_valid, error = PaymentService.validate_payment_amount(
            order_amount=Decimal('499.00'),
            received_amount=49900  # in paise
        )
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_payment_amount_mismatch(self):
        """Test validating payment amount with mismatch."""
        is_valid, error = PaymentService.validate_payment_amount(
            order_amount=Decimal('499.00'),
            received_amount=39900  # in paise, different amount
        )
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
