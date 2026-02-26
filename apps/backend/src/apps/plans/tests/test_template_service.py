"""
Unit tests for TemplateService.
"""
from django.test import TestCase
from apps.plans.models import Plan, Template, InvitationCategory
from apps.plans.services import TemplateService


class TemplateServiceTest(TestCase):
    """Test cases for TemplateService."""

    def setUp(self):
        """Set up test data."""
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

        # Create test category
        self.wedding_category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            description='Wedding invitations',
            is_active=True
        )
        self.birthday_category = InvitationCategory.objects.create(
            code='BIRTHDAY',
            name='Birthday',
            description='Birthday invitations',
            is_active=True
        )

        # Create test templates
        self.basic_template = Template.objects.create(
            name='Basic Wedding Template',
            description='Simple wedding template',
            plan=self.basic_plan,
            category=self.wedding_category,
            animation_type='elegant',
            use_count=10,
            is_premium=False,
            is_active=True
        )
        self.premium_template = Template.objects.create(
            name='Premium Wedding Template',
            description='Premium wedding template',
            plan=self.premium_plan,
            category=self.wedding_category,
            animation_type='elegant',
            use_count=50,
            is_premium=True,
            is_active=True
        )
        self.luxury_template = Template.objects.create(
            name='Luxury Birthday Template',
            description='Luxury birthday template',
            plan=self.luxury_plan,
            category=self.birthday_category,
            animation_type='fun',
            use_count=100,
            is_premium=True,
            is_active=True
        )

    def test_get_all_templates(self):
        """Test getting all active templates."""
        templates = TemplateService.get_all_templates()
        self.assertEqual(templates.count(), 3)

    def test_get_all_templates_with_plan_filter(self):
        """Test getting templates filtered by plan."""
        templates = TemplateService.get_all_templates(filters={'plan_code': 'BASIC'})
        self.assertEqual(templates.count(), 1)
        self.assertEqual(templates.first().plan.code, 'BASIC')

    def test_get_all_templates_with_category_filter(self):
        """Test getting templates filtered by category."""
        templates = TemplateService.get_all_templates(filters={'category_code': 'WEDDING'})
        self.assertEqual(templates.count(), 2)

    def test_get_all_templates_with_animation_filter(self):
        """Test getting templates filtered by animation type."""
        templates = TemplateService.get_all_templates(filters={'animation_type': 'elegant'})
        self.assertEqual(templates.count(), 2)

    def test_get_all_templates_with_premium_filter(self):
        """Test getting templates filtered by premium status."""
        templates = TemplateService.get_all_templates(filters={'is_premium': True})
        self.assertEqual(templates.count(), 2)

    def test_get_all_templates_with_ordering(self):
        """Test getting templates with custom ordering."""
        templates = TemplateService.get_all_templates(ordering='-use_count')
        template_list = list(templates)
        self.assertEqual(template_list[0].use_count, 100)
        self.assertEqual(template_list[-1].use_count, 10)

    def test_get_template_by_id_success(self):
        """Test getting template by ID successfully."""
        success, template, error = TemplateService.get_template_by_id(str(self.basic_template.id))
        self.assertTrue(success)
        self.assertIsNotNone(template)
        self.assertIsNone(error)
        self.assertEqual(template.name, 'Basic Wedding Template')

    def test_get_template_by_id_not_found(self):
        """Test getting non-existent template."""
        import uuid
        fake_id = str(uuid.uuid4())
        success, template, error = TemplateService.get_template_by_id(fake_id)
        self.assertFalse(success)
        self.assertIsNone(template)
        self.assertIsNotNone(error)

    def test_get_templates_by_plan_basic(self):
        """Test getting templates for BASIC plan."""
        success, templates, error = TemplateService.get_templates_by_plan('BASIC')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 1)
        self.assertEqual(templates.first().plan.code, 'BASIC')

    def test_get_templates_by_plan_premium(self):
        """Test getting templates for PREMIUM plan (includes BASIC)."""
        success, templates, error = TemplateService.get_templates_by_plan('PREMIUM')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 2)  # BASIC + PREMIUM

    def test_get_templates_by_plan_luxury(self):
        """Test getting templates for LUXURY plan (includes all)."""
        success, templates, error = TemplateService.get_templates_by_plan('LUXURY')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 3)  # BASIC + PREMIUM + LUXURY

    def test_get_templates_by_plan_with_category(self):
        """Test getting templates by plan and category."""
        success, templates, error = TemplateService.get_templates_by_plan('PREMIUM', 'WEDDING')
        self.assertTrue(success)
        self.assertEqual(templates.count(), 2)  # Both BASIC and PREMIUM wedding templates

    def test_get_templates_by_category(self):
        """Test getting templates by category."""
        templates = TemplateService.get_templates_by_category('WEDDING')
        self.assertEqual(templates.count(), 2)

    def test_get_templates_by_category_with_plan(self):
        """Test getting templates by category with plan filter."""
        templates = TemplateService.get_templates_by_category('WEDDING', 'BASIC')
        self.assertEqual(templates.count(), 1)

    def test_get_featured_templates(self):
        """Test getting featured templates."""
        featured = TemplateService.get_featured_templates(limit=2)
        self.assertEqual(len(featured), 2)
        # Should be ordered by use_count
        self.assertEqual(featured[0].use_count, 100)

    def test_increment_template_usage(self):
        """Test incrementing template usage count."""
        initial_count = self.basic_template.use_count
        success, error = TemplateService.increment_template_usage(str(self.basic_template.id))
        self.assertTrue(success)
        self.assertIsNone(error)

        # Refresh from database
        self.basic_template.refresh_from_db()
        self.assertEqual(self.basic_template.use_count, initial_count + 1)

    def test_increment_template_usage_not_found(self):
        """Test incrementing non-existent template."""
        import uuid
        fake_id = str(uuid.uuid4())
        success, error = TemplateService.increment_template_usage(fake_id)
        self.assertFalse(success)
        self.assertIsNotNone(error)

    def test_can_user_access_template_basic_user(self):
        """Test BASIC user access to templates."""
        # Can access BASIC template
        self.assertTrue(
            TemplateService.can_user_access_template('BASIC', self.basic_template)
        )
        # Cannot access PREMIUM template
        self.assertFalse(
            TemplateService.can_user_access_template('BASIC', self.premium_template)
        )
        # Cannot access LUXURY template
        self.assertFalse(
            TemplateService.can_user_access_template('BASIC', self.luxury_template)
        )

    def test_can_user_access_template_premium_user(self):
        """Test PREMIUM user access to templates."""
        # Can access BASIC template
        self.assertTrue(
            TemplateService.can_user_access_template('PREMIUM', self.basic_template)
        )
        # Can access PREMIUM template
        self.assertTrue(
            TemplateService.can_user_access_template('PREMIUM', self.premium_template)
        )
        # Cannot access LUXURY template
        self.assertFalse(
            TemplateService.can_user_access_template('PREMIUM', self.luxury_template)
        )

    def test_can_user_access_template_luxury_user(self):
        """Test LUXURY user access to templates."""
        # Can access all templates
        self.assertTrue(
            TemplateService.can_user_access_template('LUXURY', self.basic_template)
        )
        self.assertTrue(
            TemplateService.can_user_access_template('LUXURY', self.premium_template)
        )
        self.assertTrue(
            TemplateService.can_user_access_template('LUXURY', self.luxury_template)
        )

    def test_search_templates(self):
        """Test searching templates by query."""
        # Search by name
        results = TemplateService.search_templates('Wedding')
        self.assertEqual(results.count(), 2)

        # Search by description
        results = TemplateService.search_templates('birthday')
        self.assertEqual(results.count(), 1)

    def test_search_templates_with_filters(self):
        """Test searching templates with additional filters."""
        # Search with plan filter
        results = TemplateService.search_templates(
            'Wedding',
            filters={'plan_code': 'BASIC'}
        )
        self.assertEqual(results.count(), 1)

        # Search with category filter
        results = TemplateService.search_templates(
            'Template',
            filters={'category_code': 'BIRTHDAY'}
        )
        self.assertEqual(results.count(), 1)

    def test_get_template_summary(self):
        """Test getting template summary."""
        summary = TemplateService.get_template_summary(self.basic_template)

        self.assertEqual(summary['name'], 'Basic Wedding Template')
        self.assertEqual(summary['plan']['code'], 'BASIC')
        self.assertEqual(summary['category']['code'], 'WEDDING')
        self.assertEqual(summary['animation']['type'], 'elegant')
        self.assertFalse(summary['is_premium'])
        self.assertEqual(summary['use_count'], 10)

    def test_get_templates_by_animation_type(self):
        """Test getting templates by animation type."""
        templates = TemplateService.get_templates_by_animation_type('elegant')
        self.assertEqual(templates.count(), 2)

    def test_get_templates_by_animation_type_with_plan(self):
        """Test getting templates by animation type with plan filter."""
        templates = TemplateService.get_templates_by_animation_type('elegant', 'BASIC')
        self.assertEqual(templates.count(), 1)

    def test_get_premium_templates(self):
        """Test getting premium templates."""
        templates = TemplateService.get_premium_templates()
        self.assertEqual(templates.count(), 2)
        for template in templates:
            self.assertTrue(template.is_premium)

    def test_get_premium_templates_with_plan(self):
        """Test getting premium templates with plan filter."""
        templates = TemplateService.get_premium_templates('PREMIUM')
        self.assertEqual(templates.count(), 1)  # Only PREMIUM plan premium template

    def test_get_template_count_by_plan(self):
        """Test getting template counts by plan."""
        counts = TemplateService.get_template_count_by_plan()
        self.assertEqual(counts['BASIC'], 1)
        self.assertEqual(counts['PREMIUM'], 1)
        self.assertEqual(counts['LUXURY'], 1)

    def test_validate_template_access_success(self):
        """Test validating template access successfully."""
        can_access, error = TemplateService.validate_template_access(
            'BASIC',
            str(self.basic_template.id)
        )
        self.assertTrue(can_access)
        self.assertIsNone(error)

    def test_validate_template_access_denied(self):
        """Test validating template access denied."""
        can_access, error = TemplateService.validate_template_access(
            'BASIC',
            str(self.premium_template.id)
        )
        self.assertFalse(can_access)
        self.assertIsNotNone(error)
        self.assertIn('Premium', error)
