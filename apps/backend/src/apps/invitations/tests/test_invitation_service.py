"""
Unit tests for InvitationService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from apps.invitations.models import Order, Invitation
from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.services import InvitationService

User = get_user_model()


class InvitationServiceTest(TestCase):
    """Test cases for InvitationService."""

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

    def test_create_invitation_success(self):
        """Test creating invitation successfully."""
        success, invitation, error = InvitationService.create_invitation(
            order=self.order,
            title='Wedding Invitation',
            message='Join us for our wedding'
        )

        self.assertTrue(success)
        self.assertIsNotNone(invitation)
        self.assertIsNone(error)
        self.assertEqual(invitation.order, self.order)
        self.assertEqual(invitation.title, 'Wedding Invitation')
        self.assertIsNotNone(invitation.slug)

    def test_create_invitation_generates_unique_slug(self):
        """Test invitation gets unique slug."""
        success1, inv1, _ = InvitationService.create_invitation(
            order=self.order,
            title='Wedding Invitation',
            message='Message 1'
        )
        # Create order for second invitation
        order2 = Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Wedding',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )
        success2, inv2, _ = InvitationService.create_invitation(
            order=order2,
            title='Wedding Invitation',
            message='Message 2'
        )

        self.assertTrue(success1 and success2)
        self.assertNotEqual(inv1.slug, inv2.slug)

    def test_get_invitation_by_id_success(self):
        """Test getting invitation by ID successfully."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message'
        )

        success, retrieved_inv, error = InvitationService.get_invitation_by_id(str(invitation.id))
        self.assertTrue(success)
        self.assertEqual(retrieved_inv.id, invitation.id)

    def test_get_invitation_by_id_not_found(self):
        """Test getting non-existent invitation."""
        import uuid
        fake_id = str(uuid.uuid4())
        success, invitation, error = InvitationService.get_invitation_by_id(fake_id)
        self.assertFalse(success)
        self.assertIsNone(invitation)
        self.assertIsNotNone(error)

    def test_get_invitation_by_slug_success(self):
        """Test getting invitation by slug successfully."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            slug='test-slug-123'
        )

        success, retrieved_inv, error = InvitationService.get_invitation_by_slug('test-slug-123')
        self.assertTrue(success)
        self.assertEqual(retrieved_inv.slug, 'test-slug-123')

    def test_get_invitation_by_slug_not_found(self):
        """Test getting invitation with non-existent slug."""
        success, invitation, error = InvitationService.get_invitation_by_slug('nonexistent')
        self.assertFalse(success)
        self.assertIsNone(invitation)

    def test_get_invitations_by_user(self):
        """Test getting all invitations for a user."""
        # Create multiple invitations
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
                message=f'Message {i}'
            )

        invitations = InvitationService.get_invitations_by_user(self.user)
        self.assertEqual(invitations.count(), 3)

    def test_update_invitation_success(self):
        """Test updating invitation successfully."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Original Title',
            message='Original message'
        )

        success, error = InvitationService.update_invitation(
            invitation,
            title='Updated Title',
            message='Updated message'
        )

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertEqual(invitation.title, 'Updated Title')
        self.assertEqual(invitation.message, 'Updated message')

    def test_update_invitation_partial(self):
        """Test partially updating invitation."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Original Title',
            message='Original message'
        )

        success, error = InvitationService.update_invitation(
            invitation,
            title='Updated Title'
            # message not provided
        )

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertEqual(invitation.title, 'Updated Title')
        self.assertEqual(invitation.message, 'Original message')

    def test_activate_invitation(self):
        """Test activating invitation."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=False
        )

        success, error = InvitationService.activate_invitation(invitation)

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertTrue(invitation.is_active)
        self.assertIsNotNone(invitation.link_expires_at)

    def test_deactivate_invitation(self):
        """Test deactivating invitation."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True
        )

        success, error = InvitationService.deactivate_invitation(invitation)

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertFalse(invitation.is_active)

    def test_is_invitation_expired_not_expired(self):
        """Test checking if invitation is not expired."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=7)
        )

        is_expired = InvitationService.is_invitation_expired(invitation)
        self.assertFalse(is_expired)

    def test_is_invitation_expired_expired(self):
        """Test checking if invitation is expired."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            link_expires_at=timezone.now() - timedelta(days=1)
        )

        is_expired = InvitationService.is_invitation_expired(invitation)
        self.assertTrue(is_expired)

    def test_is_invitation_expired_no_expiry(self):
        """Test invitation with no expiry date."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            link_expires_at=None
        )

        is_expired = InvitationService.is_invitation_expired(invitation)
        self.assertFalse(is_expired)

    def test_extend_invitation_expiry(self):
        """Test extending invitation expiry."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=1)
        )

        original_expiry = invitation.link_expires_at
        success, error = InvitationService.extend_invitation_expiry(invitation, days=10)

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertGreater(invitation.link_expires_at, original_expiry)

    def test_increment_view_count(self):
        """Test incrementing invitation view count."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            total_views=0
        )

        success, error = InvitationService.increment_view_count(invitation)

        self.assertTrue(success)
        invitation.refresh_from_db()
        self.assertEqual(invitation.total_views, 1)

    def test_get_invitation_summary(self):
        """Test getting invitation summary."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=7)
        )

        summary = InvitationService.get_invitation_summary(invitation)

        self.assertEqual(summary['title'], 'Test Invitation')
        self.assertEqual(summary['slug'], invitation.slug)
        self.assertTrue(summary['is_active'])
        self.assertIn('order', summary)
        self.assertIn('template', summary)

    def test_generate_invitation_url(self):
        """Test generating invitation URL."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message',
            slug='test-slug-123'
        )

        url = InvitationService.generate_invitation_url(invitation)
        self.assertIn('test-slug-123', url)

    def test_get_active_invitations(self):
        """Test getting active invitations."""
        # Create active invitation
        Invitation.objects.create(
            order=self.order,
            title='Active Invitation',
            message='Test',
            is_active=True,
            link_expires_at=timezone.now() + timedelta(days=7)
        )

        # Create inactive invitation
        order2 = Order.objects.create(
            user=self.user,
            plan=self.plan,
            template=self.template,
            occasion='Event',
            payment_amount=Decimal('499.00'),
            status='APPROVED'
        )
        Invitation.objects.create(
            order=order2,
            title='Inactive Invitation',
            message='Test',
            is_active=False
        )

        active = InvitationService.get_active_invitations(self.user)
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().title, 'Active Invitation')

    def test_get_expired_invitations(self):
        """Test getting expired invitations."""
        # Create expired invitation
        Invitation.objects.create(
            order=self.order,
            title='Expired Invitation',
            message='Test',
            is_active=True,
            link_expires_at=timezone.now() - timedelta(days=1)
        )

        expired = InvitationService.get_expired_invitations()
        self.assertEqual(expired.count(), 1)

    def test_can_user_edit_invitation_owner(self):
        """Test owner can edit their invitation."""
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message'
        )

        can_edit = InvitationService.can_user_edit_invitation(self.user, invitation)
        self.assertTrue(can_edit)

    def test_can_user_edit_invitation_not_owner(self):
        """Test non-owner cannot edit invitation."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            full_name='Other User'
        )
        invitation = Invitation.objects.create(
            order=self.order,
            title='Test Invitation',
            message='Test message'
        )

        can_edit = InvitationService.can_user_edit_invitation(other_user, invitation)
        self.assertFalse(can_edit)
