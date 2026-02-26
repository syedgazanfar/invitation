"""
Signal handlers for the AI app.

This module contains Django signal handlers for AI-related events.
"""

import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

from .models import PhotoAnalysis, GeneratedMessage


logger = logging.getLogger(__name__)


@receiver(post_save, sender=PhotoAnalysis)
def invalidate_photo_analysis_cache(sender, instance, created, **kwargs):
    """
    Invalidate cache when a photo analysis is updated.
    
    Args:
        sender: Model class
        instance: PhotoAnalysis instance
        created: Whether this is a new instance
        **kwargs: Additional signal arguments
    """
    if not created:
        # Invalidate cache for this analysis
        cache_key = f"ai:analysis:{instance.image_url}"
        cache.delete(cache_key)
        
        # Invalidate related caches
        cache.delete(f"ai:colors:{instance.image_url}")
        cache.delete(f"ai:mood:{instance.image_url}")
        
        logger.debug(f"Invalidated cache for photo analysis {instance.id}")


@receiver(post_delete, sender=PhotoAnalysis)
def cleanup_photo_analysis(sender, instance, **kwargs):
    """
    Clean up cache when a photo analysis is deleted.
    
    Args:
        sender: Model class
        instance: PhotoAnalysis instance
        **kwargs: Additional signal arguments
    """
    # Invalidate all related caches
    cache.delete(f"ai:analysis:{instance.image_url}")
    cache.delete(f"ai:colors:{instance.image_url}")
    cache.delete(f"ai:mood:{instance.image_url}")
    
    logger.debug(f"Cleaned up cache for deleted photo analysis {instance.id}")


@receiver(post_save, sender=GeneratedMessage)
def invalidate_message_cache(sender, instance, created, **kwargs):
    """
    Invalidate cache when a generated message is updated.
    
    Args:
        sender: Model class
        instance: GeneratedMessage instance
        created: Whether this is a new instance
        **kwargs: Additional signal arguments
    """
    if not created:
        # Build cache key based on context and style
        cache_key = f"ai:messages:{instance.context}:{instance.style_used}"
        cache.delete(cache_key)
        
        logger.debug(f"Invalidated cache for generated message {instance.id}")
