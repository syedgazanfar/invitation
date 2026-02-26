"""
Unit tests for AnalyticsService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.invitations.models import Order, Invitation, Guest
from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.services import AnalyticsService

User = get_user_model()


class AnalyticsServiceTest(TestCase):
    """Test cases for AnalyticsService."""

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
            event_date='2026-06-01',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )

        # Create test invitation
        self.invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            total_views=50,
            unique_guests=25
        )

        # Create test guests
        for i in range(5):
            Guest.objects.create(
                invitation=self.invitation,
                name=f'Guest {i}',
                rsvp_status='ATTENDING' if i < 3 else 'NOT_ATTENDING'
            )

    def test_get_invitation_stats(self):
        """Test getting invitation statistics."""
        stats = AnalyticsService.get_invitation_stats(self.invitation)

        self.assertIn('views', stats)
        self.assertEqual(stats['views']['total'], 50)
        self.assertEqual(stats['views']['unique_guests'], 25)

        self.assertIn('guests', stats)
        self.assertEqual(stats['guests']['total'], 5)
        self.assertEqual(stats['guests']['attending'], 3)
        self.assertEqual(stats['guests']['not_attending'], 2)

    def test_get_user_analytics(self):
        """Test getting user analytics."""
        # Create multiple orders and invitations
        for i in range(3):
            order = Order.objects.create(
                user=self.user,
                plan=self.plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00'),
                status='APPROVED'
            )
            Invitation.objects.create(
                order=order,
                title=f'Invitation {i}',
                message='Test',
                is_active=True
            )

        analytics = AnalyticsService.get_user_analytics(self.user)

        self.assertIn('total_orders', analytics)
        self.assertEqual(analytics['total_orders'], 4)  # Including setUp order

        self.assertIn('total_invitations', analytics)
        self.assertEqual(analytics['total_invitations'], 4)

    def test_get_order_analytics_by_status(self):
        """Test getting order analytics by status."""
        # Create orders with different statuses
        Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Event 1',
            payment_amount=Decimal('499.00'),
            status='DRAFT'
        )
        Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Event 2',
            payment_amount=Decimal('499.00'),
            status='PENDING_PAYMENT'
        )

        analytics = AnalyticsService.get_order_analytics_by_status(self.user)

        self.assertIn('APPROVED', analytics)
        self.assertEqual(analytics['APPROVED'], 1)
        self.assertIn('DRAFT', analytics)
        self.assertEqual(analytics['DRAFT'], 1)

    def test_get_invitation_engagement_rate(self):
        """Test calculating invitation engagement rate."""
        rate = AnalyticsService.get_invitation_engagement_rate(self.invitation)

        # 5 guests out of 25 unique visitors = 20% engagement
        self.assertEqual(rate, 20.0)

    def test_get_invitation_engagement_rate_zero_views(self):
        """Test engagement rate with zero views."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='No Views',
            message='Test',
            total_views=0,
            unique_guests=0
        )

        rate = AnalyticsService.get_invitation_engagement_rate(invitation)
        self.assertEqual(rate, 0.0)

    def test_get_rsvp_conversion_rate(self):
        """Test calculating RSVP conversion rate."""
        # 5 guests responded out of 25 unique visitors = 20%
        rate = AnalyticsService.get_rsvp_conversion_rate(self.invitation)
        self.assertEqual(rate, 20.0)

    def test_get_attendance_rate(self):
        """Test calculating attendance rate."""
        # 3 attending out of 5 total guests = 60%
        rate = AnalyticsService.get_attendance_rate(self.invitation)
        self.assertEqual(rate, 60.0)

    def test_get_attendance_rate_no_guests(self):
        """Test attendance rate with no guests."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='No Guests',
            message='Test'
        )

        rate = AnalyticsService.get_attendance_rate(invitation)
        self.assertEqual(rate, 0.0)

    def test_get_popular_templates(self):
        """Test getting popular templates."""
        # Update template use counts
        self.template.use_count = 100
        self.template.save()

        popular = AnalyticsService.get_popular_templates(limit=5)

        self.assertEqual(len(popular), 1)
        self.assertEqual(popular[0]['name'], 'Test Template')
        self.assertEqual(popular[0]['use_count'], 100)

    def test_get_revenue_analytics(self):
        """Test getting revenue analytics."""
        # Create more paid orders
        for i in range(3):
            Order.objects.create(
                user=self.user,
                plan=self.plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00'),
                status='APPROVED'
            )

        revenue = AnalyticsService.get_revenue_analytics(days=30)

        self.assertIn('total_revenue', revenue)
        self.assertEqual(revenue['total_revenue'], Decimal('1996.00'))  # 4 * 499
        self.assertIn('total_orders', revenue)
        self.assertEqual(revenue['total_orders'], 4)

    def test_get_plan_distribution(self):
        """Test getting plan distribution."""
        # Create another plan and orders
        basic_plan = Plan.objects.create(
            code='BASIC',
            name='Basic Plan',
            price=0.00,
            is_active=True
        )

        for i in range(2):
            Order.objects.create(
                user=self.user,
                plan=basic_plan,
                template=self.template,
                occasion=f'Basic Event {i}',
                payment_amount=Decimal('0.00'),
                status='APPROVED'
            )

        distribution = AnalyticsService.get_plan_distribution()

        self.assertIn('PREMIUM', distribution)
        self.assertEqual(distribution['PREMIUM'], 1)
        self.assertIn('BASIC', distribution)
        self.assertEqual(distribution['BASIC'], 2)

    def test_get_most_used_templates(self):
        """Test getting most used templates."""
        # Create another template with higher use count
        template2 = Template.objects.create(
            name='Popular Template',
            description='Very popular',
            plan=self.plan,
            category=self.category,
            animation_type='fun',
            use_count=200,
            is_active=True
        )

        self.template.use_count = 100
        self.template.save()

        most_used = AnalyticsService.get_most_used_templates(limit=2)

        self.assertEqual(len(most_used), 2)
        self.assertEqual(most_used[0]['name'], 'Popular Template')
        self.assertEqual(most_used[0]['use_count'], 200)

    def test_get_invitation_link_analytics(self):
        """Test getting invitation link analytics."""
        analytics = AnalyticsService.get_invitation_link_analytics(self.invitation)

        self.assertIn('regular_link', analytics)
        self.assertIn('test_link', analytics)
        self.assertIn('total_views', analytics)
        self.assertEqual(analytics['total_views'], 50)

    def test_get_time_series_views(self):
        """Test getting time series view data."""
        # This would require historical data tracking
        # For now, test the structure
        time_series = AnalyticsService.get_time_series_views(
            self.invitation,
            days=7
        )

        self.assertIsInstance(time_series, list)

    def test_get_guest_registration_trends(self):
        """Test getting guest registration trends."""
        trends = AnalyticsService.get_guest_registration_trends(
            self.invitation,
            days=7
        )

        self.assertIsInstance(trends, dict)
        self.assertIn('total_registrations', trends)

    def test_get_comparative_analytics(self):
        """Test getting comparative analytics."""
        # Create another invitation for comparison
        order2 = Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Another Event',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )
        invitation2 = Invitation.objects.create(
            order=order2,
            title='Another Invitation',
            message='Test',
            is_active=True,
            total_views=100,
            unique_guests=50
        )

        comparison = AnalyticsService.get_comparative_analytics([
            self.invitation,
            invitation2
        ])

        self.assertEqual(len(comparison), 2)
        self.assertIn('views', comparison[0])
        self.assertIn('engagement_rate', comparison[0])
