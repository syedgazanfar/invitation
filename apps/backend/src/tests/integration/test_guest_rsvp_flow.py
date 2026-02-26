"""
Integration tests for guest registration and RSVP flow.

This tests the complete workflow:
1. Guest receives invitation link
2. Guest visits invitation page (view count increments)
3. Guest registers with details
4. System checks for duplicates via device fingerprinting
5. Guest submits RSVP
6. Host views guest list and analytics
"""
from django.test import TestCase, TransactionTestCase, RequestFactory
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.models import Order, Invitation, Guest
from apps.invitations.services import (
    OrderService,
    InvitationService,
    GuestService,
    AnalyticsService
)

User = get_user_model()


class GuestRSVPFlowIntegrationTest(TransactionTestCase):
    """Integration tests for guest registration and RSVP flow."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create host user
        self.host = User.objects.create_user(
            email='host@example.com',
            password='testpass123',
            full_name='Host User'
        )

        # Create plan and template
        self.plan = Plan.objects.create(
            code='PREMIUM',
            name='Premium Plan',
            price=499.00,
            is_active=True
        )

        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            is_active=True
        )

        self.template = Template.objects.create(
            name='Elegant Wedding',
            description='Beautiful template',
            plan=self.plan,
            category=self.category,
            animation_type='elegant',
            is_active=True
        )

        # Create approved order
        self.order = Order.objects.create(
            user=self.host,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )

        # Create active invitation
        success, self.invitation, error = InvitationService.create_invitation(
            order=self.order,
            title='Wedding Invitation',
            message='Join us for our special day!'
        )
        InvitationService.activate_invitation(self.invitation)

    def test_complete_guest_registration_flow(self):
        """Test complete guest registration and RSVP flow."""

        # Step 1: Guest visits invitation link (first time)
        success, error = InvitationService.increment_view_count(self.invitation)
        self.assertTrue(success)

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.total_views, 1)

        # Step 2: Generate device fingerprint
        fingerprint = GuestService.generate_device_fingerprint(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            screen_resolution='1920x1080',
            timezone_offset='-300',
            languages='en-US,en'
        )

        self.assertIsNotNone(fingerprint)
        self.assertEqual(len(fingerprint), 64)

        # Step 3: Check for duplicate (first time, should not exist)
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            device_fingerprint=fingerprint
        )

        self.assertFalse(is_duplicate)
        self.assertIsNone(existing_guest)

        # Step 4: Create guest registration
        request = self.factory.post('/register/')
        request.META['REMOTE_ADDR'] = '192.168.1.100'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        success, guest, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Smith',
            email='john@example.com',
            phone='+919876543210',
            rsvp_status='ATTENDING',
            device_fingerprint=fingerprint,
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0'
        )

        self.assertTrue(success)
        self.assertIsNotNone(guest)
        self.assertEqual(guest.name, 'John Smith')
        self.assertEqual(guest.rsvp_status, 'ATTENDING')

        # Step 5: Update unique guest count
        self.invitation.unique_guests += 1
        self.invitation.save()

        # Step 6: Guest submits additional message
        success, error = GuestService.update_guest_rsvp(
            guest,
            'ATTENDING',
            message='Looking forward to the celebration!'
        )

        self.assertTrue(success)
        guest.refresh_from_db()
        self.assertEqual(guest.message, 'Looking forward to the celebration!')

        # Step 7: Host views guest list
        guests = GuestService.get_guests_by_invitation(self.invitation)
        self.assertEqual(guests.count(), 1)

        # Step 8: Host views analytics
        stats = AnalyticsService.get_invitation_stats(self.invitation)
        self.assertEqual(stats['views']['total'], 1)
        self.assertEqual(stats['guests']['total'], 1)
        self.assertEqual(stats['guests']['attending'], 1)

    def test_duplicate_guest_prevention(self):
        """Test duplicate guest detection prevents multiple registrations."""

        fingerprint = 'test_fingerprint_123'

        # First registration
        success, guest1, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Smith',
            email='john@example.com',
            rsvp_status='ATTENDING',
            device_fingerprint=fingerprint
        )

        self.assertTrue(success)

        # Try to register again with same fingerprint
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            device_fingerprint=fingerprint
        )

        self.assertTrue(is_duplicate)
        self.assertIsNotNone(existing_guest)
        self.assertEqual(existing_guest.id, guest1.id)

    def test_multiple_guests_registration(self):
        """Test multiple guests can register for same invitation."""

        guests_data = [
            {
                'name': 'John Smith',
                'email': 'john@example.com',
                'fingerprint': 'fingerprint_1',
                'rsvp': 'ATTENDING'
            },
            {
                'name': 'Jane Doe',
                'email': 'jane@example.com',
                'fingerprint': 'fingerprint_2',
                'rsvp': 'ATTENDING'
            },
            {
                'name': 'Bob Johnson',
                'email': 'bob@example.com',
                'fingerprint': 'fingerprint_3',
                'rsvp': 'NOT_ATTENDING'
            }
        ]

        for data in guests_data:
            success, guest, error = GuestService.create_guest(
                invitation=self.invitation,
                name=data['name'],
                email=data['email'],
                rsvp_status=data['rsvp'],
                device_fingerprint=data['fingerprint']
            )
            self.assertTrue(success)

        # Verify all guests registered
        all_guests = GuestService.get_guests_by_invitation(self.invitation)
        self.assertEqual(all_guests.count(), 3)

        # Check RSVP counts
        counts = GuestService.get_guest_count_by_rsvp(self.invitation)
        self.assertEqual(counts['ATTENDING'], 2)
        self.assertEqual(counts['NOT_ATTENDING'], 1)
        self.assertEqual(counts['total'], 3)

    def test_guest_rsvp_change_flow(self):
        """Test guest changing their RSVP status."""

        # Initial registration
        success, guest, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Smith',
            email='john@example.com',
            rsvp_status='PENDING'
        )

        self.assertTrue(success)
        self.assertEqual(guest.rsvp_status, 'PENDING')

        # Guest decides to attend
        success, error = GuestService.update_guest_rsvp(
            guest,
            'ATTENDING',
            message='Count me in!'
        )

        self.assertTrue(success)
        guest.refresh_from_db()
        self.assertEqual(guest.rsvp_status, 'ATTENDING')

        # Guest changes mind
        success, error = GuestService.update_guest_rsvp(
            guest,
            'NOT_ATTENDING',
            message='Sorry, cannot make it'
        )

        self.assertTrue(success)
        guest.refresh_from_db()
        self.assertEqual(guest.rsvp_status, 'NOT_ATTENDING')

    def test_guest_list_export_flow(self):
        """Test exporting guest list to CSV."""

        # Create multiple guests
        for i in range(5):
            GuestService.create_guest(
                invitation=self.invitation,
                name=f'Guest {i}',
                email=f'guest{i}@example.com',
                phone=f'+9198765432{i}0',
                rsvp_status='ATTENDING' if i < 3 else 'NOT_ATTENDING'
            )

        # Export guest list
        csv_data = GuestService.export_guests_to_csv(self.invitation)

        self.assertIsNotNone(csv_data)
        self.assertIn('Guest 0', csv_data)
        self.assertIn('guest0@example.com', csv_data)

    def test_expired_invitation_flow(self):
        """Test guest trying to access expired invitation."""

        # Set invitation as expired
        self.invitation.link_expires_at = timezone.now() - timedelta(days=1)
        self.invitation.save()

        # Check if expired
        is_expired = InvitationService.is_invitation_expired(self.invitation)
        self.assertTrue(is_expired)

        # Guest should not be able to register (business logic would prevent this)
        # This would be enforced at the view level

    def test_inactive_invitation_flow(self):
        """Test guest trying to access inactive invitation."""

        # Deactivate invitation
        success, error = InvitationService.deactivate_invitation(self.invitation)
        self.assertTrue(success)

        self.invitation.refresh_from_db()
        self.assertFalse(self.invitation.is_active)

        # Guest registration would be blocked at view level

    def test_engagement_analytics_flow(self):
        """Test engagement analytics calculation."""

        # Set invitation stats
        self.invitation.total_views = 100
        self.invitation.unique_guests = 50
        self.invitation.save()

        # Create 10 guests
        for i in range(10):
            GuestService.create_guest(
                invitation=self.invitation,
                name=f'Guest {i}',
                rsvp_status='ATTENDING' if i < 6 else 'NOT_ATTENDING'
            )

        # Calculate engagement metrics
        engagement_rate = AnalyticsService.get_invitation_engagement_rate(
            self.invitation
        )
        self.assertEqual(engagement_rate, 20.0)  # 10 guests / 50 unique = 20%

        conversion_rate = AnalyticsService.get_rsvp_conversion_rate(
            self.invitation
        )
        self.assertEqual(conversion_rate, 20.0)  # 10 guests / 50 unique = 20%

        attendance_rate = AnalyticsService.get_attendance_rate(
            self.invitation
        )
        self.assertEqual(attendance_rate, 60.0)  # 6 attending / 10 total = 60%

    def test_guest_with_minimal_info_flow(self):
        """Test guest registration with minimal required information."""

        # Register with only name and RSVP
        success, guest, error = GuestService.create_guest(
            invitation=self.invitation,
            name='Anonymous Guest',
            rsvp_status='ATTENDING'
        )

        self.assertTrue(success)
        self.assertIsNotNone(guest)
        self.assertIsNone(guest.email)
        self.assertIsNone(guest.phone)

    def test_backup_duplicate_detection_flow(self):
        """Test backup duplicate detection using IP + User Agent."""

        ip_address = '192.168.1.100'
        user_agent = 'Mozilla/5.0 (specific browser)'

        # First registration
        success, guest1, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Smith',
            rsvp_status='ATTENDING',
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.assertTrue(success)

        # Try to register with same IP and UA (no fingerprint)
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.assertTrue(is_duplicate)
        self.assertEqual(existing_guest.id, guest1.id)

    def test_invitation_extension_flow(self):
        """Test extending invitation expiry."""

        # Set near expiry
        self.invitation.link_expires_at = timezone.now() + timedelta(days=2)
        self.invitation.save()

        original_expiry = self.invitation.link_expires_at

        # Extend by 14 days
        success, error = InvitationService.extend_invitation_expiry(
            self.invitation,
            days=14
        )

        self.assertTrue(success)
        self.invitation.refresh_from_db()
        self.assertGreater(self.invitation.link_expires_at, original_expiry)

        # Should no longer be near expiry
        days_until_expiry = (self.invitation.link_expires_at - timezone.now().date()).days
        self.assertGreater(days_until_expiry, 10)
