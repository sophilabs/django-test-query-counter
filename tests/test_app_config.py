from django.test import TestCase, override_settings

from request_query_count.apps import RequestQueryCountConfig


class TestAppConfig(TestCase):
    def test_default_enabled(self):
        self.assertTrue(RequestQueryCountConfig.enabled())

    @override_settings(REQUEST_QUERY_COUNT={'ENABLE': False})
    def test_override_disabled(self):
        self.assertFalse(RequestQueryCountConfig.enabled())

    @override_settings(REQUEST_QUERY_COUNT={'ENABLE': True})
    def test_override_enabled(self):
        self.assertTrue(RequestQueryCountConfig.enabled())
