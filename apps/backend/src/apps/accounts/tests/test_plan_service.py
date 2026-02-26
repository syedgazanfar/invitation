"""
Unit tests for PlanService (accounts app).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from apps.accounts.services import PlanService
from apps.plans.models import Plan

User = get_user_model()


class AccountsPlanServiceTest(TestCase):
    """Test cases for PlanService in accounts app."""

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
        self.luxury_plan = Plan.objects.create(
            code='LUXURY',
            name='Luxury Plan',
            price=999.00,
            is_active=True
        )

    def test_assign_plan_to_user(self):
        """Test assigning plan to user."""
        success, error = PlanService.assign_plan_to_user(
            user=self.user,
            plan=self.premium_plan,
            duration_days=30
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.premium_plan)
        self.assertIsNotNone(self.user.plan_start_date)
        self.assertIsNotNone(self.user.plan_end_date)

    def test_assign_plan_with_custom_dates(self):
        """Test assigning plan with custom start and end dates."""
        start_date = timezone.now().date()
        end_date = (timezone.now() + timedelta(days=60)).date()

        success, error = PlanService.assign_plan_to_user(
            user=self.user,
            plan=self.premium_plan,
            start_date=start_date,
            end_date=end_date
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.plan_start_date, start_date)
        self.assertEqual(self.user.plan_end_date, end_date)

    def test_upgrade_user_plan(self):
        """Test upgrading user plan."""
        # Assign basic plan first
        PlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # Upgrade to premium
        success, error = PlanService.upgrade_user_plan(
            user=self.user,
            new_plan=self.premium_plan
        )

        self.assertTrue(success)
        self.assertIsNone(error)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.premium_plan)

    def test_downgrade_user_plan(self):
        """Test downgrading user plan."""
        # Assign premium plan first
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        # Downgrade to basic
        success, error = PlanService.downgrade_user_plan(
            user=self.user,
            new_plan=self.basic_plan
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.basic_plan)

    def test_extend_plan_duration(self):
        """Test extending plan duration."""
        # Assign plan with 30 days
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        original_end_date = self.user.plan_end_date

        # Extend by 30 more days
        success, error = PlanService.extend_plan_duration(
            user=self.user,
            additional_days=30
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertGreater(self.user.plan_end_date, original_end_date)

    def test_revoke_user_plan(self):
        """Test revoking user plan."""
        # Assign plan first
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        success, error = PlanService.revoke_user_plan(self.user)

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.current_plan)
        self.assertIsNone(self.user.plan_start_date)
        self.assertIsNone(self.user.plan_end_date)

    def test_is_plan_active(self):
        """Test checking if plan is active."""
        # No plan assigned
        self.assertFalse(PlanService.is_plan_active(self.user))

        # Assign active plan
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )
        self.assertTrue(PlanService.is_plan_active(self.user))

    def test_is_plan_expired(self):
        """Test checking if plan is expired."""
        # Assign plan with past end date
        past_end_date = (timezone.now() - timedelta(days=1)).date()
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=1
        )
        self.user.plan_end_date = past_end_date
        self.user.save()

        self.assertTrue(PlanService.is_plan_expired(self.user))

    def test_get_plan_days_remaining(self):
        """Test getting days remaining in plan."""
        # Assign plan with 30 days
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        days_remaining = PlanService.get_plan_days_remaining(self.user)
        self.assertGreater(days_remaining, 0)
        self.assertLessEqual(days_remaining, 30)

    def test_get_plan_days_remaining_no_plan(self):
        """Test days remaining with no plan."""
        days_remaining = PlanService.get_plan_days_remaining(self.user)
        self.assertEqual(days_remaining, 0)

    def test_get_user_plan_history(self):
        """Test getting user plan history."""
        # Assign and change plans
        PlanService.assign_plan_to_user(self.user, self.basic_plan, duration_days=30)
        PlanService.assign_plan_to_user(self.user, self.premium_plan, duration_days=30)

        history = PlanService.get_user_plan_history(self.user)

        self.assertIsInstance(history, list)
        # Should have records of plan changes

    def test_get_plan_summary(self):
        """Test getting plan summary."""
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        summary = PlanService.get_plan_summary(self.user)

        self.assertIn('current_plan', summary)
        self.assertIn('is_active', summary)
        self.assertIn('days_remaining', summary)
        self.assertEqual(summary['current_plan']['code'], 'PREMIUM')

    def test_can_user_access_feature(self):
        """Test checking if user can access plan feature."""
        # User with basic plan
        PlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # Define feature requirements
        can_access = PlanService.can_user_access_feature(
            user=self.user,
            required_plan='BASIC'
        )
        self.assertTrue(can_access)

        can_access = PlanService.can_user_access_feature(
            user=self.user,
            required_plan='PREMIUM'
        )
        self.assertFalse(can_access)

    def test_get_available_upgrades(self):
        """Test getting available plan upgrades."""
        # User with basic plan
        PlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        upgrades = PlanService.get_available_upgrades(self.user)

        self.assertIsInstance(upgrades, list)
        # Should include premium and luxury plans
        upgrade_codes = [plan['code'] for plan in upgrades]
        self.assertIn('PREMIUM', upgrade_codes)
        self.assertIn('LUXURY', upgrade_codes)

    def test_calculate_upgrade_cost(self):
        """Test calculating upgrade cost."""
        # User with basic plan
        PlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=15
        )

        cost = PlanService.calculate_upgrade_cost(
            user=self.user,
            new_plan=self.premium_plan
        )

        self.assertIsInstance(cost, dict)
        self.assertIn('upgrade_cost', cost)
        self.assertIn('proration', cost)

    def test_schedule_plan_cancellation(self):
        """Test scheduling plan cancellation."""
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        success, error = PlanService.schedule_plan_cancellation(
            user=self.user,
            cancellation_date=(timezone.now() + timedelta(days=30)).date()
        )

        self.assertTrue(success)
        self.assertIsNone(error)

    def test_cancel_scheduled_cancellation(self):
        """Test cancelling scheduled plan cancellation."""
        PlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )
        PlanService.schedule_plan_cancellation(
            self.user,
            (timezone.now() + timedelta(days=30)).date()
        )

        success, error = PlanService.cancel_scheduled_cancellation(self.user)

        self.assertTrue(success)
        self.assertIsNone(error)
