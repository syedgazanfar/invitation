"""
Integration tests for complete invitation lifecycle.

This tests the complete workflow:
1. User creates order for invitation
2. Order gets approved
3. Invitation is created
4. Invitation is customized
5. Invitation is activated
6. Guests register and RSVP
7. Host monitors analytics
8. Invitation expires or gets deactivated
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.models import Order, Invitation, Guest
from apps.invitations.services import (
    OrderService,
    InvitationService,
    GuestService,
    AnalyticsService
)
from apps.plans.services import TemplateService

User = get_user_model()


class InvitationLifecycleIntegrationTest(TransactionTestCase):
    """Integration tests for complete invitation lifecycle."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            email='host@example.com',
            password='testpass123',
            full_name='Host User'
        )

        # Create plans
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

        # Create category and templates
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            is_active=True
        )

        self.template = Template.objects.create(
            name='Elegant Wedding',
            description='Beautiful template',
            plan=self.premium_plan,
            category=self.category,
            animation_type='elegant',
            is_active=True
        )

    def test_complete_invitation_lifecycle(self):
        """Test complete invitation lifecycle from creation to completion."""

        # Phase 1: Order Creation
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding Anniversary',
            event_date='2026-12-15',
            host_name='John & Jane',
            venue='Grand Ballroom'
        )

        self.assertTrue(success)
        self.assertEqual(order.status, 'DRAFT')

        # Phase 2: Order Approval
        order.status = 'PENDING_APPROVAL'
        order.paid_at = timezone.now()
        order.save()

        success, error = OrderService.approve_order(order)
        self.assertTrue(success)
        self.assertEqual(order.status, 'APPROVED')

        # Phase 3: Invitation Creation
        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='25th Wedding Anniversary',
            message='Join us in celebrating 25 years of love and happiness!'
        )

        self.assertTrue(success)
        self.assertIsNotNone(invitation.slug)

        # Phase 4: Invitation Customization
        success, error = InvitationService.update_invitation(
            invitation,
            title='Silver Jubilee Celebration',
            message='Join us for our 25th wedding anniversary celebration!',
            event_date='2026-12-15',
            venue='Grand Ballroom, City Hotel'
        )

        self.assertTrue(success)

        # Phase 5: Invitation Activation
        success, error = InvitationService.activate_invitation(invitation)
        self.assertTrue(success)

        invitation.refresh_from_db()
        self.assertTrue(invitation.is_active)
        self.assertIsNotNone(invitation.link_expires_at)

        # Phase 6: Template Usage Increment
        success, error = TemplateService.increment_template_usage(
            str(self.template.id)
        )
        self.assertTrue(success)

        # Phase 7: Guests Register
        guests_data = [
            {'name': 'Alice Johnson', 'email': 'alice@example.com', 'rsvp': 'ATTENDING'},
            {'name': 'Bob Smith', 'email': 'bob@example.com', 'rsvp': 'ATTENDING'},
            {'name': 'Carol Davis', 'email': 'carol@example.com', 'rsvp': 'NOT_ATTENDING'},
            {'name': 'David Wilson', 'email': 'david@example.com', 'rsvp': 'ATTENDING'},
        ]

        for guest_data in guests_data:
            success, guest, error = GuestService.create_guest(
                invitation=invitation,
                name=guest_data['name'],
                email=guest_data['email'],
                rsvp_status=guest_data['rsvp']
            )
            self.assertTrue(success)

            # Increment view count for each guest visit
            InvitationService.increment_view_count(invitation)

        # Update invitation stats
        invitation.unique_guests = len(guests_data)
        invitation.save()

        # Phase 8: Host Monitors Analytics
        stats = AnalyticsService.get_invitation_stats(invitation)

        self.assertEqual(stats['guests']['total'], 4)
        self.assertEqual(stats['guests']['attending'], 3)
        self.assertEqual(stats['guests']['not_attending'], 1)
        self.assertEqual(stats['views']['total'], 4)

        engagement_rate = AnalyticsService.get_invitation_engagement_rate(invitation)
        self.assertEqual(engagement_rate, 100.0)  # 4 guests / 4 unique visitors

        attendance_rate = AnalyticsService.get_attendance_rate(invitation)
        self.assertEqual(attendance_rate, 75.0)  # 3 attending / 4 total

        # Phase 9: Export Guest List
        csv_data = GuestService.export_guests_to_csv(invitation)
        self.assertIsNotNone(csv_data)
        self.assertIn('Alice Johnson', csv_data)

        # Phase 10: Invitation Completion
        # After event is over, deactivate invitation
        success, error = InvitationService.deactivate_invitation(invitation)
        self.assertTrue(success)

        invitation.refresh_from_db()
        self.assertFalse(invitation.is_active)

    def test_invitation_with_extension(self):
        """Test invitation lifecycle with expiry extension."""

        # Create and approve order
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Birthday Party',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        # Create invitation
        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Birthday Bash',
            message='Come celebrate!'
        )

        # Activate with default expiry
        InvitationService.activate_invitation(invitation)

        original_expiry = invitation.link_expires_at

        # Extend expiry
        success, error = InvitationService.extend_invitation_expiry(
            invitation,
            days=14
        )

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertGreater(invitation.link_expires_at, original_expiry)

    def test_multi_invitation_management(self):
        """Test user managing multiple invitations."""

        invitations = []

        # Create 3 different orders/invitations
        for i in range(3):
            # Create order
            success, order, error = OrderService.create_order(
                user=self.user,
                plan=self.premium_plan,
                template=self.template,
                occasion=f'Event {i}',
                payment_amount=Decimal('499.00')
            )

            order.status = 'APPROVED'
            order.save()

            # Create invitation
            success, invitation, error = InvitationService.create_invitation(
                order=order,
                title=f'Invitation {i}',
                message=f'Event {i} invitation'
            )

            InvitationService.activate_invitation(invitation)
            invitations.append(invitation)

        # Get all user invitations
        user_invitations = InvitationService.get_invitations_by_user(self.user)
        self.assertEqual(user_invitations.count(), 3)

        # Get only active invitations
        active_invitations = InvitationService.get_active_invitations(self.user)
        self.assertEqual(active_invitations.count(), 3)

        # Deactivate one
        InvitationService.deactivate_invitation(invitations[0])

        active_invitations = InvitationService.get_active_invitations(self.user)
        self.assertEqual(active_invitations.count(), 2)

    def test_invitation_url_generation(self):
        """Test invitation URL generation and access."""

        # Create order and invitation
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Wedding Invitation',
            message='Join us!'
        )

        # Generate URL
        url = InvitationService.generate_invitation_url(invitation)
        self.assertIn(invitation.slug, url)

        # Retrieve by slug
        success, retrieved_inv, error = InvitationService.get_invitation_by_slug(
            invitation.slug
        )

        self.assertTrue(success)
        self.assertEqual(retrieved_inv.id, invitation.id)

    def test_invitation_analytics_timeline(self):
        """Test invitation analytics over time."""

        # Create order and invitation
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Anniversary',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Anniversary Party',
            message='Celebrate with us!'
        )

        InvitationService.activate_invitation(invitation)

        # Simulate activity over time
        # Day 1: 5 views, 2 registrations
        for i in range(5):
            InvitationService.increment_view_count(invitation)

        for i in range(2):
            GuestService.create_guest(
                invitation=invitation,
                name=f'Guest {i}',
                rsvp_status='ATTENDING'
            )

        invitation.unique_guests = 5
        invitation.save()

        # Day 2: 3 more views, 1 more registration
        for i in range(3):
            InvitationService.increment_view_count(invitation)

        GuestService.create_guest(
            invitation=invitation,
            name='Guest 2',
            rsvp_status='ATTENDING'
        )

        invitation.unique_guests = 8
        invitation.save()

        # Check cumulative stats
        stats = AnalyticsService.get_invitation_stats(invitation)
        self.assertEqual(stats['views']['total'], 8)
        self.assertEqual(stats['guests']['total'], 3)
        self.assertEqual(stats['guests']['attending'], 3)

    def test_invitation_with_template_change(self):
        """Test changing template affects invitation."""

        # Create order with initial template
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Party',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Party Invitation',
            message='Join the fun!'
        )

        # Initial template
        self.assertEqual(invitation.order.template.id, self.template.id)

        # Template usage should increment when invitation is created
        initial_use_count = self.template.use_count
        TemplateService.increment_template_usage(str(self.template.id))

        self.template.refresh_from_db()
        self.assertEqual(self.template.use_count, initial_use_count + 1)

    def test_invitation_access_control(self):
        """Test invitation access control."""

        # Create invitation
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Private Event',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Private Event',
            message='Exclusive invitation'
        )

        # Owner can edit
        can_edit = InvitationService.can_user_edit_invitation(
            self.user,
            invitation
        )
        self.assertTrue(can_edit)

        # Other user cannot edit
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other User'
        )

        can_edit = InvitationService.can_user_edit_invitation(
            other_user,
            invitation
        )
        self.assertFalse(can_edit)

    def test_expired_invitation_cleanup(self):
        """Test identifying and handling expired invitations."""

        # Create expired invitation
        success, order, error = OrderService.create_order(
            user=self.user,
            plan=self.premium_plan,
            template=self.template,
            occasion='Old Event',
            payment_amount=Decimal('499.00')
        )

        order.status = 'APPROVED'
        order.save()

        success, invitation, error = InvitationService.create_invitation(
            order=order,
            title='Old Event',
            message='This has expired'
        )

        # Set as expired
        invitation.is_active = True
        invitation.link_expires_at = timezone.now() - timedelta(days=1)
        invitation.save()

        # Check if expired
        is_expired = InvitationService.is_invitation_expired(invitation)
        self.assertTrue(is_expired)

        # Get all expired invitations
        expired = InvitationService.get_expired_invitations()
        self.assertIn(invitation, expired)
