"""
Plan management service.

This service handles plan retrieval, hierarchy logic, and access control.
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
from decimal import Decimal

from ..models import Plan

logger = logging.getLogger(__name__)


class PlanService:
    """Service for plan management."""

    # Plan hierarchy for access control
    PLAN_HIERARCHY = {
        'BASIC': 1,
        'PREMIUM': 2,
        'LUXURY': 3
    }

    @staticmethod
    def get_all_active_plans() -> List[Plan]:
        """
        Get all active plans ordered by sort_order and price.

        Returns:
            List of active Plan objects
        """
        return list(Plan.objects.filter(is_active=True).order_by('sort_order', 'price_inr'))

    @staticmethod
    def get_plan_by_code(plan_code: str) -> Tuple[bool, Optional[Plan], Optional[str]]:
        """
        Get plan by code.

        Args:
            plan_code: Plan code (BASIC, PREMIUM, LUXURY)

        Returns:
            Tuple of (success, plan, error_message)
        """
        try:
            plan = Plan.objects.get(code=plan_code.upper(), is_active=True)
            return True, plan, None
        except Plan.DoesNotExist:
            return False, None, f"Plan '{plan_code}' not found"
        except Exception as e:
            logger.error(f"Error getting plan by code: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_plan_by_id(plan_id: str) -> Tuple[bool, Optional[Plan], Optional[str]]:
        """
        Get plan by UUID.

        Args:
            plan_id: Plan UUID

        Returns:
            Tuple of (success, plan, error_message)
        """
        try:
            plan = Plan.objects.get(id=plan_id, is_active=True)
            return True, plan, None
        except Plan.DoesNotExist:
            return False, None, "Plan not found"
        except Exception as e:
            logger.error(f"Error getting plan by ID: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def get_plan_hierarchy() -> Dict[str, int]:
        """
        Get plan hierarchy mapping.

        Returns:
            Dictionary mapping plan codes to tier levels
        """
        return PlanService.PLAN_HIERARCHY.copy()

    @staticmethod
    def can_access_plan(user_plan_code: str, target_plan_code: str) -> bool:
        """
        Check if user with given plan can access target plan's features.

        Users can access their tier and below:
        - BASIC user: Only BASIC
        - PREMIUM user: BASIC + PREMIUM
        - LUXURY user: All plans

        Args:
            user_plan_code: User's current plan code
            target_plan_code: Target plan code to check

        Returns:
            True if user can access, False otherwise
        """
        user_tier = PlanService.PLAN_HIERARCHY.get(user_plan_code.upper(), 0)
        target_tier = PlanService.PLAN_HIERARCHY.get(target_plan_code.upper(), 0)

        return target_tier <= user_tier

    @staticmethod
    def get_accessible_plans(user_plan_code: str) -> List[str]:
        """
        Get list of plan codes user can access.

        Args:
            user_plan_code: User's current plan code

        Returns:
            List of accessible plan codes
        """
        user_tier = PlanService.PLAN_HIERARCHY.get(user_plan_code.upper(), 0)

        accessible = []
        for plan_code, tier in PlanService.PLAN_HIERARCHY.items():
            if tier <= user_tier:
                accessible.append(plan_code)

        return accessible

    @staticmethod
    def get_plan_summary(plan: Plan) -> Dict[str, Any]:
        """
        Get comprehensive plan summary.

        Args:
            plan: Plan to summarize

        Returns:
            Dictionary with plan data
        """
        return {
            'id': str(plan.id),
            'code': plan.code,
            'name': plan.name,
            'description': plan.description,
            'pricing': {
                'inr': float(plan.price_inr),
                'display': plan.display_price
            },
            'links': {
                'regular': plan.regular_links,
                'test': plan.test_links
            },
            'features': plan.features,
            'tier': PlanService.PLAN_HIERARCHY.get(plan.code, 0),
            'is_active': plan.is_active,
            'created_at': plan.created_at.isoformat()
        }

    @staticmethod
    def compare_plans() -> Dict[str, Any]:
        """
        Get comparison data for all plans.

        Returns:
            Dictionary with comparison data
        """
        plans = PlanService.get_all_active_plans()

        comparison = {
            'plans': [],
            'features_comparison': []
        }

        # Collect all features
        all_features = set()
        for plan in plans:
            all_features.update(plan.features)

        # Build comparison data
        for plan in plans:
            comparison['plans'].append({
                'code': plan.code,
                'name': plan.name,
                'price': float(plan.price_inr),
                'display_price': plan.display_price,
                'regular_links': plan.regular_links,
                'test_links': plan.test_links,
                'features': plan.features
            })

        comparison['features_comparison'] = sorted(list(all_features))

        return comparison

    @staticmethod
    def get_plan_tier_name(plan_code: str) -> str:
        """
        Get tier name for a plan.

        Args:
            plan_code: Plan code

        Returns:
            Tier name (e.g., "Basic Tier", "Premium Tier")
        """
        tier_names = {
            'BASIC': 'Basic Tier',
            'PREMIUM': 'Premium Tier',
            'LUXURY': 'Luxury Tier'
        }
        return tier_names.get(plan_code.upper(), 'Unknown Tier')

    @staticmethod
    def get_upgrade_path(current_plan_code: str) -> List[Dict[str, Any]]:
        """
        Get available upgrade options for a plan.

        Args:
            current_plan_code: Current plan code

        Returns:
            List of upgrade options with pricing
        """
        current_tier = PlanService.PLAN_HIERARCHY.get(current_plan_code.upper(), 0)

        upgrades = []
        plans = Plan.objects.filter(is_active=True).order_by('sort_order', 'price_inr')

        for plan in plans:
            plan_tier = PlanService.PLAN_HIERARCHY.get(plan.code, 0)
            if plan_tier > current_tier:
                upgrades.append({
                    'code': plan.code,
                    'name': plan.name,
                    'price': float(plan.price_inr),
                    'tier_difference': plan_tier - current_tier,
                    'additional_links': plan.regular_links,
                    'features': plan.features
                })

        return upgrades

    @staticmethod
    def validate_plan_code(plan_code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a plan code is valid and active.

        Args:
            plan_code: Plan code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not plan_code:
            return False, "Plan code is required"

        if plan_code.upper() not in PlanService.PLAN_HIERARCHY:
            return False, f"Invalid plan code: {plan_code}"

        # Check if plan exists and is active
        exists = Plan.objects.filter(code=plan_code.upper(), is_active=True).exists()
        if not exists:
            return False, f"Plan '{plan_code}' is not available"

        return True, None
