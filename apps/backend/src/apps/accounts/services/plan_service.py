"""
Plan management service for user plans.

This service handles user plan operations, plan changes, and plan access control.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

from .activity_service import ActivityService

logger = logging.getLogger(__name__)
User = get_user_model()


class PlanService:
    """Service for user plan management."""

    # Plan hierarchy for access control
    PLAN_HIERARCHY = {
        'BASIC': 1,
        'PREMIUM': 2,
        'LUXURY': 3
    }

    @staticmethod
    def get_user_plan(user: User) -> Dict[str, Any]:
        """
        Get user's current plan details.

        If user has no current_plan set but has an approved order,
        this will automatically update the user's current_plan.

        Args:
            user: User whose plan to retrieve

        Returns:
            Dictionary with plan information
        """
        # Import here to avoid circular imports
        from apps.invitations.models import Order

        # Get latest approved order
        latest_order = user.orders.filter(
            status='APPROVED'
        ).select_related('plan').first()

        plan_data = None

        if latest_order and latest_order.plan:
            # Update user's current plan if not set
            if not user.current_plan:
                PlanService.update_user_plan(user, latest_order.plan)

            plan_data = {
                'code': latest_order.plan.code,
                'name': latest_order.plan.name,
                'price_inr': float(latest_order.plan.price_inr),
                'price_usd': float(latest_order.plan.price_usd) if hasattr(latest_order.plan, 'price_usd') else None,
                'regular_links': latest_order.plan.regular_links,
                'test_links': latest_order.plan.test_links,
                'features': latest_order.plan.features if hasattr(latest_order.plan, 'features') else []
            }
        elif user.current_plan:
            plan_data = {
                'code': user.current_plan.code,
                'name': user.current_plan.name,
                'price_inr': float(user.current_plan.price_inr),
                'price_usd': float(user.current_plan.price_usd) if hasattr(user.current_plan, 'price_usd') else None,
                'regular_links': user.current_plan.regular_links,
                'test_links': user.current_plan.test_links,
                'features': user.current_plan.features if hasattr(user.current_plan, 'features') else []
            }

        return {
            'current_plan': plan_data,
            'plan_change_requested': user.plan_change_requested,
            'plan_change_requested_at': user.plan_change_requested_at.isoformat() if user.plan_change_requested_at else None,
            'can_change_plan': not user.plan_change_requested
        }

    @staticmethod
    def update_user_plan(user: User, plan) -> None:
        """
        Update user's current plan.

        Args:
            user: User whose plan to update
            plan: Plan object to set as current
        """
        user.current_plan = plan
        user.save(update_fields=['current_plan'])

    @staticmethod
    def request_plan_change(
        user: User,
        new_plan_code: str,
        request = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        Request a plan change.

        Args:
            user: User requesting plan change
            new_plan_code: Code of the plan to change to
            request: Django request object

        Returns:
            Tuple of (success, plan_data, error_message)
        """
        # Import here to avoid circular imports
        from apps.plans.models import Plan

        try:
            # Check if user already has a pending request
            if user.plan_change_requested:
                return False, None, "You already have a pending plan change request. Please wait for admin approval or contact support."

            # Validate plan exists and is active
            try:
                new_plan = Plan.objects.get(code=new_plan_code.upper(), is_active=True)
            except Plan.DoesNotExist:
                return False, None, "Invalid plan selected"

            # Check if user already has this plan
            if user.current_plan and user.current_plan.code == new_plan.code:
                return False, None, "You are already subscribed to this plan"

            # Create plan change request
            with transaction.atomic():
                user.plan_change_requested = True
                user.plan_change_requested_at = timezone.now()
                user.save(update_fields=['plan_change_requested', 'plan_change_requested_at'])

                # Log activity
                ActivityService.log_plan_change_request(
                    user=user,
                    new_plan_code=new_plan.code,
                    current_plan_code=user.current_plan.code if user.current_plan else None,
                    request=request
                )

            plan_data = {
                'code': new_plan.code,
                'name': new_plan.name,
                'price_inr': float(new_plan.price_inr),
                'price_usd': float(new_plan.price_usd) if hasattr(new_plan, 'price_usd') else None
            }

            return True, plan_data, None

        except Exception as e:
            logger.error(f"Error in request_plan_change: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def approve_plan_change(user: User, new_plan, admin: User) -> Tuple[bool, Optional[str]]:
        """
        Approve a plan change request.

        Args:
            user: User whose plan change to approve
            new_plan: Plan object to set as new plan
            admin: Admin user approving the change

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with transaction.atomic():
                user.current_plan = new_plan
                user.plan_change_requested = False
                user.plan_change_requested_at = None
                user.save(update_fields=['current_plan', 'plan_change_requested', 'plan_change_requested_at'])

            logger.info(f"Plan change approved for user {user.id} by admin {admin.id}")
            return True, None

        except Exception as e:
            logger.error(f"Error in approve_plan_change: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def reject_plan_change(user: User, admin: User, reason: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Reject a plan change request.

        Args:
            user: User whose plan change to reject
            admin: Admin user rejecting the change
            reason: Optional reason for rejection

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with transaction.atomic():
                user.plan_change_requested = False
                user.plan_change_requested_at = None
                user.save(update_fields=['plan_change_requested', 'plan_change_requested_at'])

            logger.info(f"Plan change rejected for user {user.id} by admin {admin.id}. Reason: {reason}")
            return True, None

        except Exception as e:
            logger.error(f"Error in reject_plan_change: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def can_access_plan(user: User, plan_code: str) -> bool:
        """
        Check if user can access features of a given plan.

        Users can access their current plan and lower tier plans.

        Args:
            user: User to check
            plan_code: Plan code to check access for

        Returns:
            True if user can access the plan, False otherwise
        """
        if not user.current_plan:
            # Default to BASIC if no plan
            return plan_code.upper() == 'BASIC'

        # Get tier levels
        user_tier = PlanService.PLAN_HIERARCHY.get(user.current_plan.code, 1)
        target_tier = PlanService.PLAN_HIERARCHY.get(plan_code.upper(), 1)

        # User can access their tier and below
        return target_tier <= user_tier

    @staticmethod
    def get_plan_hierarchy() -> Dict[str, int]:
        """
        Get plan hierarchy for reference.

        Returns:
            Dictionary mapping plan codes to tier levels
        """
        return PlanService.PLAN_HIERARCHY.copy()

    @staticmethod
    def get_available_plans_for_user(user: User) -> Dict[str, Any]:
        """
        Get plans available for a user to upgrade/downgrade to.

        Args:
            user: User to check plans for

        Returns:
            Dictionary with available plans categorized by action
        """
        # Import here to avoid circular imports
        from apps.plans.models import Plan

        current_tier = 0
        if user.current_plan:
            current_tier = PlanService.PLAN_HIERARCHY.get(user.current_plan.code, 0)

        all_plans = Plan.objects.filter(is_active=True).order_by('price_inr')

        upgrades = []
        downgrades = []
        current = None

        for plan in all_plans:
            plan_tier = PlanService.PLAN_HIERARCHY.get(plan.code, 0)

            plan_data = {
                'code': plan.code,
                'name': plan.name,
                'price_inr': float(plan.price_inr),
                'price_usd': float(plan.price_usd) if hasattr(plan, 'price_usd') else None,
                'regular_links': plan.regular_links,
                'test_links': plan.test_links
            }

            if plan_tier == current_tier:
                current = plan_data
            elif plan_tier > current_tier:
                upgrades.append(plan_data)
            else:
                downgrades.append(plan_data)

        return {
            'current_plan': current,
            'available_upgrades': upgrades,
            'available_downgrades': downgrades,
            'can_change_plan': not user.plan_change_requested
        }
