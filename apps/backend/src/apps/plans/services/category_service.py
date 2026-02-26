"""
Category management service.

This service handles invitation category operations.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from django.db.models import Count

from ..models import InvitationCategory, Template

logger = logging.getLogger(__name__)


class CategoryService:
    """Service for category management."""

    @staticmethod
    def get_all_categories() -> List[InvitationCategory]:
        """
        Get all active categories ordered by sort_order.

        Returns:
            List of active categories
        """
        return list(
            InvitationCategory.objects.filter(is_active=True)
            .order_by('sort_order', 'name')
        )

    @staticmethod
    def get_category_by_code(code: str) -> Tuple[bool, Optional[InvitationCategory], Optional[str]]:
        """
        Get category by code.

        Args:
            code: Category code

        Returns:
            Tuple of (success, category, error_message)
        """
        try:
            category = InvitationCategory.objects.get(code=code.upper(), is_active=True)
            return True, category, None
        except InvitationCategory.DoesNotExist:
            return False, None, f"Category '{code}' not found"
        except Exception as e:
            logger.error(f"Error getting category by code: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_templates_count_by_category() -> Dict[str, int]:
        """
        Get count of active templates for each category.

        Returns:
            Dictionary mapping category codes to template counts
        """
        counts = {}
        category_counts = Template.objects.filter(
            is_active=True
        ).values('category__code', 'category__name').annotate(
            count=Count('id')
        ).order_by('-count')

        for item in category_counts:
            counts[item['category__code']] = {
                'name': item['category__name'],
                'count': item['count']
            }

        return counts

    @staticmethod
    def get_popular_categories(limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get most popular categories by template usage.

        Args:
            limit: Number of categories to return (default 5)

        Returns:
            List of categories with usage stats
        """
        from django.db.models import Sum

        categories = InvitationCategory.objects.filter(
            is_active=True
        ).annotate(
            total_usage=Sum('templates__use_count'),
            template_count=Count('templates', filter=models.Q(templates__is_active=True))
        ).order_by('-total_usage')[:limit]

        result = []
        for category in categories:
            result.append({
                'code': category.code,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'template_count': category.template_count,
                'total_usage': category.total_usage or 0
            })

        return result

    @staticmethod
    def get_category_summary(category: InvitationCategory) -> Dict[str, Any]:
        """
        Get comprehensive category summary.

        Args:
            category: Category to summarize

        Returns:
            Dictionary with category data
        """
        # Get template count for this category
        template_count = Template.objects.filter(
            category=category,
            is_active=True
        ).count()

        return {
            'code': category.code,
            'name': category.name,
            'description': category.description,
            'icon': category.icon,
            'template_count': template_count,
            'sort_order': category.sort_order,
            'is_active': category.is_active
        }

    @staticmethod
    def get_categories_with_template_counts() -> List[Dict[str, Any]]:
        """
        Get all categories with their template counts.

        Returns:
            List of categories with template counts
        """
        categories = InvitationCategory.objects.filter(is_active=True).annotate(
            template_count=Count('templates', filter=models.Q(templates__is_active=True))
        ).order_by('sort_order', 'name')

        result = []
        for category in categories:
            result.append({
                'code': category.code,
                'name': category.name,
                'description': category.description,
                'icon': category.icon,
                'template_count': category.template_count,
                'sort_order': category.sort_order
            })

        return result

    @staticmethod
    def search_categories(query: str) -> List[InvitationCategory]:
        """
        Search categories by name or description.

        Args:
            query: Search query string

        Returns:
            List of matching categories
        """
        from django.db.models import Q

        return list(
            InvitationCategory.objects.filter(
                Q(name__icontains=query) | Q(description__icontains=query),
                is_active=True
            ).order_by('sort_order', 'name')
        )

    @staticmethod
    def validate_category_code(code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a category code is valid and active.

        Args:
            code: Category code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not code:
            return False, "Category code is required"

        exists = InvitationCategory.objects.filter(
            code=code.upper(),
            is_active=True
        ).exists()

        if not exists:
            return False, f"Category '{code}' is not available"

        return True, None


# Import at the end to avoid circular imports
from django.db import models
