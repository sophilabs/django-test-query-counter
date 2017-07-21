from django.conf import settings
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

    def test_add_middleware_twice(self):
        RequestQueryCountConfig.add_middleware()
        RequestQueryCountConfig.add_middleware()

        middlewares = settings.MIDDLEWARE
        self.assertEqual(len(middlewares), 1)
        self.assertEqual(middlewares[0],
                         'test_query_counter.middleware.Middleware'
                         )

    def test_list_middlewares_types(self):
        with override_settings(MIDDLEWARE=[]):
            RequestQueryCountConfig.add_middleware()
            self.assertEqual(settings.MIDDLEWARE, [
                             'test_query_counter.middleware.Middleware'
                             ])
        with override_settings(MIDDLEWARE=()):
            RequestQueryCountConfig.add_middleware()
            self.assertEqual(
                settings.MIDDLEWARE,
                ('test_query_counter.middleware.Middleware',)
            )
        with override_settings(MIDDLEWARE='some_nasty_thing'):
            with self.assertRaises(Exception):
                RequestQueryCountConfig.add_middleware()
