"""
Unit tests for ActivityService.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from apps.accounts.services import ActivityService
from apps.accounts.models import UserActivity

User = get_user_model()


class ActivityServiceTest(TestCase):
    """Test cases for ActivityService."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()

        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            full_name='Test User'
        )

    def test_log_activity_success(self):
        """Test logging activity successfully."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        success, activity, error = ActivityService.log_activity(
            user=self.user,
            activity_type='LOGIN',
            request=request
        )

        self.assertTrue(success)
        self.assertIsNotNone(activity)
        self.assertIsNone(error)
        self.assertEqual(activity.user, self.user)
        self.assertEqual(activity.activity_type, 'LOGIN')

    def test_log_activity_with_description(self):
        """Test logging activity with description."""
        request = self.factory.get('/')

        success, activity, error = ActivityService.log_activity(
            user=self.user,
            activity_type='PROFILE_UPDATE',
            description='Updated phone number',
            request=request
        )

        self.assertTrue(success)
        self.assertEqual(activity.description, 'Updated phone number')

    def test_log_activity_without_request(self):
        """Test logging activity without request object."""
        success, activity, error = ActivityService.log_activity(
            user=self.user,
            activity_type='SYSTEM_ACTION'
        )

        self.assertTrue(success)
        self.assertIsNotNone(activity)

    def test_get_user_activities(self):
        """Test getting user activities."""
        request = self.factory.get('/')

        # Create multiple activities
        for i in range(5):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        activities = ActivityService.get_user_activities(self.user)
        self.assertEqual(activities.count(), 5)

    def test_get_user_activities_with_limit(self):
        """Test getting user activities with limit."""
        request = self.factory.get('/')

        # Create multiple activities
        for i in range(10):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        activities = ActivityService.get_user_activities(self.user, limit=5)
        self.assertEqual(len(activities), 5)

    def test_get_user_activities_by_type(self):
        """Test getting activities filtered by type."""
        request = self.factory.get('/')

        # Create different types of activities
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGOUT', request=request)
        ActivityService.log_activity(self.user, 'PROFILE_UPDATE', request=request)

        login_activities = ActivityService.get_user_activities_by_type(
            self.user,
            'LOGIN'
        )
        self.assertEqual(login_activities.count(), 2)

    def test_get_recent_activities(self):
        """Test getting recent activities."""
        request = self.factory.get('/')

        # Create activities
        for i in range(3):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        recent = ActivityService.get_recent_activities(self.user, limit=2)
        self.assertEqual(len(recent), 2)

    def test_get_activity_summary(self):
        """Test getting activity summary."""
        request = self.factory.get('/')

        # Create various activities
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGOUT', request=request)
        ActivityService.log_activity(self.user, 'PROFILE_UPDATE', request=request)

        summary = ActivityService.get_activity_summary(self.user)

        self.assertIn('total_activities', summary)
        self.assertEqual(summary['total_activities'], 4)
        self.assertIn('by_type', summary)
        self.assertEqual(summary['by_type']['LOGIN'], 2)

    def test_get_login_history(self):
        """Test getting login history."""
        request = self.factory.get('/')

        # Create login activities
        for i in range(3):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        # Create non-login activity
        ActivityService.log_activity(
            user=self.user,
            activity_type='LOGOUT',
            request=request
        )

        login_history = ActivityService.get_login_history(self.user)
        self.assertEqual(login_history.count(), 3)

    def test_get_last_login_info(self):
        """Test getting last login information."""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0'

        ActivityService.log_activity(
            user=self.user,
            activity_type='LOGIN',
            request=request
        )

        last_login = ActivityService.get_last_login_info(self.user)

        self.assertIsNotNone(last_login)
        self.assertEqual(last_login['activity_type'], 'LOGIN')
        self.assertIn('timestamp', last_login)
        self.assertIn('ip_address', last_login)

    def test_get_last_login_info_no_login(self):
        """Test getting last login with no login history."""
        last_login = ActivityService.get_last_login_info(self.user)
        self.assertIsNone(last_login)

    def test_clear_old_activities(self):
        """Test clearing old activities."""
        from django.utils import timezone
        from datetime import timedelta

        request = self.factory.get('/')

        # Create old activity
        old_activity = ActivityService.log_activity(
            user=self.user,
            activity_type='LOGIN',
            request=request
        )[1]
        old_activity.created_at = timezone.now() - timedelta(days=100)
        old_activity.save()

        # Create recent activity
        ActivityService.log_activity(
            user=self.user,
            activity_type='LOGOUT',
            request=request
        )

        deleted_count = ActivityService.clear_old_activities(days=90)

        self.assertGreater(deleted_count, 0)
        # Recent activity should still exist
        self.assertEqual(UserActivity.objects.filter(user=self.user).count(), 1)

    def test_get_activity_count(self):
        """Test getting activity count."""
        request = self.factory.get('/')

        # Create activities
        for i in range(7):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        count = ActivityService.get_activity_count(self.user)
        self.assertEqual(count, 7)

    def test_get_activity_count_by_type(self):
        """Test getting activity count by type."""
        request = self.factory.get('/')

        # Create activities
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGOUT', request=request)

        login_count = ActivityService.get_activity_count_by_type(self.user, 'LOGIN')
        self.assertEqual(login_count, 3)

        logout_count = ActivityService.get_activity_count_by_type(self.user, 'LOGOUT')
        self.assertEqual(logout_count, 1)

    def test_get_activities_in_date_range(self):
        """Test getting activities in date range."""
        from django.utils import timezone
        from datetime import timedelta

        request = self.factory.get('/')

        # Create activities
        for i in range(5):
            ActivityService.log_activity(
                user=self.user,
                activity_type='LOGIN',
                request=request
            )

        start_date = (timezone.now() - timedelta(days=1)).date()
        end_date = (timezone.now() + timedelta(days=1)).date()

        activities = ActivityService.get_activities_in_date_range(
            user=self.user,
            start_date=start_date,
            end_date=end_date
        )

        self.assertEqual(activities.count(), 5)

    def test_export_activity_log(self):
        """Test exporting activity log."""
        request = self.factory.get('/')

        # Create activities
        ActivityService.log_activity(self.user, 'LOGIN', request=request)
        ActivityService.log_activity(self.user, 'LOGOUT', request=request)

        export_data = ActivityService.export_activity_log(self.user)

        self.assertIsNotNone(export_data)
        self.assertIn('LOGIN', export_data)
        self.assertIn('LOGOUT', export_data)

    def test_get_suspicious_activities(self):
        """Test getting suspicious activities."""
        request = self.factory.get('/')

        # Create multiple failed login attempts
        for i in range(5):
            ActivityService.log_activity(
                user=self.user,
                activity_type='FAILED_LOGIN',
                request=request
            )

        suspicious = ActivityService.get_suspicious_activities(self.user)

        self.assertGreater(suspicious.count(), 0)
