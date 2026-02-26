"""
Unit tests for GuestService.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.invitations.models import Order, Invitation, Guest
from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.services import GuestService

User = get_user_model()


class GuestServiceTest(TestCase):
    """Test cases for GuestService."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

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

        # Create test order and invitation
        self.order = Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )
        self.invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True
        )

    def test_create_guest_success(self):
        """Test creating guest successfully."""
        success, guest, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Doe',
            email='john@example.com',
            phone='+1234567890',
            rsvp_status='ATTENDING'
        )

        self.assertTrue(success)
        self.assertIsNotNone(guest)
        self.assertIsNone(error)
        self.assertEqual(guest.name, 'John Doe')
        self.assertEqual(guest.email, 'john@example.com')
        self.assertEqual(guest.rsvp_status, 'ATTENDING')

    def test_create_guest_minimal_data(self):
        """Test creating guest with minimal required data."""
        success, guest, error = GuestService.create_guest(
            invitation=self.invitation,
            name='John Doe',
            rsvp_status='PENDING'
        )

        self.assertTrue(success)
        self.assertEqual(guest.name, 'John Doe')
        self.assertIsNone(guest.email)
        self.assertIsNone(guest.phone)

    def test_get_guest_by_id_success(self):
        """Test getting guest by ID successfully."""
        guest = Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            rsvp_status='ATTENDING'
        )

        success, retrieved_guest, error = GuestService.get_guest_by_id(str(guest.id))
        self.assertTrue(success)
        self.assertEqual(retrieved_guest.id, guest.id)

    def test_get_guest_by_id_not_found(self):
        """Test getting non-existent guest."""
        import uuid
        fake_id = str(uuid.uuid4())
        success, guest, error = GuestService.get_guest_by_id(fake_id)
        self.assertFalse(success)
        self.assertIsNone(guest)
        self.assertIsNotNone(error)

    def test_get_guests_by_invitation(self):
        """Test getting all guests for an invitation."""
        # Create multiple guests
        for i in range(3):
            Guest.objects.create(
                invitation=self.invitation,
                name=f'Guest {i}',
                rsvp_status='PENDING'
            )

        guests = GuestService.get_guests_by_invitation(self.invitation)
        self.assertEqual(guests.count(), 3)

    def test_get_guests_by_invitation_with_status_filter(self):
        """Test getting guests filtered by RSVP status."""
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 1',
            rsvp_status='ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 2',
            rsvp_status='NOT_ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 3',
            rsvp_status='ATTENDING'
        )

        attending = GuestService.get_guests_by_invitation(
            self.invitation,
            rsvp_status='ATTENDING'
        )
        self.assertEqual(attending.count(), 2)

    def test_update_guest_rsvp_success(self):
        """Test updating guest RSVP status successfully."""
        guest = Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            rsvp_status='PENDING'
        )

        success, error = GuestService.update_guest_rsvp(
            guest,
            'ATTENDING',
            message='Looking forward to it!'
        )

        self.assertTrue(success)
        guest.refresh_from_db()
        self.assertEqual(guest.rsvp_status, 'ATTENDING')
        self.assertEqual(guest.message, 'Looking forward to it!')

    def test_generate_device_fingerprint(self):
        """Test generating device fingerprint."""
        fingerprint = GuestService.generate_device_fingerprint(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            screen_resolution='1920x1080',
            timezone_offset='-300',
            languages='en-US,en',
            canvas_hash='abc123def456'
        )

        self.assertIsNotNone(fingerprint)
        self.assertEqual(len(fingerprint), 64)  # SHA-256 produces 64 hex characters

    def test_generate_device_fingerprint_consistency(self):
        """Test fingerprint is consistent for same inputs."""
        fp1 = GuestService.generate_device_fingerprint(
            user_agent='Mozilla/5.0',
            screen_resolution='1920x1080'
        )
        fp2 = GuestService.generate_device_fingerprint(
            user_agent='Mozilla/5.0',
            screen_resolution='1920x1080'
        )

        self.assertEqual(fp1, fp2)

    def test_generate_device_fingerprint_different_for_different_inputs(self):
        """Test fingerprint differs for different inputs."""
        fp1 = GuestService.generate_device_fingerprint(
            user_agent='Mozilla/5.0',
            screen_resolution='1920x1080'
        )
        fp2 = GuestService.generate_device_fingerprint(
            user_agent='Chrome/90.0',
            screen_resolution='1920x1080'
        )

        self.assertNotEqual(fp1, fp2)

    def test_check_duplicate_guest_by_fingerprint(self):
        """Test checking duplicate guest by device fingerprint."""
        fingerprint = 'test_fingerprint_123'

        # Create guest with fingerprint
        Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            device_fingerprint=fingerprint,
            rsvp_status='ATTENDING'
        )

        # Check for duplicate
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            device_fingerprint=fingerprint
        )

        self.assertTrue(is_duplicate)
        self.assertIsNotNone(existing_guest)
        self.assertEqual(existing_guest.name, 'John Doe')

    def test_check_duplicate_guest_no_duplicate(self):
        """Test no duplicate found when guest doesn't exist."""
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            device_fingerprint='unique_fingerprint'
        )

        self.assertFalse(is_duplicate)
        self.assertIsNone(existing_guest)

    def test_check_duplicate_guest_by_backup_method(self):
        """Test checking duplicate by backup method (IP + User Agent)."""
        ip_address = '192.168.1.1'
        user_agent = 'Mozilla/5.0'

        # Create guest with IP and UA
        Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            ip_address=ip_address,
            user_agent=user_agent,
            rsvp_status='ATTENDING'
        )

        # Check for duplicate (no fingerprint provided, should use backup)
        is_duplicate, existing_guest = GuestService.check_duplicate_guest(
            invitation=self.invitation,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.assertTrue(is_duplicate)
        self.assertIsNotNone(existing_guest)

    def test_parse_user_agent(self):
        """Test parsing user agent string."""
        ua_string = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        parsed = GuestService.parse_user_agent(ua_string)

        self.assertIn('browser', parsed)
        self.assertIn('os', parsed)
        self.assertIn('device', parsed)

    def test_get_guest_count_by_rsvp(self):
        """Test getting guest counts by RSVP status."""
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 1',
            rsvp_status='ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 2',
            rsvp_status='ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 3',
            rsvp_status='NOT_ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Guest 4',
            rsvp_status='PENDING'
        )

        counts = GuestService.get_guest_count_by_rsvp(self.invitation)

        self.assertEqual(counts['ATTENDING'], 2)
        self.assertEqual(counts['NOT_ATTENDING'], 1)
        self.assertEqual(counts['PENDING'], 1)
        self.assertEqual(counts['total'], 4)

    def test_export_guests_to_csv(self):
        """Test exporting guests to CSV."""
        # Create some guests
        Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            email='john@example.com',
            phone='+1234567890',
            rsvp_status='ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Jane Smith',
            email='jane@example.com',
            rsvp_status='NOT_ATTENDING'
        )

        csv_data = GuestService.export_guests_to_csv(self.invitation)

        self.assertIsNotNone(csv_data)
        self.assertIn('John Doe', csv_data)
        self.assertIn('Jane Smith', csv_data)
        self.assertIn('john@example.com', csv_data)
        self.assertIn('ATTENDING', csv_data)

    def test_get_guest_summary(self):
        """Test getting guest summary."""
        guest = Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            email='john@example.com',
            phone='+1234567890',
            rsvp_status='ATTENDING',
            message='Looking forward!'
        )

        summary = GuestService.get_guest_summary(guest)

        self.assertEqual(summary['name'], 'John Doe')
        self.assertEqual(summary['email'], 'john@example.com')
        self.assertEqual(summary['phone'], '+1234567890')
        self.assertEqual(summary['rsvp_status'], 'ATTENDING')
        self.assertEqual(summary['message'], 'Looking forward!')

    def test_delete_guest_success(self):
        """Test deleting guest successfully."""
        guest = Guest.objects.create(
            invitation=self.invitation,
            name='John Doe',
            rsvp_status='PENDING'
        )
        guest_id = guest.id

        success, error = GuestService.delete_guest(guest)

        self.assertTrue(success)
        self.assertFalse(Guest.objects.filter(id=guest_id).exists())

    def test_get_recent_guests(self):
        """Test getting recent guests."""
        # Create multiple guests
        for i in range(5):
            Guest.objects.create(
                invitation=self.invitation,
                name=f'Guest {i}',
                rsvp_status='PENDING'
            )

        recent = GuestService.get_recent_guests(self.invitation, limit=3)
        self.assertEqual(len(recent), 3)

    def test_get_attending_guests(self):
        """Test getting guests who are attending."""
        Guest.objects.create(
            invitation=self.invitation,
            name='Attending 1',
            rsvp_status='ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Not Attending',
            rsvp_status='NOT_ATTENDING'
        )
        Guest.objects.create(
            invitation=self.invitation,
            name='Attending 2',
            rsvp_status='ATTENDING'
        )

        attending = GuestService.get_attending_guests(self.invitation)
        self.assertEqual(attending.count(), 2)
