"""
Template recommendation service.

This service provides intelligent template recommendations based on various factors.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import timedelta
from django.db.models import Q, Count
from django.utils import timezone

from ..models import Template
from .plan_service import PlanService

logger = logging.getLogger(__name__)


class RecommendationService:
    """Service for template recommendations."""

    @staticmethod
    def get_recommended_templates(
        user_plan_code: str,
        category_code: Optional[str] = None,
        limit: int = 6
    ) -> List[Template]:
        """
        Get personalized template recommendations for user.

        Recommendation factors:
        1. User's plan tier (can only access their tier and below)
        2. Category preference (if provided)
        3. Template popularity (use_count)
        4. Recency (recently added templates)

        Args:
            user_plan_code: User's plan code
            category_code: Optional preferred category
            limit: Number of recommendations (default 6)

        Returns:
            List of recommended templates
        """
        # Get accessible plans based on user's tier
        accessible_plans = PlanService.get_accessible_plans(user_plan_code)

        # Build base query
        templates = Template.objects.filter(
            plan__code__in=accessible_plans,
            is_active=True
        )

        # Filter by category if provided
        if category_code:
            templates = templates.filter(category__code=category_code.upper())

        # Order by popularity and recency (weighted)
        # Use F expressions for complex ordering
        from django.db.models import F, ExpressionWrapper, IntegerField
        from django.db.models.functions import Coalesce

        # Calculate a score: use_count * 0.7 + days_old_factor * 0.3
        # Newer templates get slight boost
        templates = templates.select_related('plan', 'category').order_by(
            '-use_count',      # Primary: popularity
            '-created_at'       # Secondary: recency
        )[:limit]

        return list(templates)

    @staticmethod
    def get_similar_templates(template_id: str, limit: int = 4) -> List[Template]:
        """
        Get templates similar to the given template.

        Similarity factors:
        1. Same category (strongest)
        2. Same animation type (medium)
        3. Same plan tier (weak)

        Args:
            template_id: Template UUID to find similar to
            limit: Number of similar templates (default 4)

        Returns:
            List of similar templates
        """
        try:
            base_template = Template.objects.get(id=template_id, is_active=True)
        except Template.DoesNotExist:
            logger.warning(f"Template {template_id} not found for similarity")
            return []

        # Find similar templates
        similar = Template.objects.filter(
            is_active=True
        ).exclude(
            id=template_id
        ).select_related('plan', 'category')

        # Score by similarity
        # Same category: +3, Same animation: +2, Same plan: +1
        same_category = similar.filter(category=base_template.category)
        same_animation = similar.filter(animation_type=base_template.animation_type)
        same_plan = similar.filter(plan=base_template.plan)

        # Combine: prioritize same category, then animation, then plan
        results = []

        # Add same category + animation (highest similarity)
        results.extend(same_category.filter(animation_type=base_template.animation_type)[:limit])

        # Add same category (if we need more)
        if len(results) < limit:
            for template in same_category:
                if template not in results and len(results) < limit:
                    results.append(template)

        # Add same animation (if we still need more)
        if len(results) < limit:
            for template in same_animation:
                if template not in results and len(results) < limit:
                    results.append(template)

        # Add same plan (if we still need more)
        if len(results) < limit:
            for template in same_plan:
                if template not in results and len(results) < limit:
                    results.append(template)

        return results[:limit]

    @staticmethod
    def get_trending_templates(days: int = 7, limit: int = 6) -> List[Template]:
        """
        Get trending templates based on recent usage increase.

        Args:
            days: Number of days to consider (default 7)
            limit: Number of templates (default 6)

        Returns:
            List of trending templates
        """
        # For now, simply return most popular recent templates
        # In future, can track usage_delta by comparing current vs previous period

        cutoff_date = timezone.now() - timedelta(days=days)

        trending = Template.objects.filter(
            is_active=True,
            created_at__gte=cutoff_date
        ).select_related('plan', 'category').order_by(
            '-use_count',
            '-created_at'
        )[:limit]

        # If not enough recent templates, fill with popular ones
        if trending.count() < limit:
            popular = Template.objects.filter(
                is_active=True
            ).exclude(
                id__in=[t.id for t in trending]
            ).select_related('plan', 'category').order_by(
                '-use_count'
            )[:limit - trending.count()]

            return list(trending) + list(popular)

        return list(trending)

    @staticmethod
    def get_templates_for_event(
        event_type: str,
        user_plan_code: str,
        limit: int = 6
    ) -> List[Template]:
        """
        Get recommended templates for a specific event type.

        Maps event types to categories and returns relevant templates.

        Args:
            event_type: Event type (wedding, birthday, etc.)
            user_plan_code: User's plan code
            limit: Number of templates (default 6)

        Returns:
            List of templates for the event
        """
        # Map event types to category codes
        event_category_map = {
            'WEDDING': 'WEDDING',
            'BIRTHDAY': 'BIRTHDAY',
            'ANNIVERSARY': 'ANNIVERSARY',
            'ENGAGEMENT': 'ENGAGEMENT',
            'HOUSEWARMING': 'HOUSEWARMING',
            'BABY_SHOWER': 'BABY_SHOWER',
            'GRADUATION': 'GRADUATION',
            'RETIREMENT': 'RETIREMENT',
            'CORPORATE': 'CORPORATE',
            'RELIGIOUS': 'RELIGIOUS'
        }

        category_code = event_category_map.get(event_type.upper())

        if category_code:
            return RecommendationService.get_recommended_templates(
                user_plan_code=user_plan_code,
                category_code=category_code,
                limit=limit
            )
        else:
            # If event type not mapped, return general recommendations
            return RecommendationService.get_recommended_templates(
                user_plan_code=user_plan_code,
                limit=limit
            )

    @staticmethod
    def get_new_arrivals(limit: int = 6) -> List[Template]:
        """
        Get recently added templates.

        Args:
            limit: Number of templates (default 6)

        Returns:
            List of newest templates
        """
        return list(
            Template.objects.filter(is_active=True)
            .select_related('plan', 'category')
            .order_by('-created_at')[:limit]
        )

    @staticmethod
    def get_best_sellers(limit: int = 6) -> List[Template]:
        """
        Get best-selling (most used) templates.

        Args:
            limit: Number of templates (default 6)

        Returns:
            List of most popular templates
        """
        return list(
            Template.objects.filter(is_active=True)
            .select_related('plan', 'category')
            .order_by('-use_count', '-created_at')[:limit]
        )

    @staticmethod
    def get_premium_picks(user_plan_code: str, limit: int = 6) -> List[Template]:
        """
        Get premium template recommendations.

        Args:
            user_plan_code: User's plan code
            limit: Number of templates (default 6)

        Returns:
            List of premium templates user can access
        """
        accessible_plans = PlanService.get_accessible_plans(user_plan_code)

        return list(
            Template.objects.filter(
                plan__code__in=accessible_plans,
                is_premium=True,
                is_active=True
            ).select_related('plan', 'category').order_by(
                '-use_count',
                '-created_at'
            )[:limit]
        )

    @staticmethod
    def get_recommendations_by_animation(
        animation_type: str,
        user_plan_code: str,
        limit: int = 6
    ) -> List[Template]:
        """
        Get templates by animation style.

        Args:
            animation_type: Animation type (elegant, fun, traditional, etc.)
            user_plan_code: User's plan code
            limit: Number of templates (default 6)

        Returns:
            List of templates with specified animation
        """
        accessible_plans = PlanService.get_accessible_plans(user_plan_code)

        return list(
            Template.objects.filter(
                plan__code__in=accessible_plans,
                animation_type=animation_type,
                is_active=True
            ).select_related('plan', 'category').order_by(
                '-use_count',
                '-created_at'
            )[:limit]
        )

    @staticmethod
    def get_personalized_homepage(user_plan_code: str) -> Dict[str, List[Template]]:
        """
        Get personalized homepage template sections.

        Returns multiple sections of templates for homepage display.

        Args:
            user_plan_code: User's plan code

        Returns:
            Dictionary with different template sections
        """
        return {
            'recommended': RecommendationService.get_recommended_templates(user_plan_code, limit=6),
            'trending': RecommendationService.get_trending_templates(limit=6),
            'new_arrivals': RecommendationService.get_new_arrivals(limit=6),
            'best_sellers': RecommendationService.get_best_sellers(limit=6),
            'premium_picks': RecommendationService.get_premium_picks(user_plan_code, limit=4)
        }

    @staticmethod
    def get_recommendation_score(template: Template, user_plan_code: str, category_code: Optional[str] = None) -> float:
        """
        Calculate recommendation score for a template.

        Score factors:
        - Plan match: +10 if matches user's plan
        - Category match: +20 if matches preferred category
        - Popularity: +use_count
        - Recency: +10 if created within last 30 days

        Args:
            template: Template to score
            user_plan_code: User's plan code
            category_code: Optional preferred category

        Returns:
            Recommendation score (higher is better)
        """
        score = 0.0

        # Plan match
        if template.plan.code == user_plan_code.upper():
            score += 10

        # Category match
        if category_code and template.category.code == category_code.upper():
            score += 20

        # Popularity (normalized)
        score += min(template.use_count, 100)  # Cap at 100

        # Recency bonus
        days_old = (timezone.now() - template.created_at).days
        if days_old <= 30:
            score += 10

        # Premium bonus for higher tier plans
        if template.is_premium and user_plan_code.upper() in ['PREMIUM', 'LUXURY']:
            score += 5

        return score
