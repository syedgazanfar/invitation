"""
Django admin must be movable off /admin/: in production the Next.js frontend
owns /admin/* (its admin dashboard), so nginx can't send that prefix to Django.
"""
import importlib

from django.test import SimpleTestCase, override_settings
from django.urls import clear_url_caches, reverse

import config.urls


class AdminPathTest(SimpleTestCase):
    def _reload_urls(self):
        clear_url_caches()
        importlib.reload(config.urls)

    def tearDown(self):
        self._reload_urls()

    def test_default_admin_path_is_unchanged(self):
        self._reload_urls()
        self.assertEqual(reverse('admin:index'), '/admin/')

    @override_settings(DJANGO_ADMIN_PATH='django-admin/')
    def test_admin_path_follows_setting(self):
        self._reload_urls()
        self.assertEqual(reverse('admin:index'), '/django-admin/')
