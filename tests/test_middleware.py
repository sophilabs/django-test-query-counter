import os
from os import path
from unittest import TestCase, TestSuite, mock
from unittest.mock import MagicMock

import django
from django.core.exceptions import MiddlewareNotUsed
from django.test import Client, TransactionTestCase, override_settings
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.manager import RequestQueryCountManager
from test_query_counter.middleware import Middleware

from tests.runner import MiniTestRunner


class TestMiddleWare(TestCase):
    @classmethod
    def setUpClass(cls):
        django.setup()

    def setUp(self):
        self.test_runner = MiniTestRunner()

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
            Client().get('/url-1')
            self.assertEqual(mocked.call_count, 1)

    def test_case_injected_one_test(self):
        class Test(TransactionTestCase):
            def test_foo(self):
                Client().get('/url-1')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')
        self.assertEqual(RequestQueryCountManager.queries.total, 1)

    def test_case_injected_two_tests(self):
        class Test(TransactionTestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        test_suite.addTest(Test('test_bar'))
        self.test_runner.run_tests(test_labels='')
        self.assertEqual(RequestQueryCountManager.queries.total, 2)

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_case_disable_setting(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        test_suite.addTest(Test('test_bar'))
        self.test_runner.run_tests(test_labels='')
        self.assertIsNone(RequestQueryCountManager.queries)

    @override_settings(TEST_QUERY_COUNTER={'ENABLE': False})
    def test_disabled(self):
        mock_get_response = object()
        with self.assertRaises(MiddlewareNotUsed):
            Middleware(mock_get_response)

    def test_json_exists(self):
        class Test(TransactionTestCase):
            def test_foo(self):
                self.client.get('/url-1')

        self.assertFalse(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')

        self.assertTrue(
            path.exists(
                RequestQueryCountConfig.get_setting('DETAIL_PATH')
            ),
            'JSON doesn\'t exists in {}'.format(
                RequestQueryCountConfig.get_setting('DETAIL_PATH')
            )
        )
