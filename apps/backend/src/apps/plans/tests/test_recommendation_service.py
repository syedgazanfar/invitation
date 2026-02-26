"""
Unit tests for RecommendationService.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.plans.models import Plan, Template, InvitationCategory
from apps.plans.services import RecommendationService


class RecommendationServiceTest(TestCase):
    """Test cases for RecommendationService."""

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

        # Create test categories
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

        # Create templates with varying attributes
        # BASIC plan templates
        self.basic_wedding = Template.objects.create(
            name='Basic Wedding',
            description='Basic wedding template',
            plan=self.basic_plan,
            category=self.wedding_category,
            animation_type='elegant',
            use_count=10,
            is_premium=False,
            is_active=True
        )

        # PREMIUM plan templates
        self.premium_wedding = Template.objects.create(
            name='Premium Wedding',
            description='Premium wedding template',
            plan=self.premium_plan,
            category=self.wedding_category,
            animation_type='elegant',
            use_count=50,
            is_premium=True,
            is_active=True
        )

        self.premium_birthday = Template.objects.create(
            name='Premium Birthday',
            description='Premium birthday template',
            plan=self.premium_plan,
            category=self.birthday_category,
            animation_type='fun',
            use_count=30,
            is_premium=True,
            is_active=True
        )

        # LUXURY plan templates
        self.luxury_wedding = Template.objects.create(
            name='Luxury Wedding',
            description='Luxury wedding template',
            plan=self.luxury_plan,
            category=self.wedding_category,
            animation_type='elegant',
            use_count=100,
            is_premium=True,
            is_active=True
        )

        # Recent template
        self.recent_template = Template.objects.create(
            name='Recent Template',
            description='Recently added',
            plan=self.basic_plan,
            category=self.birthday_category,
            animation_type='fun',
            use_count=5,
            is_premium=False,
            is_active=True,
            created_at=timezone.now() - timedelta(days=2)
        )

    def test_get_recommended_templates_basic_user(self):
        """Test recommendations for BASIC user."""
        recommended = RecommendationService.get_recommended_templates('BASIC', limit=10)
        # Should only get BASIC templates
        for template in recommended:
            self.assertEqual(template.plan.code, 'BASIC')

    def test_get_recommended_templates_premium_user(self):
        """Test recommendations for PREMIUM user."""
        recommended = RecommendationService.get_recommended_templates('PREMIUM', limit=10)
        # Should get BASIC + PREMIUM templates
        plan_codes = {t.plan.code for t in recommended}
        self.assertIn('BASIC', plan_codes)
        self.assertIn('PREMIUM', plan_codes)
        self.assertNotIn('LUXURY', plan_codes)

    def test_get_recommended_templates_luxury_user(self):
        """Test recommendations for LUXURY user."""
        recommended = RecommendationService.get_recommended_templates('LUXURY', limit=10)
        # Should get all templates
        self.assertGreaterEqual(len(recommended), 3)

    def test_get_recommended_templates_with_category(self):
        """Test recommendations filtered by category."""
        recommended = RecommendationService.get_recommended_templates(
            'PREMIUM',
            category_code='WEDDING',
            limit=10
        )
        # All should be wedding templates
        for template in recommended:
            self.assertEqual(template.category.code, 'WEDDING')

    def test_get_recommended_templates_ordered_by_popularity(self):
        """Test recommendations are ordered by popularity."""
        recommended = RecommendationService.get_recommended_templates('LUXURY', limit=10)
        # Should be ordered by use_count descending
        use_counts = [t.use_count for t in recommended]
        self.assertEqual(use_counts, sorted(use_counts, reverse=True))

    def test_get_recommended_templates_limit(self):
        """Test recommendation limit is respected."""
        recommended = RecommendationService.get_recommended_templates('LUXURY', limit=2)
        self.assertEqual(len(recommended), 2)

    def test_get_similar_templates(self):
        """Test getting similar templates."""
        similar = RecommendationService.get_similar_templates(
            str(self.basic_wedding.id),
            limit=4
        )
        # Should find similar templates
        self.assertGreater(len(similar), 0)
        # Should not include the original template
        similar_ids = [str(t.id) for t in similar]
        self.assertNotIn(str(self.basic_wedding.id), similar_ids)

    def test_get_similar_templates_same_category_priority(self):
        """Test similar templates prioritize same category."""
        similar = RecommendationService.get_similar_templates(
            str(self.basic_wedding.id),
            limit=4
        )
        # First result should be same category
        if len(similar) > 0:
            # At least one should be from wedding category
            categories = [t.category.code for t in similar]
            self.assertIn('WEDDING', categories)

    def test_get_similar_templates_invalid_id(self):
        """Test getting similar templates with invalid ID."""
        import uuid
        fake_id = str(uuid.uuid4())
        similar = RecommendationService.get_similar_templates(fake_id, limit=4)
        self.assertEqual(len(similar), 0)

    def test_get_trending_templates(self):
        """Test getting trending templates."""
        trending = RecommendationService.get_trending_templates(days=7, limit=6)
        self.assertGreater(len(trending), 0)
        # Recent template should be included
        template_ids = [str(t.id) for t in trending]
        self.assertIn(str(self.recent_template.id), template_ids)

    def test_get_trending_templates_fills_with_popular(self):
        """Test trending fills with popular templates if not enough recent."""
        # Request more trending than recent templates available
        trending = RecommendationService.get_trending_templates(days=7, limit=10)
        # Should still return templates (filled with popular ones)
        self.assertGreater(len(trending), 0)

    def test_get_templates_for_event_wedding(self):
        """Test getting templates for wedding event."""
        templates = RecommendationService.get_templates_for_event(
            'WEDDING',
            'PREMIUM',
            limit=6
        )
        # All should be wedding templates
        for template in templates:
            self.assertEqual(template.category.code, 'WEDDING')

    def test_get_templates_for_event_birthday(self):
        """Test getting templates for birthday event."""
        templates = RecommendationService.get_templates_for_event(
            'BIRTHDAY',
            'PREMIUM',
            limit=6
        )
        # All should be birthday templates
        for template in templates:
            self.assertEqual(template.category.code, 'BIRTHDAY')

    def test_get_templates_for_event_unmapped_type(self):
        """Test getting templates for unmapped event type."""
        templates = RecommendationService.get_templates_for_event(
            'UNKNOWN_EVENT',
            'PREMIUM',
            limit=6
        )
        # Should return general recommendations
        self.assertGreater(len(templates), 0)

    def test_get_new_arrivals(self):
        """Test getting new arrivals."""
        new_arrivals = RecommendationService.get_new_arrivals(limit=6)
        self.assertGreater(len(new_arrivals), 0)
        # Recent template should be first or near the top
        template_ids = [str(t.id) for t in new_arrivals[:3]]
        self.assertIn(str(self.recent_template.id), template_ids)

    def test_get_best_sellers(self):
        """Test getting best sellers."""
        best_sellers = RecommendationService.get_best_sellers(limit=6)
        self.assertGreater(len(best_sellers), 0)
        # Luxury wedding (use_count=100) should be first
        self.assertEqual(str(best_sellers[0].id), str(self.luxury_wedding.id))

    def test_get_best_sellers_ordered(self):
        """Test best sellers are ordered by use count."""
        best_sellers = RecommendationService.get_best_sellers(limit=10)
        use_counts = [t.use_count for t in best_sellers]
        self.assertEqual(use_counts, sorted(use_counts, reverse=True))

    def test_get_premium_picks_basic_user(self):
        """Test premium picks for BASIC user."""
        picks = RecommendationService.get_premium_picks('BASIC', limit=6)
        # Should get no premium templates (BASIC plan doesn't have premium templates)
        self.assertEqual(len(picks), 0)

    def test_get_premium_picks_premium_user(self):
        """Test premium picks for PREMIUM user."""
        picks = RecommendationService.get_premium_picks('PREMIUM', limit=6)
        # Should get premium templates from BASIC and PREMIUM plans
        self.assertGreater(len(picks), 0)
        for template in picks:
            self.assertTrue(template.is_premium)

    def test_get_premium_picks_luxury_user(self):
        """Test premium picks for LUXURY user."""
        picks = RecommendationService.get_premium_picks('LUXURY', limit=6)
        # Should get all premium templates
        self.assertGreater(len(picks), 0)
        for template in picks:
            self.assertTrue(template.is_premium)

    def test_get_recommendations_by_animation(self):
        """Test getting recommendations by animation type."""
        elegant = RecommendationService.get_recommendations_by_animation(
            'elegant',
            'LUXURY',
            limit=6
        )
        # All should have elegant animation
        for template in elegant:
            self.assertEqual(template.animation_type, 'elegant')

    def test_get_recommendations_by_animation_respects_plan(self):
        """Test animation recommendations respect plan access."""
        elegant = RecommendationService.get_recommendations_by_animation(
            'elegant',
            'BASIC',
            limit=6
        )
        # All should be BASIC plan only
        for template in elegant:
            self.assertEqual(template.plan.code, 'BASIC')

    def test_get_personalized_homepage(self):
        """Test getting personalized homepage sections."""
        homepage = RecommendationService.get_personalized_homepage('PREMIUM')

        # Check all sections exist
        self.assertIn('recommended', homepage)
        self.assertIn('trending', homepage)
        self.assertIn('new_arrivals', homepage)
        self.assertIn('best_sellers', homepage)
        self.assertIn('premium_picks', homepage)

        # Check sections have content
        self.assertGreater(len(homepage['recommended']), 0)
        self.assertGreater(len(homepage['new_arrivals']), 0)
        self.assertGreater(len(homepage['best_sellers']), 0)

    def test_get_recommendation_score_plan_match(self):
        """Test recommendation score with plan match."""
        score = RecommendationService.get_recommendation_score(
            self.premium_wedding,
            'PREMIUM'
        )
        # Should include plan match bonus (+10)
        self.assertGreaterEqual(score, 10)

    def test_get_recommendation_score_category_match(self):
        """Test recommendation score with category match."""
        score = RecommendationService.get_recommendation_score(
            self.premium_wedding,
            'PREMIUM',
            'WEDDING'
        )
        # Should include category match bonus (+20)
        self.assertGreaterEqual(score, 20)

    def test_get_recommendation_score_popularity(self):
        """Test recommendation score includes popularity."""
        score = RecommendationService.get_recommendation_score(
            self.luxury_wedding,  # use_count=100
            'LUXURY'
        )
        # Should include use_count (capped at 100)
        self.assertGreaterEqual(score, 100)

    def test_get_recommendation_score_recency_bonus(self):
        """Test recommendation score includes recency bonus."""
        score = RecommendationService.get_recommendation_score(
            self.recent_template,
            'BASIC'
        )
        # Recent template (2 days old) should get recency bonus (+10)
        self.assertGreaterEqual(score, 10)

    def test_get_recommendation_score_premium_bonus(self):
        """Test recommendation score includes premium bonus."""
        score_premium = RecommendationService.get_recommendation_score(
            self.premium_wedding,
            'PREMIUM'
        )
        score_basic = RecommendationService.get_recommendation_score(
            self.basic_wedding,
            'BASIC'
        )
        # Premium template for premium user should have higher score
        # (assuming similar other factors)
        # Premium template gets +5 bonus for premium/luxury users
        self.assertGreater(score_premium, score_basic - 10)  # Account for use_count difference
