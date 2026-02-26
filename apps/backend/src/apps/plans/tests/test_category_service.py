"""
Unit tests for CategoryService.
"""
from django.test import TestCase
from apps.plans.models import InvitationCategory, Template, Plan
from apps.plans.services import CategoryService


class CategoryServiceTest(TestCase):
    """Test cases for CategoryService."""

    def setUp(self):
        """Set up test data."""
        # Create test categories
        self.wedding_category = InvitationCategory.objects.create(
            code='WEDDING',
            name='Wedding',
            description='Wedding invitations',
            icon='favorite',
            sort_order=1,
            is_active=True
        )
        self.birthday_category = InvitationCategory.objects.create(
            code='BIRTHDAY',
            name='Birthday',
            description='Birthday invitations',
            icon='cake',
            sort_order=2,
            is_active=True
        )
        self.anniversary_category = InvitationCategory.objects.create(
            code='ANNIVERSARY',
            name='Anniversary',
            description='Anniversary invitations',
            icon='celebration',
            sort_order=3,
            is_active=True
        )
        # Create inactive category
        self.inactive_category = InvitationCategory.objects.create(
            code='INACTIVE',
            name='Inactive Category',
            description='Inactive',
            is_active=False
        )

        # Create a plan for templates
        self.plan = Plan.objects.create(
            code='BASIC',
            name='Basic Plan',
            price=0.00,
            is_active=True
        )

        # Create templates for categories
        for i in range(3):
            Template.objects.create(
                name=f'Wedding Template {i}',
                description='Test template',
                plan=self.plan,
                category=self.wedding_category,
                animation_type='elegant',
                use_count=10 * (i + 1),
                is_active=True
            )

        for i in range(2):
            Template.objects.create(
                name=f'Birthday Template {i}',
                description='Test template',
                plan=self.plan,
                category=self.birthday_category,
                animation_type='fun',
                use_count=5 * (i + 1),
                is_active=True
            )

    def test_get_all_categories(self):
        """Test getting all active categories."""
        categories = CategoryService.get_all_categories()
        self.assertEqual(len(categories), 3)
        # Should be ordered by sort_order
        self.assertEqual(categories[0].code, 'WEDDING')
        self.assertEqual(categories[1].code, 'BIRTHDAY')
        self.assertEqual(categories[2].code, 'ANNIVERSARY')

    def test_get_all_categories_excludes_inactive(self):
        """Test that inactive categories are excluded."""
        categories = CategoryService.get_all_categories()
        codes = [cat.code for cat in categories]
        self.assertNotIn('INACTIVE', codes)

    def test_get_category_by_code_success(self):
        """Test getting category by code successfully."""
        success, category, error = CategoryService.get_category_by_code('WEDDING')
        self.assertTrue(success)
        self.assertIsNotNone(category)
        self.assertIsNone(error)
        self.assertEqual(category.code, 'WEDDING')

    def test_get_category_by_code_not_found(self):
        """Test getting non-existent category."""
        success, category, error = CategoryService.get_category_by_code('INVALID')
        self.assertFalse(success)
        self.assertIsNone(category)
        self.assertIsNotNone(error)
        self.assertIn('not found', error.lower())

    def test_get_category_by_code_case_insensitive(self):
        """Test category code lookup is case insensitive."""
        success, category, error = CategoryService.get_category_by_code('wedding')
        self.assertTrue(success)
        self.assertEqual(category.code, 'WEDDING')

    def test_get_templates_count_by_category(self):
        """Test getting template counts by category."""
        counts = CategoryService.get_templates_count_by_category()

        self.assertIn('WEDDING', counts)
        self.assertEqual(counts['WEDDING']['count'], 3)
        self.assertEqual(counts['WEDDING']['name'], 'Wedding')

        self.assertIn('BIRTHDAY', counts)
        self.assertEqual(counts['BIRTHDAY']['count'], 2)

    def test_get_popular_categories(self):
        """Test getting popular categories by usage."""
        popular = CategoryService.get_popular_categories(limit=2)
        self.assertEqual(len(popular), 2)

        # Wedding should be first (total usage: 10+20+30=60)
        self.assertEqual(popular[0]['code'], 'WEDDING')
        self.assertEqual(popular[0]['template_count'], 3)
        self.assertEqual(popular[0]['total_usage'], 60)

        # Birthday should be second (total usage: 5+10=15)
        self.assertEqual(popular[1]['code'], 'BIRTHDAY')
        self.assertEqual(popular[1]['template_count'], 2)
        self.assertEqual(popular[1]['total_usage'], 15)

    def test_get_popular_categories_default_limit(self):
        """Test getting popular categories with default limit."""
        popular = CategoryService.get_popular_categories()
        self.assertLessEqual(len(popular), 5)

    def test_get_category_summary(self):
        """Test getting category summary."""
        summary = CategoryService.get_category_summary(self.wedding_category)

        self.assertEqual(summary['code'], 'WEDDING')
        self.assertEqual(summary['name'], 'Wedding')
        self.assertEqual(summary['description'], 'Wedding invitations')
        self.assertEqual(summary['icon'], 'favorite')
        self.assertEqual(summary['template_count'], 3)
        self.assertEqual(summary['sort_order'], 1)
        self.assertTrue(summary['is_active'])

    def test_get_categories_with_template_counts(self):
        """Test getting categories with template counts."""
        categories = CategoryService.get_categories_with_template_counts()

        self.assertEqual(len(categories), 3)

        # Find wedding category
        wedding = next(cat for cat in categories if cat['code'] == 'WEDDING')
        self.assertEqual(wedding['template_count'], 3)
        self.assertEqual(wedding['icon'], 'favorite')

        # Find birthday category
        birthday = next(cat for cat in categories if cat['code'] == 'BIRTHDAY')
        self.assertEqual(birthday['template_count'], 2)

        # Anniversary should have 0 templates
        anniversary = next(cat for cat in categories if cat['code'] == 'ANNIVERSARY')
        self.assertEqual(anniversary['template_count'], 0)

    def test_search_categories_by_name(self):
        """Test searching categories by name."""
        results = CategoryService.search_categories('Wedding')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].code, 'WEDDING')

    def test_search_categories_by_description(self):
        """Test searching categories by description."""
        results = CategoryService.search_categories('birthday')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].code, 'BIRTHDAY')

    def test_search_categories_partial_match(self):
        """Test searching categories with partial match."""
        results = CategoryService.search_categories('day')
        # Should match "Birthday" and "Anniversary"
        self.assertEqual(len(results), 2)
        codes = [cat.code for cat in results]
        self.assertIn('BIRTHDAY', codes)
        self.assertIn('ANNIVERSARY', codes)

    def test_search_categories_no_results(self):
        """Test searching categories with no matches."""
        results = CategoryService.search_categories('nonexistent')
        self.assertEqual(len(results), 0)

    def test_validate_category_code_valid(self):
        """Test validating valid category code."""
        is_valid, error = CategoryService.validate_category_code('WEDDING')
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_validate_category_code_invalid(self):
        """Test validating invalid category code."""
        is_valid, error = CategoryService.validate_category_code('INVALID')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('not available', error)

    def test_validate_category_code_empty(self):
        """Test validating empty category code."""
        is_valid, error = CategoryService.validate_category_code('')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('required', error)

    def test_validate_category_code_inactive(self):
        """Test validating inactive category code."""
        is_valid, error = CategoryService.validate_category_code('INACTIVE')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)

    def test_category_ordering_by_sort_order(self):
        """Test categories are ordered by sort_order."""
        categories = CategoryService.get_all_categories()
        sort_orders = [cat.sort_order for cat in categories]
        self.assertEqual(sort_orders, sorted(sort_orders))
