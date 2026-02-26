# Test settings - Uses SQLite instead of PostgreSQL for testing without Docker
from .settings import *

# Override database to use SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable Redis for testing (use in-memory channel layer)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Disable Celery for testing
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAG ATES = True

# Simplified caching for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

print("=" * 80)
print("USING TEST SETTINGS WITH SQLITE DATABASE")
print("This is for API testing without Docker/PostgreSQL")
print("=" * 80)
