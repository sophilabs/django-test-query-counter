from unittest import mock

from django.test import TestCase
from rest_framework.test import APIClient

from django_api_query_count.query_count import QueryCountAPIClient


class TestAPIClient(TestCase):

    def test_connection(self):
        self.assertIsNotNone(QueryCountAPIClient().connection)

    @classmethod
    def _test_method(cls, method_name):
        with mock.patch.object(APIClient, method_name) as mock_method:
            query_count_api_client = QueryCountAPIClient()
            bound_method = getattr(query_count_api_client, method_name)
            bound_method('some_path', None)
            mock_method.assert_called_with('some_path', None)

    def test_get(self):
        self._test_method('get')

    def test_post(self):
        self._test_method('post')

    def test_put(self):
        self._test_method('put')

    def test_patch(self):
        self._test_method('patch')

    def test_delete(self):
        self._test_method('delete')

    def test_options(self):
        self._test_method('options')
