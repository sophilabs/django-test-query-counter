from io import StringIO
from unittest import TestSuite, TextTestRunner, mock
from unittest.mock import MagicMock

from django.test import TestCase

from test_query_counter.middleware import Middleware


class TestMiddleWare(TestCase):
    def setUp(self):
        # Simple class that doesn't output to the standard output
        class StringIOTextRunner(TextTestRunner):
            def __init__(self, *args, **kwargs):
                kwargs['stream'] = StringIO()
                super().__init__(*args, **kwargs)

        self.test_runner = StringIOTextRunner()

    def test_middleware_called(self):
        with mock.patch('test_query_counter.middleware.Middleware',
                        new=MagicMock(wraps=Middleware)) as mocked:
            self.client.get('/url-1')
            self.assertGreater(len(mocked.call_args_list), 0)

    def test_api_test_case_injected(self):
        class Test(TestCase):
            def test_foo(self):
                self.client.get('/url-1')

        suite = TestSuite()
        suite.addTest(Test('test_foo'))

        result = self.test_runner.run(suite)

        self.assertEqual(result.queries.total, 1)
