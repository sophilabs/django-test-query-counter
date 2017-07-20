from django.test import TestCase, override_settings

from test_query_counter.apps import RequestQueryCountConfig


class TestAppConfig(TestCase):
    def test_default_enabled(self):
        self.assertTrue(RequestQueryCountConfig.enabled())

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_override_disabled(self):
        self.assertFalse(RequestQueryCountConfig.enabled())

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': True})
    def test_override_enabled(self):
        self.assertTrue(RequestQueryCountConfig.enabled())
