"""
Unit tests for PlanService.
"""
from django.test import TestCase
from apps.plans.models import Plan
from apps.plans.services import PlanService


class PlanServiceTest(TestCase):
    """Test cases for PlanService."""

    def setUp(self):
        """Set up test data."""
        # Create test plans
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

    def test_get_all_active_plans(self):
        """Test getting all active plans."""
        plans = PlanService.get_all_active_plans()
        self.assertEqual(len(plans), 3)
        self.assertEqual(plans[0].code, 'BASIC')

    def test_get_plan_by_code_success(self):
        """Test getting plan by code successfully."""
        success, plan, error = PlanService.get_plan_by_code('PREMIUM')
        self.assertTrue(success)
        self.assertIsNotNone(plan)
        self.assertIsNone(error)
        self.assertEqual(plan.code, 'PREMIUM')

    def test_get_plan_by_code_not_found(self):
        """Test getting non-existent plan."""
        success, plan, error = PlanService.get_plan_by_code('INVALID')
        self.assertFalse(success)
        self.assertIsNone(plan)
        self.assertIsNotNone(error)
        self.assertIn('not found', error.lower())

    def test_get_plan_by_id_success(self):
        """Test getting plan by ID successfully."""
        success, plan, error = PlanService.get_plan_by_id(str(self.premium_plan.id))
        self.assertTrue(success)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.code, 'PREMIUM')

    def test_plan_hierarchy(self):
        """Test plan hierarchy mapping."""
        hierarchy = PlanService.get_plan_hierarchy()
        self.assertEqual(hierarchy['BASIC'], 1)
        self.assertEqual(hierarchy['PREMIUM'], 2)
        self.assertEqual(hierarchy['LUXURY'], 3)

    def test_can_access_plan_basic_user(self):
        """Test BASIC user can only access BASIC plan."""
        # BASIC user accessing BASIC plan
        self.assertTrue(PlanService.can_access_plan('BASIC', 'BASIC'))
        # BASIC user accessing PREMIUM plan
        self.assertFalse(PlanService.can_access_plan('BASIC', 'PREMIUM'))
        # BASIC user accessing LUXURY plan
        self.assertFalse(PlanService.can_access_plan('BASIC', 'LUXURY'))

    def test_can_access_plan_premium_user(self):
        """Test PREMIUM user can access BASIC and PREMIUM plans."""
        # PREMIUM user accessing BASIC plan
        self.assertTrue(PlanService.can_access_plan('PREMIUM', 'BASIC'))
        # PREMIUM user accessing PREMIUM plan
        self.assertTrue(PlanService.can_access_plan('PREMIUM', 'PREMIUM'))
        # PREMIUM user accessing LUXURY plan
        self.assertFalse(PlanService.can_access_plan('PREMIUM', 'LUXURY'))

    def test_can_access_plan_luxury_user(self):
        """Test LUXURY user can access all plans."""
        # LUXURY user accessing BASIC plan
        self.assertTrue(PlanService.can_access_plan('LUXURY', 'BASIC'))
        # LUXURY user accessing PREMIUM plan
        self.assertTrue(PlanService.can_access_plan('LUXURY', 'PREMIUM'))
        # LUXURY user accessing LUXURY plan
        self.assertTrue(PlanService.can_access_plan('LUXURY', 'LUXURY'))

    def test_get_accessible_plans_basic(self):
        """Test getting accessible plans for BASIC user."""
        accessible = PlanService.get_accessible_plans('BASIC')
        self.assertEqual(accessible, ['BASIC'])

    def test_get_accessible_plans_premium(self):
        """Test getting accessible plans for PREMIUM user."""
        accessible = PlanService.get_accessible_plans('PREMIUM')
        self.assertEqual(set(accessible), {'BASIC', 'PREMIUM'})

    def test_get_accessible_plans_luxury(self):
        """Test getting accessible plans for LUXURY user."""
        accessible = PlanService.get_accessible_plans('LUXURY')
        self.assertEqual(set(accessible), {'BASIC', 'PREMIUM', 'LUXURY'})

    def test_compare_plans(self):
        """Test plan comparison."""
        comparison = PlanService.compare_plans()
        self.assertEqual(len(comparison), 3)

        # Check BASIC plan
        basic_comparison = comparison[0]
        self.assertEqual(basic_comparison['code'], 'BASIC')
        self.assertEqual(basic_comparison['tier'], 1)

        # Check PREMIUM plan
        premium_comparison = comparison[1]
        self.assertEqual(premium_comparison['code'], 'PREMIUM')
        self.assertEqual(premium_comparison['tier'], 2)

        # Check LUXURY plan
        luxury_comparison = comparison[2]
        self.assertEqual(luxury_comparison['code'], 'LUXURY')
        self.assertEqual(luxury_comparison['tier'], 3)

    def test_get_plan_tier_name(self):
        """Test getting plan tier display name."""
        self.assertEqual(PlanService.get_plan_tier_name(1), 'Basic')
        self.assertEqual(PlanService.get_plan_tier_name(2), 'Premium')
        self.assertEqual(PlanService.get_plan_tier_name(3), 'Luxury')
        self.assertEqual(PlanService.get_plan_tier_name(99), 'Unknown')

    def test_get_upgrade_path_from_basic(self):
        """Test upgrade path from BASIC plan."""
        upgrades = PlanService.get_upgrade_path('BASIC')
        self.assertEqual(len(upgrades), 2)
        self.assertEqual(upgrades[0]['code'], 'PREMIUM')
        self.assertEqual(upgrades[1]['code'], 'LUXURY')

    def test_get_upgrade_path_from_premium(self):
        """Test upgrade path from PREMIUM plan."""
        upgrades = PlanService.get_upgrade_path('PREMIUM')
        self.assertEqual(len(upgrades), 1)
        self.assertEqual(upgrades[0]['code'], 'LUXURY')

    def test_get_upgrade_path_from_luxury(self):
        """Test upgrade path from LUXURY plan."""
        upgrades = PlanService.get_upgrade_path('LUXURY')
        self.assertEqual(len(upgrades), 0)

    def test_validate_plan_code_valid(self):
        """Test validating valid plan code."""
        is_valid, error = PlanService.validate_plan_code('PREMIUM')
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_plan_code_invalid(self):
        """Test validating invalid plan code."""
        is_valid, error = PlanService.validate_plan_code('INVALID')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_validate_plan_code_empty(self):
        """Test validating empty plan code."""
        is_valid, error = PlanService.validate_plan_code('')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_case_insensitive_plan_code(self):
        """Test plan code lookup is case insensitive."""
        # Test lowercase
        success1, plan1, _ = PlanService.get_plan_by_code('premium')
        self.assertTrue(success1)
        self.assertEqual(plan1.code, 'PREMIUM')

        # Test mixed case
        success2, plan2, _ = PlanService.get_plan_by_code('PrEmIuM')
        self.assertTrue(success2)
        self.assertEqual(plan2.code, 'PREMIUM')
