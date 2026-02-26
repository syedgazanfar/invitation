"""
Celery tasks for the AI app.

This module contains background tasks for AI operations including:
- Async photo analysis
- Batch message generation
- Usage report generation
- Cleanup tasks
"""

import logging
from typing import List, Dict

from celery import shared_task
from django.contrib.auth import get_user_model

from .models import PhotoAnalysis, GeneratedMessage, AIUsageLog
from .services import PhotoAnalysisService, MessageGenerationService


logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_photo_async(self, image_url: str, user_id: str, order_id: str = None, **options):
    """
    Analyze a photo asynchronously.
    
    Args:
        image_url: URL of the image to analyze
        user_id: ID of the user requesting analysis
        event_id: Optional ID of the associated event
        **options: Additional analysis options
        
    Returns:
        Dict with analysis results
    """
    try:
        user = User.objects.get(id=user_id)
        event = None
        if order_id:
            from apps.invitations.models import Order
            order = Order.objects.get(id=order_id)
        
        service = PhotoAnalysisService()
        result = service.analyze_photo(
            image_url=image_url,
            user=user,
            order=order,
            extract_colors=options.get('extract_colors', True),
            detect_mood=options.get('detect_mood', True),
            generate_recommendations=options.get('generate_recommendations', True)
        )
        
        return {
            'status': 'success',
            'analysis_id': str(result.id),
            'primary_colors': result.primary_colors,
            'mood': result.mood,
        }
        
    except Exception as exc:
        logger.error(f"Photo analysis task failed: {exc}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def generate_messages_async(
    self,
    context: Dict,
    style: str,
    num_options: int,
    user_id: str,
    order_id: str = None
):
    """
    Generate messages asynchronously.
    
    Args:
        context: Message context
        style: Message style
        num_options: Number of options to generate
        user_id: ID of the user requesting generation
        event_id: Optional ID of the associated event
        
    Returns:
        Dict with generated messages
    """
    try:
        user = User.objects.get(id=user_id)
        event = None
        if order_id:
            from apps.invitations.models import Order
            order = Order.objects.get(id=order_id)
        
        service = MessageGenerationService()
        result = service.generate_messages(
            context=context,
            style=style,
            num_options=num_options,
            user=user,
            event=event
        )
        
        return {
            'status': 'success',
            'message_id': str(result.id),
            'options': result.generated_options,
            'style_used': result.style_used,
            'tokens_used': result.tokens_used,
        }
        
    except Exception as exc:
        logger.error(f"Message generation task failed: {exc}")
        raise self.retry(exc=exc)


@shared_task
def generate_daily_usage_report():
    """
    Generate a daily usage report for AI features.
    
    Returns:
        Dict with usage statistics
    """
    from django.utils import timezone
    from datetime import timedelta
    
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get usage stats for yesterday
    logs = AIUsageLog.objects.filter(created_at__date=yesterday)
    
    stats = {
        'date': str(yesterday),
        'total_requests': logs.count(),
        'successful_requests': logs.filter(success=True).count(),
        'failed_requests': logs.filter(success=False).count(),
        'total_tokens': sum(log.tokens_used for log in logs.filter(success=True)),
        'requests_by_feature': {},
        'top_users': [],
    }
    
    # Breakdown by feature
    for feature_type, _ in AIUsageLog.FEATURE_CHOICES:
        count = logs.filter(feature_type=feature_type).count()
        if count > 0:
            stats['requests_by_feature'][feature_type] = count
    
    # Top users by token usage
    top_users = (
        logs.filter(success=True)
        .values('user__email')
        .annotate(
            total_tokens=models.Sum('tokens_used'),
            request_count=models.Count('id')
        )
        .order_by('-total_tokens')[:10]
    )
    stats['top_users'] = list(top_users)
    
    logger.info(f"Daily AI usage report generated for {yesterday}")
    return stats


@shared_task
def cleanup_old_analyses(days: int = 90):
    """
    Clean up old photo analyses to free up storage.
    
    Args:
        days: Delete analyses older than this many days
        
    Returns:
        Dict with cleanup results
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_analyses = PhotoAnalysis.objects.filter(created_at__lt=cutoff_date)
    count = old_analyses.count()
    old_analyses.delete()
    
    result = {
        'deleted_count': count,
        'cutoff_date': str(cutoff_date),
        'status': 'success'
    }
    
    logger.info(f"Cleaned up {count} old photo analyses")
    return result


@shared_task
def cleanup_old_usage_logs(days: int = 365):
    """
    Clean up old usage logs to free up database space.
    
    Args:
        days: Delete logs older than this many days
        
    Returns:
        Dict with cleanup results
    """
    from django.utils import timezone
    from datetime import timedelta
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    old_logs = AIUsageLog.objects.filter(created_at__lt=cutoff_date)
    count = old_logs.count()
    old_logs.delete()
    
    result = {
        'deleted_count': count,
        'cutoff_date': str(cutoff_date),
        'status': 'success'
    }
    
    logger.info(f"Cleaned up {count} old usage logs")
    return result


@shared_task
def send_usage_alerts():
    """
    Send alerts to users approaching their usage limits.
    
    Returns:
        Dict with alert results
    """
    from django.utils import timezone
    
    alerts_sent = 0
    
    # Get users who have used more than 80% of their daily limit
    users_to_notify = []
    
    for user in User.objects.filter(is_active=True):
        usage_today = AIUsageLog.get_user_usage_today(user)
        total_tokens = usage_today.get('total_tokens') or 0
        
        # Check against plan limits (simplified)
        daily_limit = 10000  # Default limit
        
        if total_tokens > daily_limit * 0.8:
            users_to_notify.append({
                'user_id': user.id,
                'email': user.email,
                'usage_percentage': (total_tokens / daily_limit) * 100,
                'tokens_remaining': daily_limit - total_tokens
            })
    
    # TODO: Send email notifications
    # for user_info in users_to_notify:
    #     send_mail(...)
    
    logger.info(f"Sent usage alerts to {len(users_to_notify)} users")
    
    return {
        'alerts_sent': len(users_to_notify),
        'users': users_to_notify,
        'status': 'success'
    }


@shared_task
def batch_analyze_photos(image_urls: List[str], user_id: str, order_id: str = None):
    """
    Analyze multiple photos in batch.
    
    Args:
        image_urls: List of image URLs to analyze
        user_id: ID of the user requesting analysis
        event_id: Optional ID of the associated event
        
    Returns:
        Dict with batch results
    """
    results = []
    errors = []
    
    for url in image_urls:
        try:
            result = analyze_photo_async.delay(
                image_url=url,
                user_id=user_id,
                order_id=order_id
            )
            results.append({
                'image_url': url,
                'task_id': result.id,
                'status': 'queued'
            })
        except Exception as e:
            errors.append({
                'image_url': url,
                'error': str(e)
            })
    
    return {
        'total': len(image_urls),
        'queued': len(results),
        'errors': len(errors),
        'results': results,
        'error_details': errors,
    }


# Import models at the end to avoid circular imports
from django.db import models
