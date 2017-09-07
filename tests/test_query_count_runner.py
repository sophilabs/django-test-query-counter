import os
import unittest
from os import path
from unittest import TestSuite

import django.test.testcases as django_testcase
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.manager import RequestQueryCountManager
from test_query_counter.query_count import (TestResultQueryContainer,
                                            exclude_query_count)

from tests.runner import MiniTestRunner


class TestRunnerTest(unittest.TestCase):
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

    def test_empty_test(self):
        class Test(django_testcase.TestCase):
            def test_foo(self):
                pass

            def test_bar(self):
                pass

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        test_suite.addTest(Test('test_bar'))
        self.test_runner.run_tests(test_labels='')

        # check for empty tests
        self.assertIsNotNone(RequestQueryCountManager, 'queries')
        self.assertIsInstance(RequestQueryCountManager.queries,
                              TestResultQueryContainer)
        self.assertEqual(RequestQueryCountManager.queries.total, 0)

        # check if files are generated
        self.assertTrue(path.exists(
            RequestQueryCountConfig.get_setting('SUMMARY_PATH'))
        )
        self.assertTrue(path.isfile(
            RequestQueryCountConfig.get_setting('SUMMARY_PATH'))
        )
        self.assertTrue(path.exists(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )
        self.assertTrue(path.isfile(
            RequestQueryCountConfig.get_setting('DETAIL_PATH'))
        )

    @classmethod
    def get_id(cls, test_class, method_name):
        return "{}.{}.{}".format(test_class.__module__,
                                 test_class.__qualname__,
                                 method_name)

    def test_runner_include_queries(self):
        class Test(django_testcase.TestCase):
            def test_foo(self):
                self.client.get('/url-1')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')

        # Assert it ran one test
        self.assertEqual(len(RequestQueryCountManager.queries.queries_by_testcase), 1)

        test_foo_id = self.get_id(Test, 'test_foo')
        self.assertIn(test_foo_id,
                      RequestQueryCountManager.queries.queries_by_testcase)

        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[test_foo_id].total, 1
        )

    def test_excluded_test(self):
        class Test(django_testcase.TestCase):
            @exclude_query_count()
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-1')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        test_suite.addTest(Test('test_bar'))
        self.test_runner.run_tests(test_labels='')

        # Assert test_foo has excluded queries
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_foo')].total,
            0
        )
        # Assert test_bar has some queries
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_bar')].total,
            1
        )

    def test_excluded_class(self):
        @exclude_query_count()
        class Test(django_testcase.TestCase):
            def test_foo(self):
                self.client.get('path-1')

            def test_bar(self):
                self.client.get('path-1')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        test_suite.addTest(Test('test_bar'))
        self.test_runner.run_tests(test_labels='')

        # Assert test_foo has excluded queries
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_foo')].total,
            0
        )
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_bar')].total,
            0
        )

    def test_conditional_exclude(self):
        class Test(django_testcase.TestCase):
            @exclude_query_count(path='url-2')
            def test_exclude_path(self):
                self.client.get('/url-1')
                self.client.post('/url-2')

            @exclude_query_count(method='post')
            def test_exclude_method(self):
                self.client.get('/url-1')
                self.client.post('/url-2')

            @exclude_query_count(count=2)
            def test_exclude_count(self):
                self.client.get('/url-1')
                self.client.post('/url-2')
                #  succesive url are additive
                self.client.put('/url-3')
                self.client.put('/url-3')
                self.client.put('/url-3')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_exclude_path'))
        test_suite.addTest(Test('test_exclude_method'))
        test_suite.addTest(Test('test_exclude_count'))
        self.test_runner.run_tests(test_labels='')

        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_exclude_path')].total,
            1
        )
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_exclude_method')].total,
            1
        )
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_exclude_count')].total,
            3
        )

    def test_nested_method_exclude(self):
        class Test(django_testcase.TestCase):
            @exclude_query_count(path='url-1')
            @exclude_query_count(method='post')
            @exclude_query_count(path='url-3')
            def test_foo(self):
                self.client.get('/url-1')
                self.client.post('/url-2')
                self.client.put('/url-3')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')

        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_foo')].total,
            0
        )

    def test_nested_class_method_exclude(self):
        @exclude_query_count(path='url-1')
        class Test(django_testcase.TestCase):
            @exclude_query_count(method='post')
            def test_foo(self):
                self.client.get('/url-1')
                self.client.post('/url-2')
                self.client.put('/url-3')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')

        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_foo')].total,
            1
        )

    def test_custom_setup_teardown(self):
        class Test(django_testcase.TestCase):
            def setUp(self):
                pass

            def tearDown(self):
                pass

            def test_foo(self):
                self.client.get('/url-1')

        test_suite = self.test_runner.suite = TestSuite()
        test_suite.addTest(Test('test_foo'))
        self.test_runner.run_tests(test_labels='')

        self.assertIn(
            self.get_id(Test, 'test_foo'),
            RequestQueryCountManager.queries.queries_by_testcase
        )
        self.assertEqual(
            RequestQueryCountManager.queries.queries_by_testcase[
                self.get_id(Test, 'test_foo')].total,
            1
        )
