"""
Template management service.

This service handles template retrieval, filtering, and usage tracking.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from django.db.models import Q, QuerySet

from ..models import Template, Plan
from .plan_service import PlanService

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for template management."""

    @staticmethod
    def get_all_templates(
        filters: Optional[Dict[str, Any]] = None,
        ordering: Optional[str] = None
    ) -> QuerySet:
        """
        Get all active templates with optional filtering.

        Args:
            filters: Dictionary of filters (plan_code, category_code, animation_type, is_premium)
            ordering: Ordering field (use_count, created_at, name)

        Returns:
            QuerySet of templates
        """
        queryset = Template.objects.filter(is_active=True).select_related('plan', 'category')

        # Apply filters
        if filters:
            if 'plan_code' in filters:
                queryset = queryset.filter(plan__code=filters['plan_code'].upper())

            if 'category_code' in filters:
                queryset = queryset.filter(category__code=filters['category_code'].upper())

            if 'animation_type' in filters:
                queryset = queryset.filter(animation_type=filters['animation_type'])

            if 'is_premium' in filters:
                queryset = queryset.filter(is_premium=filters['is_premium'])

        # Apply ordering
        if ordering:
            if ordering.startswith('-'):
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('sort_order', '-use_count', '-created_at')

        return queryset

    @staticmethod
    def get_template_by_id(template_id: str) -> Tuple[bool, Optional[Template], Optional[str]]:
        """
        Get template by UUID.

        Args:
            template_id: Template UUID

        Returns:
            Tuple of (success, template, error_message)
        """
        try:
            template = Template.objects.select_related('plan', 'category').get(
                id=template_id,
                is_active=True
            )
            return True, template, None
        except Template.DoesNotExist:
            return False, None, "Template not found"
        except Exception as e:
            logger.error(f"Error getting template by ID: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_templates_by_plan(
        plan_code: str,
        category_code: Optional[str] = None
    ) -> Tuple[bool, Optional[QuerySet], Optional[str]]:
        """
        Get templates accessible for a specific plan.

        Uses plan hierarchy:
        - BASIC: Only BASIC templates
        - PREMIUM: BASIC + PREMIUM templates
        - LUXURY: All templates

        Args:
            plan_code: Plan code
            category_code: Optional category filter

        Returns:
            Tuple of (success, templates, error_message)
        """
        try:
            # Validate plan exists
            success, plan, error = PlanService.get_plan_by_code(plan_code)
            if not success:
                return False, None, error

            # Get accessible plan codes based on hierarchy
            accessible_plans = PlanService.get_accessible_plans(plan_code)

            # Build query
            templates = Template.objects.filter(
                plan__code__in=accessible_plans,
                is_active=True
            )

            # Filter by category if provided
            if category_code:
                templates = templates.filter(category__code=category_code.upper())

            templates = templates.select_related('plan', 'category').order_by(
                'sort_order', '-use_count', '-created_at'
            )

            return True, templates, None

        except Exception as e:
            logger.error(f"Error getting templates by plan: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_templates_by_category(
        category_code: str,
        plan_code: Optional[str] = None
    ) -> QuerySet:
        """
        Get templates for a specific category.

        Args:
            category_code: Category code
            plan_code: Optional plan filter

        Returns:
            QuerySet of templates
        """
        templates = Template.objects.filter(
            category__code=category_code.upper(),
            is_active=True
        )

        if plan_code:
            accessible_plans = PlanService.get_accessible_plans(plan_code)
            templates = templates.filter(plan__code__in=accessible_plans)

        return templates.select_related('plan', 'category').order_by(
            'sort_order', '-use_count'
        )

    @staticmethod
    def get_featured_templates(limit: int = 6) -> List[Template]:
        """
        Get featured/popular templates.

        Args:
            limit: Number of templates to return (default 6)

        Returns:
            List of most popular templates
        """
        return list(
            Template.objects.filter(is_active=True)
            .select_related('plan', 'category')
            .order_by('-use_count', '-created_at')[:limit]
        )

    @staticmethod
    def increment_template_usage(template_id: str) -> Tuple[bool, Optional[str]]:
        """
        Increment template usage count.

        Args:
            template_id: Template UUID

        Returns:
            Tuple of (success, error_message)
        """
        try:
            template = Template.objects.get(id=template_id, is_active=True)
            template.increment_use_count()

            logger.info(f"Template {template.name} usage incremented to {template.use_count}")
            return True, None

        except Template.DoesNotExist:
            return False, "Template not found"
        except Exception as e:
            logger.error(f"Error incrementing template usage: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def can_user_access_template(user_plan_code: str, template: Template) -> bool:
        """
        Check if user with given plan can access template.

        Args:
            user_plan_code: User's plan code
            template: Template to check

        Returns:
            True if user can access, False otherwise
        """
        return PlanService.can_access_plan(user_plan_code, template.plan.code)

    @staticmethod
    def search_templates(
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> QuerySet:
        """
        Search templates by name or description.

        Args:
            query: Search query string
            filters: Optional filters (plan_code, category_code)

        Returns:
            QuerySet of matching templates
        """
        templates = Template.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )

        if filters:
            if 'plan_code' in filters:
                accessible_plans = PlanService.get_accessible_plans(filters['plan_code'])
                templates = templates.filter(plan__code__in=accessible_plans)

            if 'category_code' in filters:
                templates = templates.filter(category__code=filters['category_code'].upper())

        return templates.select_related('plan', 'category').order_by(
            '-use_count', '-created_at'
        )

    @staticmethod
    def get_template_summary(template: Template) -> Dict[str, Any]:
        """
        Get comprehensive template summary.

        Args:
            template: Template to summarize

        Returns:
            Dictionary with template data
        """
        return {
            'id': str(template.id),
            'name': template.name,
            'description': template.description,
            'plan': {
                'code': template.plan.code,
                'name': template.plan.name
            },
            'category': {
                'code': template.category.code,
                'name': template.category.name
            },
            'animation': {
                'type': template.animation_type,
                'config': template.animation_config
            },
            'theme_colors': template.theme_colors,
            'features': {
                'supports_gallery': template.supports_gallery,
                'supports_music': template.supports_music,
                'supports_video': template.supports_video,
                'supports_rsvp': template.supports_rsvp
            },
            'thumbnail': template.thumbnail.url if template.thumbnail else None,
            'preview_url': template.preview_url,
            'is_premium': template.is_premium,
            'use_count': template.use_count,
            'created_at': template.created_at.isoformat()
        }

    @staticmethod
    def get_templates_by_animation_type(
        animation_type: str,
        plan_code: Optional[str] = None
    ) -> QuerySet:
        """
        Get templates by animation type.

        Args:
            animation_type: Animation type (elegant, fun, traditional, etc.)
            plan_code: Optional plan filter

        Returns:
            QuerySet of templates
        """
        templates = Template.objects.filter(
            animation_type=animation_type,
            is_active=True
        )

        if plan_code:
            accessible_plans = PlanService.get_accessible_plans(plan_code)
            templates = templates.filter(plan__code__in=accessible_plans)

        return templates.select_related('plan', 'category').order_by('-use_count')

    @staticmethod
    def get_premium_templates(plan_code: Optional[str] = None) -> QuerySet:
        """
        Get premium templates.

        Args:
            plan_code: Optional plan filter

        Returns:
            QuerySet of premium templates
        """
        templates = Template.objects.filter(
            is_premium=True,
            is_active=True
        )

        if plan_code:
            accessible_plans = PlanService.get_accessible_plans(plan_code)
            templates = templates.filter(plan__code__in=accessible_plans)

        return templates.select_related('plan', 'category').order_by('-use_count')

    @staticmethod
    def get_template_count_by_plan() -> Dict[str, int]:
        """
        Get count of templates for each plan.

        Returns:
            Dictionary with plan codes and counts
        """
        from django.db.models import Count

        counts = {}
        plan_counts = Template.objects.filter(is_active=True).values('plan__code').annotate(
            count=Count('id')
        )

        for item in plan_counts:
            counts[item['plan__code']] = item['count']

        return counts

    @staticmethod
    def validate_template_access(user_plan_code: str, template_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if user can access a template.

        Args:
            user_plan_code: User's plan code
            template_id: Template UUID

        Returns:
            Tuple of (can_access, error_message)
        """
        success, template, error = TemplateService.get_template_by_id(template_id)
        if not success:
            return False, error

        if not TemplateService.can_user_access_template(user_plan_code, template):
            return False, f"This template requires {template.plan.name} plan or higher"

        return True, None
