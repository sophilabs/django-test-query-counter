import os
from io import StringIO
from os import path
from unittest import TestLoader, TextTestRunner, mock
from unittest.mock import MagicMock

from django.core.exceptions import MiddlewareNotUsed
from django.test import TestCase, override_settings
from django.test.runner import DiscoverRunner
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.manager import RequestQueryCountManager
from test_query_counter.middleware import Middleware


class TestMiddleWare(TestCase):

    def setUp(self):
        # Simple class that doesn't output to the standard output
        class StringIOTextRunner(TextTestRunner):
            def __init__(self, *args, **kwargs):
                kwargs['stream'] = StringIO()
                super().__init__(*args, **kwargs)

        self.test_runner = DiscoverRunner()
        self.test_runner.test_runner = StringIOTextRunner

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

        self.test_runner.setup_test_environment()
        self.test_runner.run_suite(TestLoader().loadTestsFromTestCase(
            testCaseClass=Test))
        self.test_runner.teardown_test_environment()

        self.assertEqual(RequestQueryCountManager.queries.total, 1)

    def test_case_injected_two_tests(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        self.test_runner.run_suite(
            TestLoader().loadTestsFromTestCase(testCaseClass=Test)
        )

        self.assertEqual(RequestQueryCountManager.queries.total, 2)

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_case_disable_setting(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        self.test_runner.run_tests(
            None,
            TestLoader().loadTestsFromTestCase(testCaseClass=Test)
        )
        self.assertIsNone(RequestQueryCountManager.queries)

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_disabled(self):
        mock_get_response = object()
        with self.assertRaises(MiddlewareNotUsed):
            Middleware(mock_get_response)

    def test_json_exists(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

        self.assertFalse(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )
        self.test_runner.run_tests(
            None,
            TestLoader().loadTestsFromTestCase(testCaseClass=Test)
        )
        self.assertTrue(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )
