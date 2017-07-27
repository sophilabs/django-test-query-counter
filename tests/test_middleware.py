import os
from io import StringIO
from os import path
from unittest import TestSuite, TextTestRunner, mock
from unittest.mock import MagicMock

from django.core.exceptions import MiddlewareNotUsed
from django.test import TestCase, override_settings
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.middleware import Middleware


class TestMiddleWare(TestCase):

    def setUp(self):
        # Simple class that doesn't output to the standard output
        class StringIOTextRunner(TextTestRunner):
            def __init__(self, *args, **kwargs):
                kwargs['stream'] = StringIO()
                super().__init__(*args, **kwargs)

        self.test_runner = StringIOTextRunner()

    def tearDown(self):
        try:
            os.remove(RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        except FileNotFoundError:
            pass
        try:
            os.remove(RequestQueryCountConfig.get_setting('SUMMARY_PATH'))
        except FileNotFoundError:
            pass

    def test_middleware_called(self):
        with mock.patch('test_query_counter.middleware.Middleware',
                        new=MagicMock(wraps=Middleware)) as mocked:
            self.client.get('/url-1')
            self.assertEqual(mocked.call_count, 1)

    def test_case_injected_one_test(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))

        result = self.test_runner.run(suite)

        self.assertEqual(result.queries.total, 1)

    def test_case_injected_two_tests(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))
        suite.addTest(Test('test_bar'))

        result = self.test_runner.run(suite)

        self.assertEqual(result.queries.total, 2)

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_case_disable_setting(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))
        suite.addTest(Test('test_bar'))

        result = self.test_runner.run(suite)
        self.assertFalse(hasattr(result, 'queries'))

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_disabled(self):
        mock_get_response = object()
        with self.assertRaises(MiddlewareNotUsed):
            Middleware(mock_get_response)

    def test_json_exists(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))

        self.assertFalse(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )
        self.test_runner.run(suite)
        self.assertTrue(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )
