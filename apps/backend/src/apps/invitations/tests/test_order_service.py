"""
Unit tests for OrderService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.invitations.models import Order
from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.services import OrderService

User = get_user_model()


class OrderServiceTest(TestCase):
    """Test cases for OrderService."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

        # Create test plans
        self.basic_plan = Plan.objects.create(
            code='BASIC',
            name='Basic Plan',
            price=0.00,
            is_active=True
        )
        self.premium_plan = Plan.objects.create(
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
            plan=self.basic_plan,
            category=self.category,
            animation_type='elegant',
            is_active=True
        )

    def test_create_order_success(self):
        """Test creating order successfully."""
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            event_date='2026-06-01'
        )

        self.assertTrue(success)
        self.assertIsNotNone(order)
        self.assertIsNone(error)
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.plan, self.premium_plan)
        self.assertEqual(order.status, 'DRAFT')
        self.assertIsNotNone(order.order_number)

    def test_create_order_with_custom_amount(self):
        """Test creating order with custom payment amount."""
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('599.00')
        )

        self.assertTrue(success)
        self.assertEqual(order.payment_amount, Decimal('599.00'))

    def test_create_order_default_payment_amount(self):
        """Test order uses plan price as default payment amount."""
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding'
        )

        self.assertTrue(success)
        self.assertEqual(order.payment_amount, self.premium_plan.price)

    def test_get_order_by_id_success(self):
        """Test getting order by ID successfully."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        success, retrieved_order, error = OrderService.get_order_by_id(str(order.id))
        self.assertTrue(success)
        self.assertEqual(retrieved_order.id, order.id)

    def test_get_order_by_id_not_found(self):
        """Test getting non-existent order."""
        import uuid
        fake_id = str(uuid.uuid4())
        success, order, error = OrderService.get_order_by_id(fake_id)
        self.assertFalse(success)
        self.assertIsNone(order)
        self.assertIsNotNone(error)

    def test_get_orders_by_user(self):
        """Test getting all orders for a user."""
        # Create multiple orders
        for i in range(3):
            Order.objects.create(
                user=self.user,
                plan=self.premium_plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00')
            )

        orders = OrderService.get_orders_by_user(self.user)
        self.assertEqual(orders.count(), 3)

    def test_get_orders_by_user_with_status_filter(self):
        """Test getting orders filtered by status."""
        Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Event 1',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )
        Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Event 2',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )

        draft_orders = OrderService.get_orders_by_user(self.user, status='DRAFT')
        self.assertEqual(draft_orders.count(), 1)

    def test_update_order_status_success(self):
        """Test updating order status successfully."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )

        success, error = OrderService.update_order_status(order, 'PENDING_PAYMENT')
        self.assertTrue(success)
        self.assertIsNone(error)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PENDING_PAYMENT')

    def test_update_order_status_with_notes(self):
        """Test updating order status with notes."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )

        success, error = OrderService.update_order_status(
            order,
            'REJECTED',
            notes='Invalid payment details'
        )
        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'REJECTED')
        self.assertIn('Invalid payment', order.notes)

    def test_can_user_order_plan_no_current_plan(self):
        """Test user with no plan can order any plan."""
        self.user.current_plan = None
        self.user.save()

        can_order, error = OrderService.can_user_order_plan(self.user, 'PREMIUM')
        self.assertTrue(can_order)
        self.assertIsNone(error)

    def test_can_user_order_plan_same_plan(self):
        """Test user can reorder their current plan."""
        self.user.current_plan = self.premium_plan
        self.user.save()

        can_order, error = OrderService.can_user_order_plan(self.user, 'PREMIUM')
        self.assertTrue(can_order)
        self.assertIsNone(error)

    def test_can_user_order_plan_different_plan(self):
        """Test user cannot order different plan while subscribed."""
        self.user.current_plan = self.basic_plan
        self.user.save()

        can_order, error = OrderService.can_user_order_plan(self.user, 'PREMIUM')
        self.assertFalse(can_order)
        self.assertIsNotNone(error)
        self.assertIn('subscribed', error.lower())

    def test_mark_order_as_paid(self):
        """Test marking order as paid."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='PENDING_PAYMENT'
        )

        success, error = OrderService.mark_order_as_paid(
            order,
            payment_id='pay_123456',
            payment_method='razorpay'
        )

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'PENDING_APPROVAL')
        self.assertEqual(order.payment_id, 'pay_123456')
        self.assertEqual(order.payment_method, 'razorpay')
        self.assertIsNotNone(order.paid_at)

    def test_approve_order(self):
        """Test approving an order."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='PENDING_APPROVAL'
        )

        success, error = OrderService.approve_order(order)

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'APPROVED')
        self.assertIsNotNone(order.approved_at)

    def test_reject_order(self):
        """Test rejecting an order."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='PENDING_APPROVAL'
        )

        success, error = OrderService.reject_order(
            order,
            reason='Invalid verification'
        )

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'REJECTED')
        self.assertIn('Invalid verification', order.notes)

    def test_cancel_order(self):
        """Test cancelling an order."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='PENDING_PAYMENT'
        )

        success, error = OrderService.cancel_order(order, 'User requested')

        self.assertTrue(success)
        order.refresh_from_db()
        self.assertEqual(order.status, 'CANCELLED')
        self.assertIn('User requested', order.notes)

    def test_get_order_summary(self):
        """Test getting order summary."""
        order = Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            event_date='2026-06-01',
            payment_amount=Decimal('499.00')
        )

        summary = OrderService.get_order_summary(order)

        self.assertEqual(summary['order_number'], order.order_number)
        self.assertEqual(summary['status'], order.status)
        self.assertEqual(summary['plan']['code'], 'PREMIUM')
        self.assertEqual(summary['template']['name'], 'Test Template')
        self.assertEqual(summary['occasion'], 'Wedding')
        self.assertEqual(summary['payment_amount'], Decimal('499.00'))

    def test_get_recent_orders(self):
        """Test getting recent orders."""
        # Create orders with different timestamps
        for i in range(5):
            Order.objects.create(
                user=self.user,
                plan=self.premium_plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00')
            )

        recent = OrderService.get_recent_orders(limit=3)
        self.assertEqual(len(recent), 3)

    def test_get_pending_approval_orders(self):
        """Test getting orders pending approval."""
        Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Event 1',
            payment_amount=Decimal('499.00'),
            status='PENDING_APPROVAL'
        )
        Order.objects.create(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Event 2',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )

        pending = OrderService.get_pending_approval_orders()
        self.assertEqual(pending.count(), 1)
        self.assertEqual(pending.first().status, 'PENDING_APPROVAL')
