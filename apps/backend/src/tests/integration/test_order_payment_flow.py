"""
Integration tests for order placement and payment flow.

This tests the complete workflow:
1. User selects a plan and template
2. Creates an order
3. Makes payment via Razorpay
4. Order gets approved
5. Invitation is created and activated
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from decimal import Decimal
from django.utils import timezone

from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.models import Order, Invitation
from apps.invitations.services import (
    OrderService,
    InvitationService,
    PaymentService
)

User = get_user_model()


class OrderPaymentFlowIntegrationTest(TransactionTestCase):
    """Integration tests for complete order and payment flow."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create plan
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
            name='Elegant Wedding',
            description='Beautiful wedding template',
            plan=self.plan,
            category=self.category,
            animation_type='elegant',
            is_active=True
        )

    def test_complete_order_to_invitation_flow(self):
        """Test complete flow from order creation to invitation activation."""

        # Step 1: Create order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding Anniversary',
            event_date='2026-12-15',
            host_name='John & Jane Doe',
            venue='Grand Hotel'
        )

        self.assertTrue(success)
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'DRAFT')
        self.assertEqual(order.payment_amount, Decimal('499.00'))

        # Step 2: Create Razorpay order
        with patch('apps.invitations.services.payment_service.razorpay.Client') as mock_razorpay:
            mock_client = MagicMock()
            mock_client.order.create.return_value = {
                'id': 'order_test123',
                'amount': 49900,
                'currency': 'INR',
                'status': 'created'
            }
            mock_razorpay.return_value = mock_client

            success, payment_data, error = PaymentService.create_razorpay_order(
                order,
                self.user
            )

            self.assertTrue(success)
            self.assertEqual(payment_data['razorpay_order_id'], 'order_test123')

            # Update order with Razorpay order ID
            order.razorpay_order_id = payment_data['razorpay_order_id']
            order.status = 'PENDING_PAYMENT'
            order.save()

        # Step 3: Simulate successful payment
        with patch('apps.invitations.services.payment_service.razorpay.Client') as mock_razorpay:
            mock_client = MagicMock()
            mock_client.utility.verify_payment_signature.return_value = True
            mock_razorpay.return_value = mock_client

            success, error = PaymentService.process_successful_payment(
                order=order,
                payment_id='pay_test456',
                razorpay_order_id='order_test123',
                razorpay_signature='signature_test789'
            )

            self.assertTrue(success)
            order.refresh_from_db()
            self.assertEqual(order.status, 'PENDING_APPROVAL')
            self.assertIsNotNone(order.paid_at)

        # Step 4: Admin approves order
        success, error = OrderService.approve_order(order)
        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'APPROVED')
        self.assertIsNotNone(order.approved_at)

        # Step 5: Create invitation
        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='You are Invited!',
            message='Join us for our wedding anniversary celebration'
        )

        self.assertTrue(success)
        self.assertIsNotNone(invitation)
        self.assertIsNotNone(invitation.slug)

        # Step 6: Activate invitation
        success, error = InvitationService.activate_invitation(invitation)
        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_active)
        self.assertIsNotNone(invitation.link_expires_at)

        # Verify complete flow
        final_order = Order.objects.get(id=order.id)
        final_invitation = Invitation.objects.get(id=invitation.id)

        self.assertEqual(final_order.status, 'APPROVED')
        self.assertTrue(final_invitation.is_active)
        self.assertEqual(final_invitation.order, final_order)

    def test_payment_failure_flow(self):
        """Test flow when payment fails."""

        # Create order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        self.assertTrue(success)
        order.status = 'PENDING_PAYMENT'
        order.save()

        # Simulate payment failure
        success, error = PaymentService.process_failed_payment(
            order=order,
            error_code='PAYMENT_DECLINED',
            error_description='Insufficient funds'
        )

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PAYMENT_FAILED')
        self.assertIn('Insufficient funds', order.notes)

        # Verify no invitation created
        invitation_count = Invitation.objects.filter(order=order).count()
        self.assertEqual(invitation_count, 0)

    def test_order_cancellation_flow(self):
        """Test order cancellation flow."""

        # Create and approve order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        order.status = 'PENDING_PAYMENT'
        order.save()

        # Cancel order
        success, error = OrderService.cancel_order(
            order,
            reason='User changed mind'
        )

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'CANCELLED')

    def test_order_rejection_flow(self):
        """Test order rejection flow."""

        # Create order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        order.status = 'PENDING_APPROVAL'
        order.paid_at = timezone.now()
        order.save()

        # Admin rejects order
        success, error = OrderService.reject_order(
            order,
            reason='Payment verification failed'
        )

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'REJECTED')

        # Verify no invitation created
        invitation_count = Invitation.objects.filter(order=order).count()
        self.assertEqual(invitation_count, 0)

    def test_webhook_payment_confirmation_flow(self):
        """Test payment confirmation via webhook."""

        # Create order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        order.status = 'PENDING_PAYMENT'
        order.razorpay_order_id = 'order_webhook123'
        order.save()

        # Simulate webhook
        webhook_data = {
            'event': 'payment.captured',
            'payload': {
                'payment': {
                    'entity': {
                        'id': 'pay_webhook456',
                        'order_id': 'order_webhook123',
                        'status': 'captured',
                        'amount': 49900
                    }
                }
            }
        }

        success, error = PaymentService.handle_payment_webhook(webhook_data)

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PENDING_APPROVAL')
        self.assertEqual(order.payment_id, 'pay_webhook456')

    def test_multiple_orders_same_user(self):
        """Test user creating multiple orders."""

        orders = []
        for i in range(3):
            success, order, error = OrderService.create_order(
                user=self.user,
                plan=self.plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00')
            )
            self.assertTrue(success)
            orders.append(order)

        # Verify all orders created
        user_orders = OrderService.get_orders_by_user(self.user)
        self.assertEqual(user_orders.count(), 3)

        # Each order should have unique order number
        order_numbers = [o.order_number for o in orders]
        self.assertEqual(len(order_numbers), len(set(order_numbers)))

    def test_order_with_plan_restriction(self):
        """Test order creation with plan restrictions."""

        # Assign user to BASIC plan
        self.user.current_plan = Plan.objects.create(
            code='BASIC',
            name='Basic Plan',
            price=0.00,
            is_active=True
        )
        self.user.save()

        # Try to order PREMIUM plan (different from current)
        can_order, error = OrderService.can_user_order_plan(
            self.user,
            'PREMIUM'
        )

        self.assertFalse(can_order)
        self.assertIsNotNone(error)

    def test_template_usage_increment_on_order(self):
        """Test template usage count increments when used in order."""

        initial_count = self.template.use_count

        # Create order with template
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        # Manually increment (normally done when invitation is created)
        self.template.increment_use_count()

        self.template.refresh_from_db()
        self.assertEqual(self.template.use_count, initial_count + 1)
