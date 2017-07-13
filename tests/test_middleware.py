from io import StringIO
from unittest import TestSuite, TextTestRunner

from django.db import connection
from django.test import TestCase


class TestMiddleWare(TestCase):
    def setUp(self):
        # Simple class that doesn't output to the standard output
        class StringIOTextRunner(TextTestRunner):
            def __init__(self, *args, **kwargs):
                kwargs['stream'] = StringIO()
                super().__init__(*args, **kwargs)

        self.test_runner = StringIOTextRunner()

    def test_middleware_called(self):
        response = self.client.get('/url-1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(connection, 'queries'))

    def test_api_test_case_injected(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

            def test_bar(self):
                self.client.get('/url-2')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))
        suite.addTest(Test('test_bar'))
        self.test_runner.run(suite)

        self.assertEqual
