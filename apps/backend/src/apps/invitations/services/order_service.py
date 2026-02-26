"""
Order management service.

This service handles order lifecycle, business rules, and order-related operations.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Order, OrderStatus
from .utils import generate_order_number

logger = logging.getLogger(__name__)
User = get_user_model()


class OrderService:
    """Service for order management."""

    @staticmethod
    def create_order(
        user: User,
        plan_code: str,
        event_type: str,
        event_type_name: str,
        request = None
    ) -> Tuple[bool, Optional[Order], Optional[str]]:
        """
        Create a new order.

        Args:
            user: User creating the order
            plan_code: Plan code to order
            event_type: Event type code
            event_type_name: Event type display name
            request: Django request object

        Returns:
            Tuple of (success, order, error_message)
        """
        from apps.plans.models import Plan

        try:
            # Validate plan exists
            try:
                plan = Plan.objects.get(code=plan_code.upper(), is_active=True)
            except Plan.DoesNotExist:
                return False, None, "Invalid plan selected"

            # Check if user can order this plan
            can_order, reason = OrderService.can_user_order_plan(user, plan_code)
            if not can_order:
                return False, None, reason

            # Create order
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    plan=plan,
                    event_type=event_type,
                    event_type_name=event_type_name,
                    payment_amount=plan.price_inr,  # TODO: Handle currency/country
                    granted_regular_links=plan.regular_links,
                    granted_test_links=5,  # Default test links
                    order_number=generate_order_number(),
                    status=OrderStatus.DRAFT
                )

                # Set user's current plan if first order
                if not user.current_plan:
                    user.current_plan = plan
                    user.save(update_fields=['current_plan'])

                # Log activity
                try:
                    from apps.accounts.services import ActivityService
                    ActivityService.log_order_created(
                        user=user,
                        order_id=str(order.id),
                        plan_code=plan.code,
                        request=request
                    )
                except Exception as e:
                    logger.error(f"Failed to log order creation: {e}")

            return True, order, None

        except Exception as e:
            logger.error(f"Error in create_order: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def can_user_order_plan(user: User, plan_code: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user can order a specific plan.

        Rules:
        - If user has no current plan: Can order any plan
        - If user has current plan: Can only reorder same plan
        - To change plans: Must request via admin

        Args:
            user: User wanting to order
            plan_code: Plan code to check

        Returns:
            Tuple of (can_order, reason_if_not)
        """
        # User has no plan - can order any plan
        if not user.current_plan:
            return True, None

        # User has a plan - must match current plan
        if plan_code.upper() != user.current_plan.code:
            return False, (
                f"You are subscribed to the {user.current_plan.name} plan. "
                "To change plans, please contact admin support."
            )

        return True, None

    @staticmethod
    def get_user_orders(user: User):
        """
        Get all orders for a user.

        Args:
            user: User whose orders to retrieve

        Returns:
            QuerySet of orders
        """
        return Order.objects.filter(
            user=user
        ).select_related('plan').prefetch_related('invitation').order_by('-created_at')

    @staticmethod
    def get_order_details(order_id: str, user: User) -> Tuple[bool, Optional[Order], Optional[str]]:
        """
        Get order details.

        Args:
            order_id: Order UUID
            user: User requesting the order

        Returns:
            Tuple of (success, order, error_message)
        """
        try:
            order = Order.objects.select_related(
                'plan', 'approved_by', 'user'
            ).prefetch_related('invitation').get(
                id=order_id,
                user=user
            )
            return True, order, None
        except Order.DoesNotExist:
            return False, None, "Order not found"
        except Exception as e:
            logger.error(f"Error in get_order_details: {e}", exc_info=True)
            return False, None, str(e)

    @staticmethod
    def approve_order(order: Order, admin: User, notes: str = '') -> Tuple[bool, Optional[str]]:
        """
        Approve an order.

        Args:
            order: Order to approve
            admin: Admin user approving
            notes: Optional admin notes

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with transaction.atomic():
                order.status = OrderStatus.APPROVED
                order.approved_by = admin
                order.approved_at = timezone.now()
                if notes:
                    order.admin_notes = notes
                order.save()

                # Activate associated invitation if exists
                if hasattr(order, 'invitation') and order.invitation:
                    from .invitation_service import InvitationService
                    InvitationService.activate_invitation(order.invitation)

            logger.info(f"Order {order.order_number} approved by admin {admin.id}")
            return True, None

        except Exception as e:
            logger.error(f"Error approving order: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def reject_order(order: Order, admin: User, reason: str = '') -> Tuple[bool, Optional[str]]:
        """
        Reject an order.

        Args:
            order: Order to reject
            admin: Admin user rejecting
            reason: Reason for rejection

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with transaction.atomic():
                order.status = OrderStatus.REJECTED
                order.approved_by = admin
                order.approved_at = timezone.now()
                order.admin_notes = reason
                order.save()

            logger.info(f"Order {order.order_number} rejected by admin {admin.id}")
            return True, None

        except Exception as e:
            logger.error(f"Error rejecting order: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def grant_additional_links(
        order: Order,
        regular: int = 0,
        test: int = 0,
        admin: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Grant additional links to an order.

        Args:
            order: Order to grant links to
            regular: Number of regular links to add
            test: Number of test links to add
            admin: Admin user granting links

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with transaction.atomic():
                if regular > 0:
                    order.granted_regular_links += regular
                if test > 0:
                    order.granted_test_links += test

                # Add notes
                if admin:
                    note = f"\n[{timezone.now()}] Granted {regular} regular and {test} test links by {admin.username}"
                    order.admin_notes += note

                order.save()

                # Log activity
                if admin:
                    try:
                        from apps.accounts.models import UserActivityLog
                        UserActivityLog.objects.create(
                            user=order.user,
                            activity_type='LINKS_GRANTED',
                            description=f'Admin granted {regular} regular and {test} test links',
                            ip_address='',
                            user_agent='',
                            metadata={
                                'admin_id': str(admin.id),
                                'regular_links': regular,
                                'test_links': test,
                                'order_id': str(order.id)
                            }
                        )
                    except Exception as e:
                        logger.error(f"Failed to log link grant: {e}")

            return True, None

        except Exception as e:
            logger.error(f"Error granting links: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def get_order_summary(order: Order) -> Dict[str, Any]:
        """
        Get comprehensive order summary.

        Args:
            order: Order to summarize

        Returns:
            Dictionary with order summary data
        """
        return {
            'id': str(order.id),
            'order_number': order.order_number,
            'status': order.status,
            'plan': {
                'code': order.plan.code,
                'name': order.plan.name,
                'price': float(order.payment_amount)
            },
            'event': {
                'type': order.event_type,
                'name': order.event_type_name
            },
            'payment': {
                'amount': float(order.payment_amount),
                'method': order.payment_method,
                'status': order.payment_status,
                'received_at': order.payment_received_at.isoformat() if order.payment_received_at else None
            },
            'links': {
                'regular_granted': order.granted_regular_links,
                'test_granted': order.granted_test_links,
                'regular_used': order.used_links_count,
                'remaining': order.remaining_links
            },
            'approval': {
                'approved': order.status == OrderStatus.APPROVED,
                'approved_by': order.approved_by.username if order.approved_by else None,
                'approved_at': order.approved_at.isoformat() if order.approved_at else None,
                'notes': order.admin_notes
            },
            'has_invitation': hasattr(order, 'invitation') and order.invitation is not None,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat()
        }

    @staticmethod
    def update_order_status(
        order: Order,
        new_status: str,
        admin: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Update order status with validation.

        Args:
            order: Order to update
            new_status: New status (from OrderStatus choices)
            admin: Admin user making the change

        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Validate status
            valid_statuses = [choice[0] for choice in OrderStatus.choices]
            if new_status not in valid_statuses:
                return False, f"Invalid status: {new_status}"

            with transaction.atomic():
                order.status = new_status

                # Set approved_by and approved_at for approval/rejection
                if new_status in [OrderStatus.APPROVED, OrderStatus.REJECTED] and admin:
                    order.approved_by = admin
                    order.approved_at = timezone.now()

                order.save()

            logger.info(f"Order {order.order_number} status updated to {new_status}")
            return True, None

        except Exception as e:
            logger.error(f"Error updating order status: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def can_create_invitation(order: Order) -> Tuple[bool, Optional[str]]:
        """
        Check if an invitation can be created for this order.

        Args:
            order: Order to check

        Returns:
            Tuple of (can_create, reason_if_not)
        """
        # Check if order already has an invitation
        if hasattr(order, 'invitation') and order.invitation:
            return False, "Order already has an invitation"

        # Check order status
        if order.status not in [OrderStatus.APPROVED, OrderStatus.PENDING_APPROVAL]:
            return False, f"Order must be approved or pending approval (current: {order.status})"

        # Check if there are remaining links
        if order.remaining_links <= 0:
            return False, "No remaining invitation links"

        return True, None
