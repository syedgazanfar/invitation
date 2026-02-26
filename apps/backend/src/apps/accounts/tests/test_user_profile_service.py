"""
Unit tests for UserProfileService.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.accounts.services import UserProfileService

User = get_user_model()


class UserProfileServiceTest(TestCase):
    """Test cases for UserProfileService."""

    def setUp(self):
        """Set up test data."""
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User',
            phone='+911234567890'
        )

    def test_get_user_profile(self):
        """Test getting user profile."""
        profile = UserProfileService.get_user_profile(self.user)

        self.assertEqual(profile['email'], 'test@example.com')
        self.assertEqual(profile['full_name'], 'Test User')
        self.assertEqual(profile['phone'], '+911234567890')
        self.assertIn('is_verified', profile)
        self.assertIn('is_active', profile)

    def test_update_profile_success(self):
        """Test updating profile successfully."""
        success, error = UserProfileService.update_profile(
            user=self.user,
            full_name='Updated Name',
            phone='+919876543210'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')
        self.assertEqual(self.user.phone, '+919876543210')

    def test_update_profile_partial(self):
        """Test partial profile update."""
        success, error = UserProfileService.update_profile(
            user=self.user,
            full_name='New Name'
            # Phone not provided
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'New Name')
        self.assertEqual(self.user.phone, '+911234567890')  # Unchanged

    def test_update_email_success(self):
        """Test updating email successfully."""
        success, error = UserProfileService.update_email(
            user=self.user,
            new_email='newemail@example.com'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')
        # Email verification should be reset
        self.assertFalse(self.user.is_verified)

    def test_update_email_duplicate(self):
        """Test updating to duplicate email."""
        # Create another user
        User.objects.create_user(
            email='existing@example.com',
            password='testpass123',
            full_name='Existing User'
        )

        success, error = UserProfileService.update_email(
            user=self.user,
            new_email='existing@example.com'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertIn('already exists', error.lower())

    def test_update_email_invalid_format(self):
        """Test updating with invalid email format."""
        success, error = UserProfileService.update_email(
            user=self.user,
            new_email='invalid-email'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_update_phone_success(self):
        """Test updating phone successfully."""
        success, error = UserProfileService.update_phone(
            user=self.user,
            new_phone='+919876543210'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, '+919876543210')
        self.assertFalse(self.user.is_phone_verified)

    def test_get_profile_completion_percentage(self):
        """Test calculating profile completion percentage."""
        # User with all fields
        percentage = UserProfileService.get_profile_completion_percentage(self.user)
        self.assertGreater(percentage, 0)
        self.assertLessEqual(percentage, 100)

    def test_get_profile_completion_percentage_incomplete(self):
        """Test profile completion with missing fields."""
        user = User.objects.create_user(
            email='incomplete@example.com',
            password='testpass123',
            full_name=''  # Missing name
        )

        percentage = UserProfileService.get_profile_completion_percentage(user)
        self.assertLess(percentage, 100)

    def test_is_profile_complete(self):
        """Test checking if profile is complete."""
        is_complete, missing_fields = UserProfileService.is_profile_complete(self.user)

        # Profile should be complete with all required fields
        self.assertTrue(is_complete)
        self.assertEqual(len(missing_fields), 0)

    def test_is_profile_complete_missing_fields(self):
        """Test checking incomplete profile."""
        user = User.objects.create_user(
            email='incomplete@example.com',
            password='testpass123',
            full_name='',
            phone=''
        )

        is_complete, missing_fields = UserProfileService.is_profile_complete(user)

        self.assertFalse(is_complete)
        self.assertGreater(len(missing_fields), 0)

    def test_get_account_summary(self):
        """Test getting account summary."""
        summary = UserProfileService.get_account_summary(self.user)

        self.assertIn('profile', summary)
        self.assertIn('security', summary)
        self.assertIn('subscription', summary)
        self.assertEqual(summary['profile']['email'], 'test@example.com')

    def test_delete_account(self):
        """Test deleting user account."""
        user_id = self.user.id

        success, error = UserProfileService.delete_account(
            self.user,
            password='testpass123'
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.assertFalse(User.objects.filter(id=user_id).exists())

    def test_delete_account_wrong_password(self):
        """Test deleting account with wrong password."""
        success, error = UserProfileService.delete_account(
            self.user,
            password='wrongpassword'
        )

        self.assertFalse(success)
        self.assertIsNotNone(error)
        self.assertTrue(User.objects.filter(id=self.user.id).exists())

    def test_export_user_data(self):
        """Test exporting user data."""
        data = UserProfileService.export_user_data(self.user)

        self.assertIn('profile', data)
        self.assertIn('account_info', data)
        self.assertEqual(data['profile']['email'], 'test@example.com')

    def test_update_preferences(self):
        """Test updating user preferences."""
        preferences = {
            'email_notifications': True,
            'sms_notifications': False,
            'language': 'en'
        }

        success, error = UserProfileService.update_preferences(
            self.user,
            preferences
        )

        self.assertTrue(success)
        self.assertIsNone(error)

    def test_get_user_statistics(self):
        """Test getting user statistics."""
        stats = UserProfileService.get_user_statistics(self.user)

        self.assertIn('total_orders', stats)
        self.assertIn('total_invitations', stats)
        self.assertIn('account_age_days', stats)
