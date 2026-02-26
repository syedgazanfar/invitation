"""
Custom permissions for the AI app.

This module provides permission classes for:
- Rate limiting based on user plan
- Ownership verification
- Subscription status checking
"""

from rest_framework import permissions
from django.conf import settings
from django.utils import timezone

from .models import AIUsageLog


class CanUseAIFeature(permissions.BasePermission):
    """
    Permission to check if a user can use AI features based on their plan
    and usage limits.
    
    Checks both daily token limits and per-feature request limits.
    """
    
    message = "AI feature usage limit exceeded or not available for your plan."
    
    def has_permission(self, request, view):
        """
        Check if the user has permission to use AI features.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: True if user can use the feature, False otherwise
        """
        # Allow anonymous users for specific endpoints if needed
        if not request.user or not request.user.is_authenticated:
            # Check if view allows anonymous access
            if getattr(view, 'allow_anonymous', False):
                return True
            return False
        
        # Check if user is active
        if not request.user.is_active:
            self.message = "User account is not active."
            return False
        
        # Get the feature type from the view
        feature_type = getattr(view, 'feature_type', None)
        
        # If no specific feature type, allow (basic check passed)
        if not feature_type:
            return True
        
        # Check rate limits
        return self.check_rate_limits(request.user, feature_type)
    
    def check_rate_limits(self, user, feature_type):
        """
        Check if user is within rate limits for a feature.
        
        Args:
            user: The user to check
            feature_type: The type of AI feature being used
            
        Returns:
            bool: True if within limits, False otherwise
        """
        # Get today's usage
        usage_today = AIUsageLog.get_user_usage_today(user)
        total_tokens_today = usage_today.get('total_tokens') or 0
        
        # Define limits based on user plan
        plan_limits = self.get_plan_limits(user)
        
        # Check if within daily token limit
        if total_tokens_today >= plan_limits['daily_token_limit']:
            self.message = (
                f"Daily token limit exceeded. "
                f"Limit: {plan_limits['daily_token_limit']}, "
                f"Used: {total_tokens_today}"
            )
            return False
        
        # Get feature-specific limits
        feature_limits = plan_limits.get('feature_limits', {})
        
        # Check feature-specific daily request limit
        max_requests_key = f'{feature_type}_max_requests'
        max_requests_per_day = feature_limits.get(max_requests_key, 100)
        
        # Get today's usage for this specific feature
        today = timezone.now().date()
        feature_usage_today = AIUsageLog.objects.filter(
            user=user,
            feature_type=feature_type,
            created_at__date=today,
            success=True
        ).count()
        
        # Check if within feature-specific limit
        if feature_usage_today >= max_requests_per_day:
            self.message = (
                f"Daily request limit for {feature_type} exceeded. "
                f"Limit: {max_requests_per_day}, "
                f"Used: {feature_usage_today}"
            )
            return False
        
        # Check monthly token limit
        month_usage = AIUsageLog.get_user_usage_this_month(user)
        total_tokens_this_month = month_usage.get('total_tokens') or 0
        
        if total_tokens_this_month >= plan_limits['monthly_token_limit']:
            self.message = (
                f"Monthly token limit exceeded. "
                f"Limit: {plan_limits['monthly_token_limit']}, "
                f"Used: {total_tokens_this_month}"
            )
            return False
        
        return True
    
    def get_plan_limits(self, user):
        """
        Get AI usage limits based on user's plan.
        
        Args:
            user: The user to check
            
        Returns:
            dict: Limits containing daily_token_limit, monthly_token_limit, 
                  and feature_limits
        """
        # Default limits (free tier)
        default_limits = {
            'daily_token_limit': 10000,
            'monthly_token_limit': 100000,
            'feature_limits': {
                'photo_analysis_max_requests': 10,
                'color_extraction_max_requests': 20,
                'mood_detection_max_requests': 20,
                'message_generation_max_requests': 20,
                'template_recommendation_max_requests': 50,
                'hashtag_generation_max_requests': 30,
                'smart_suggestions_max_requests': 50,
            }
        }
        
        # Try to get user's plan
        try:
            # Check if user has an active order with a plan
            from apps.invitations.models import Order
            order = Order.objects.filter(
                user=user,
                status='APPROVED'
            ).select_related('plan').first()
            
            if order and order.plan:
                plan_code = order.plan.code
                
                if plan_code == 'BASIC':
                    return {
                        'daily_token_limit': 5000,
                        'monthly_token_limit': 50000,
                        'feature_limits': {
                            'photo_analysis_max_requests': 5,
                            'color_extraction_max_requests': 10,
                            'mood_detection_max_requests': 10,
                            'message_generation_max_requests': 10,
                            'template_recommendation_max_requests': 20,
                            'hashtag_generation_max_requests': 15,
                            'smart_suggestions_max_requests': 30,
                        }
                    }
                elif plan_code == 'PREMIUM':
                    return {
                        'daily_token_limit': 15000,
                        'monthly_token_limit': 200000,
                        'feature_limits': {
                            'photo_analysis_max_requests': 20,
                            'color_extraction_max_requests': 40,
                            'mood_detection_max_requests': 40,
                            'message_generation_max_requests': 50,
                            'template_recommendation_max_requests': 100,
                            'hashtag_generation_max_requests': 50,
                            'smart_suggestions_max_requests': 100,
                        }
                    }
                elif plan_code == 'LUXURY':
                    return {
                        'daily_token_limit': 50000,
                        'monthly_token_limit': 500000,
                        'feature_limits': {
                            'photo_analysis_max_requests': 100,
                            'color_extraction_max_requests': 100,
                            'mood_detection_max_requests': 100,
                            'message_generation_max_requests': 200,
                            'template_recommendation_max_requests': 500,
                            'hashtag_generation_max_requests': 200,
                            'smart_suggestions_max_requests': 500,
                        }
                    }
        except Exception:
            pass
        
        return default_limits
    
    def get_remaining_quota(self, user, feature_type=None):
        """
        Get remaining quota for a user.
        
        Args:
            user: The user to check
            feature_type: Optional specific feature to check
            
        Returns:
            dict: Remaining quota information
        """
        limits = self.get_plan_limits(user)
        today_usage = AIUsageLog.get_user_usage_today(user)
        month_usage = AIUsageLog.get_user_usage_this_month(user)
        
        tokens_used_today = today_usage.get('total_tokens') or 0
        tokens_used_this_month = month_usage.get('total_tokens') or 0
        
        result = {
            'daily_tokens_remaining': max(0, limits['daily_token_limit'] - tokens_used_today),
            'monthly_tokens_remaining': max(0, limits['monthly_token_limit'] - tokens_used_this_month),
            'daily_token_limit': limits['daily_token_limit'],
            'monthly_token_limit': limits['monthly_token_limit'],
        }
        
        if feature_type:
            max_requests = limits['feature_limits'].get(
                f'{feature_type}_max_requests', 100
            )
            today = timezone.now().date()
            used_today = AIUsageLog.objects.filter(
                user=user,
                feature_type=feature_type,
                created_at__date=today,
                success=True
            ).count()
            
            result['feature'] = {
                'type': feature_type,
                'requests_remaining': max(0, max_requests - used_today),
                'daily_limit': max_requests,
                'used_today': used_today
            }
        
        return result


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners of an object to edit or delete it.
    
    Read permissions are allowed to any request.
    """
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the owner of the object.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: True if user is owner or request is safe, False otherwise
        """
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for the owner
        return obj.user == request.user


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of an object to access it.
    
    More restrictive than IsOwnerOrReadOnly - requires ownership for all methods.
    """
    
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the user is the owner of the object.
        
        Args:
            request: The incoming request
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            bool: True if user is owner, False otherwise
        """
        return obj.user == request.user


class HasActiveSubscription(permissions.BasePermission):
    """
    Permission to check if user has an active subscription/plan.
    
    Used for premium features that require an active order.
    """
    
    message = "Active subscription required to use AI features."
    
    def has_permission(self, request, view):
        """
        Check if user has an active subscription.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: True if user has active subscription, False otherwise
        """
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if user has any approved orders
        try:
            from apps.invitations.models import Order
            return Order.objects.filter(
                user=request.user,
                status='APPROVED'
            ).exists()
        except Exception:
            return False


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admin users to modify resources.
    
    Read permissions are allowed to any authenticated request.
    """
    
    def has_permission(self, request, view):
        """
        Check if user is admin or request is safe.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: True if admin or safe method, False otherwise
        """
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class RateLimitByIP(permissions.BasePermission):
    """
    Permission to rate limit by IP address for anonymous users.
    
    Used for public endpoints that need rate limiting.
    """
    
    message = "Rate limit exceeded. Please try again later."
    
    def has_permission(self, request, view):
        """
        Check if IP is within rate limits.
        
        Args:
            request: The incoming request
            view: The view being accessed
            
        Returns:
            bool: True if within limits, False otherwise
        """
        # Only apply to anonymous users
        if request.user and request.user.is_authenticated:
            return True
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Check cache for rate limit
        from django.core.cache import cache
        cache_key = f"rate_limit:{ip}:{view.__class__.__name__}"
        requests = cache.get(cache_key, 0)
        
        # Default: 10 requests per minute for anonymous users
        limit = getattr(view, 'anonymous_rate_limit', 10)
        
        if requests >= limit:
            return False
        
        # Increment counter
        cache.set(cache_key, requests + 1, 60)  # 1 minute expiry
        return True
