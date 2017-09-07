import unittest
from io import StringIO
from unittest import TextTestRunner

from django.test.runner import DiscoverRunner


# Simple class that doesn't output to the standard output
class StringIOTextRunner(TextTestRunner):
    def __init__(self, *args, **kwargs):
        kwargs['stream'] = StringIO()
        super().__init__(*args, **kwargs)


class MiniTestRunner(DiscoverRunner):
    suite = None
    test_runner = StringIOTextRunner

    def setup_test_environment(self, **kwargs):
        unittest.installHandler()

    def teardown_test_environment(self, **kwargs):
        unittest.removeHandler()

    def setup_databases(self, **kwargs):
        pass

    def teardown_databases(self, old_config, **kwargs):
        pass

    def run_checks(self):
        pass

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        return self.suite
