import re
import shutil
from io import StringIO
from os import path
from tempfile import mkdtemp
from unittest import TestLoader, TextTestRunner

from django.test import TestCase

from request_query_count.query_count import (APIQueryCountTestCase,
                                             APIQueryCountTransactionTestCase,
                                             QueryCountCITestSuiteRunner,
                                             TestResultQueryContainer,
                                             exclude_query_count)


class TestQueryCountCITestSuiteRunner(TestCase):
    def setUp(self):
        # Simple class that doesn't output to the standard output
        class StringIOTextRunner(TextTestRunner):
            def __init__(self, *args, **kwargs):
                kwargs['stream'] = StringIO()
                super().__init__(*args, **kwargs)

        self.tempdir = mkdtemp(suffix='TestQueryCountCITestSuiteRunner')
        self.test_runner = QueryCountCITestSuiteRunner(
            output_dir=self.tempdir
        )
        self.test_runner.test_runner = StringIOTextRunner

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_empty_test(self):
        class Test(APIQueryCountTestCase):
            def test_foo(self):
                pass

            def test_bar(self):
                pass

        result = self.test_runner.run_suite(
            TestLoader().loadTestsFromTestCase(testCaseClass=Test)
        )

        # check for empty tests
        self.assertIsNotNone(result, 'queries')
        self.assertIsInstance(result.queries, TestResultQueryContainer)
        self.assertEqual(result.queries.total, 0)

        # check if files are generated
        self.assertTrue(path.exists(
            path.join(self.tempdir, 'query_count.json'))
        )
        self.assertTrue(path.isfile(
            path.join(self.tempdir, 'query_count.json'))
        )
        self.assertTrue(path.exists(
            path.join(self.tempdir, 'query_count_detail.json'))
        )
        self.assertTrue(path.isfile(
            path.join(self.tempdir, 'query_count_detail.json'))
        )

    def test_skipped_test(self):
        class Test(APIQueryCountTransactionTestCase):
            @exclude_query_count()
            def test_foo(self):
                pass

            def test_bar(self):
                pass

        result = self.test_runner.run_suite(
            TestLoader().loadTestsFromTestCase(testCaseClass=Test)
        )

        self.assertEqual(len(result.queries.queries_by_testcase), 1)
        self.assertIsNotNone(
            re.search(
                r'test_bar$',
                next(iter(result.queries.queries_by_testcase.keys()))
            )
        )
