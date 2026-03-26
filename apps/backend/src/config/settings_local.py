"""
Local development settings.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings_local python src/manage.py runserver

Or add to .env:
    DJANGO_SETTINGS_MODULE=config.settings_local

Overrides production settings with SQLite, in-memory cache/channels, and
synchronous Celery so you can run the backend without Docker, Redis, or
PostgreSQL installed.
"""
from .settings import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
DEBUG = True
SECRET_KEY = 'local-dev-secret-key-do-not-use-in-production'
ALLOWED_HOSTS = ['*']

# ---------------------------------------------------------------------------
# Database — SQLite (no PostgreSQL needed)
# ---------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_local.sqlite3',  # noqa: F405
    }
}

# ---------------------------------------------------------------------------
# Cache — local memory (no Redis needed)
# ---------------------------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'default',
    },
    'ai': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'ai-cache',
    },
}

# ---------------------------------------------------------------------------
# Django Channels — in-memory layer (no Redis needed)
# ---------------------------------------------------------------------------
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ---------------------------------------------------------------------------
# Celery — run tasks eagerly in the same process (no worker needed)
# ---------------------------------------------------------------------------
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# ---------------------------------------------------------------------------
# Email — print to console
# ---------------------------------------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ---------------------------------------------------------------------------
# AI — always mock in local dev
# ---------------------------------------------------------------------------
AI_MOCK_MODE = True

# ---------------------------------------------------------------------------
# CORS — allow all for local dev
# ---------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# ---------------------------------------------------------------------------
# Health checks — remove Celery check (no broker in local mode)
# ---------------------------------------------------------------------------
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'health_check.contrib.celery']  # noqa: F405
