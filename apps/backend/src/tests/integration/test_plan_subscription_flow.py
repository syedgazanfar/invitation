"""
Integration tests for plan subscription and management flow.

This tests the complete workflow:
1. User starts with no plan
2. User subscribes to a plan
3. User creates orders based on plan
4. User upgrades/downgrades plan
5. Plan expiry and renewal
6. Access control based on plan tier
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.plans.models import Plan, Template, InvitationCategory
from apps.invitations.models import Order
from apps.invitations.services import OrderService
from apps.accounts.services import PlanService as AccountsPlanService
from apps.plans.services import PlanService, TemplateService

User = get_user_model()


class PlanSubscriptionFlowIntegrationTest(TransactionTestCase):
    """Integration tests for plan subscription and management."""

    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            email='subscriber@example.com',
            password='testpass123',
            full_name='Subscriber User'
        )

        # Create plans
        self.basic_plan = Plan.objects.create(
            code='BASIC',
            name='Basic Plan',
            description='Basic features',
            price=0.00,
            is_active=True
        )

        self.premium_plan = Plan.objects.create(
            code='PREMIUM',
            name='Premium Plan',
            description='Premium features',
            price=499.00,
            is_active=True
        )

        self.luxury_plan = Plan.objects.create(
            code='LUXURY',
            name='Luxury Plan',
            description='All features',
            price=999.00,
            is_active=True
        )

        # Create category
        self.category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            is_active=True
        )

        # Create templates for each plan
        self.basic_template = Template.objects.create(
            name='Basic Template',
            description='Simple template',
            plan=self.basic_plan,
            category=self.category,
            animation_type='simple',
            is_active=True
        )

        self.premium_template = Template.objects.create(
            name='Premium Template',
            description='Premium template',
            plan=self.premium_plan,
            category=self.category,
            animation_type='elegant',
            is_premium=True,
            is_active=True
        )

        self.luxury_template = Template.objects.create(
            name='Luxury Template',
            description='Luxury template',
            plan=self.luxury_plan,
            category=self.category,
            animation_type='luxury',
            is_premium=True,
            is_active=True
        )

    def test_complete_subscription_lifecycle(self):
        """Test complete plan subscription lifecycle."""

        # Phase 1: User starts with no plan
        self.assertIsNone(self.user.current_plan)

        # Phase 2: User subscribes to BASIC plan
        success, error = AccountsPlanService.assign_plan_to_user(
            user=self.user,
            plan=self.basic_plan,
            duration_days=30
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.basic_plan)

        # Check plan is active
        is_active = AccountsPlanService.is_plan_active(self.user)
        self.assertTrue(is_active)

        # Phase 3: User can only access BASIC templates
        accessible_templates = PlanService.get_accessible_plans('BASIC')
        self.assertEqual(accessible_templates, ['BASIC'])

        success, templates, error = TemplateService.get_templates_by_plan('BASIC')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 1)

        # Phase 4: User upgrades to PREMIUM
        success, error = AccountsPlanService.upgrade_user_plan(
            user=self.user,
            new_plan=self.premium_plan
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.premium_plan)

        # Phase 5: User can now access BASIC + PREMIUM templates
        accessible_plans = PlanService.get_accessible_plans('PREMIUM')
        self.assertIn('BASIC', accessible_plans)
        self.assertIn('PREMIUM', accessible_plans)

        success, templates, error = TemplateService.get_templates_by_plan('PREMIUM')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 2)  # BASIC + PREMIUM

        # Phase 6: User upgrades to LUXURY
        success, error = AccountsPlanService.upgrade_user_plan(
            user=self.user,
            new_plan=self.luxury_plan
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.luxury_plan)

        # Phase 7: User can access all templates
        success, templates, error = TemplateService.get_templates_by_plan('LUXURY')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 3)  # All templates

    def test_plan_access_control(self):
        """Test access control based on plan tier."""

        # Assign BASIC plan
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # BASIC user can access BASIC template
        can_access = TemplateService.can_user_access_template(
            'BASIC',
            self.basic_template
        )
        self.assertTrue(can_access)

        # BASIC user cannot access PREMIUM template
        can_access = TemplateService.can_user_access_template(
            'BASIC',
            self.premium_template
        )
        self.assertFalse(can_access)

        # Upgrade to PREMIUM
        AccountsPlanService.upgrade_user_plan(
            self.user,
            self.premium_plan
        )

        # PREMIUM user can access both BASIC and PREMIUM
        can_access_basic = TemplateService.can_user_access_template(
            'PREMIUM',
            self.basic_template
        )
        can_access_premium = TemplateService.can_user_access_template(
            'PREMIUM',
            self.premium_template
        )

        self.assertTrue(can_access_basic)
        self.assertTrue(can_access_premium)

    def test_order_creation_with_plan_restriction(self):
        """Test order creation respects plan restrictions."""

        # Assign BASIC plan to user
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # User with BASIC plan tries to order PREMIUM plan
        can_order, error = OrderService.can_user_order_plan(
            self.user,
            'PREMIUM'
        )

        self.assertFalse(can_order)
        self.assertIsNotNone(error)

        # User can reorder their current plan
        can_order, error = OrderService.can_user_order_plan(
            self.user,
            'BASIC'
        )

        self.assertTrue(can_order)

    def test_plan_expiry_and_renewal(self):
        """Test plan expiry and renewal flow."""

        # Assign plan with short duration
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        # Check days remaining
        days_remaining = AccountsPlanService.get_plan_days_remaining(self.user)
        self.assertGreater(days_remaining, 0)
        self.assertLessEqual(days_remaining, 30)

        # Simulate near expiry (set end date to past)
        self.user.plan_end_date = (timezone.now() - timedelta(days=1)).date()
        self.user.save()

        # Check if expired
        is_expired = AccountsPlanService.is_plan_expired(self.user)
        self.assertTrue(is_expired)

        # Renew plan
        success, error = AccountsPlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        self.assertTrue(success)
        is_expired = AccountsPlanService.is_plan_expired(self.user)
        self.assertFalse(is_expired)

    def test_plan_extension_flow(self):
        """Test extending plan duration."""

        # Assign plan
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=15
        )

        original_end_date = self.user.plan_end_date

        # Extend by 30 days
        success, error = AccountsPlanService.extend_plan_duration(
            self.user,
            additional_days=30
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertGreater(self.user.plan_end_date, original_end_date)

    def test_plan_downgrade_flow(self):
        """Test downgrading plan."""

        # Start with LUXURY
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.luxury_plan,
            duration_days=30
        )

        # Can access all templates
        success, templates, error = TemplateService.get_templates_by_plan('LUXURY')
        self.assertEqual(templates.count(), 3)

        # Downgrade to PREMIUM
        success, error = AccountsPlanService.downgrade_user_plan(
            self.user,
            self.premium_plan
        )

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.premium_plan)

        # Can only access BASIC + PREMIUM templates
        success, templates, error = TemplateService.get_templates_by_plan('PREMIUM')
        self.assertEqual(templates.count(), 2)

    def test_plan_comparison(self):
        """Test plan comparison functionality."""

        comparison = PlanService.compare_plans()

        self.assertEqual(len(comparison), 3)

        # Check hierarchy
        basic_tier = next(p['tier'] for p in comparison if p['code'] == 'BASIC')
        premium_tier = next(p['tier'] for p in comparison if p['code'] == 'PREMIUM')
        luxury_tier = next(p['tier'] for p in comparison if p['code'] == 'LUXURY')

        self.assertEqual(basic_tier, 1)
        self.assertEqual(premium_tier, 2)
        self.assertEqual(luxury_tier, 3)

    def test_upgrade_path_calculation(self):
        """Test calculating available upgrade paths."""

        # From BASIC
        upgrades = PlanService.get_upgrade_path('BASIC')
        self.assertEqual(len(upgrades), 2)
        upgrade_codes = [u['code'] for u in upgrades]
        self.assertIn('PREMIUM', upgrade_codes)
        self.assertIn('LUXURY', upgrade_codes)

        # From PREMIUM
        upgrades = PlanService.get_upgrade_path('PREMIUM')
        self.assertEqual(len(upgrades), 1)
        self.assertEqual(upgrades[0]['code'], 'LUXURY')

        # From LUXURY (no upgrades)
        upgrades = PlanService.get_upgrade_path('LUXURY')
        self.assertEqual(len(upgrades), 0)

    def test_template_filtering_by_plan_hierarchy(self):
        """Test template filtering respects plan hierarchy."""

        # BASIC user sees only BASIC templates
        success, templates, error = TemplateService.get_templates_by_plan('BASIC')
        self.assertTrue(success)
        template_plans = [t.plan.code for t in templates]
        self.assertEqual(template_plans, ['BASIC'])

        # PREMIUM user sees BASIC + PREMIUM
        success, templates, error = TemplateService.get_templates_by_plan('PREMIUM')
        self.assertTrue(success)
        template_plans = [t.plan.code for t in templates]
        self.assertIn('BASIC', template_plans)
        self.assertIn('PREMIUM', template_plans)
        self.assertNotIn('LUXURY', template_plans)

        # LUXURY user sees all
        success, templates, error = TemplateService.get_templates_by_plan('LUXURY')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 3)

    def test_plan_feature_access(self):
        """Test feature access based on plan."""

        # Assign BASIC plan
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # Check feature access
        can_access_basic = AccountsPlanService.can_user_access_feature(
            self.user,
            required_plan='BASIC'
        )
        self.assertTrue(can_access_basic)

        can_access_premium = AccountsPlanService.can_user_access_feature(
            self.user,
            required_plan='PREMIUM'
        )
        self.assertFalse(can_access_premium)

    def test_multiple_plan_changes(self):
        """Test user changing plans multiple times."""

        # Start with BASIC
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.basic_plan,
            duration_days=30
        )

        # Upgrade to PREMIUM
        AccountsPlanService.upgrade_user_plan(
            self.user,
            self.premium_plan
        )

        # Upgrade to LUXURY
        AccountsPlanService.upgrade_user_plan(
            self.user,
            self.luxury_plan
        )

        # Downgrade to PREMIUM
        AccountsPlanService.downgrade_user_plan(
            self.user,
            self.premium_plan
        )

        # Check final state
        self.user.refresh_from_db()
        self.assertEqual(self.user.current_plan, self.premium_plan)

        # Get plan history
        history = AccountsPlanService.get_user_plan_history(self.user)
        self.assertIsInstance(history, list)

    def test_plan_summary_and_analytics(self):
        """Test plan summary and analytics."""

        # Assign plan
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        # Get plan summary
        summary = AccountsPlanService.get_plan_summary(self.user)

        self.assertIn('current_plan', summary)
        self.assertIn('is_active', summary)
        self.assertIn('days_remaining', summary)
        self.assertEqual(summary['current_plan']['code'], 'PREMIUM')
        self.assertTrue(summary['is_active'])

    def test_premium_template_access(self):
        """Test premium template access based on plan."""

        # Get premium templates for BASIC user
        premium_templates = TemplateService.get_premium_templates('BASIC')
        self.assertEqual(premium_templates.count(), 0)

        # Get premium templates for PREMIUM user
        premium_templates = TemplateService.get_premium_templates('PREMIUM')
        self.assertGreater(premium_templates.count(), 0)

        # Get premium templates for LUXURY user
        premium_templates = TemplateService.get_premium_templates('LUXURY')
        self.assertEqual(premium_templates.count(), 2)  # PREMIUM + LUXURY

    def test_plan_revocation_flow(self):
        """Test revoking user plan."""

        # Assign plan
        AccountsPlanService.assign_plan_to_user(
            self.user,
            self.premium_plan,
            duration_days=30
        )

        self.assertIsNotNone(self.user.current_plan)

        # Revoke plan
        success, error = AccountsPlanService.revoke_user_plan(self.user)

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.current_plan)
        self.assertIsNone(self.user.plan_start_date)
        self.assertIsNone(self.user.plan_end_date)
