from django.db import connection
from django.test import TestCase


class TestMiddleWare(TestCase):

    def test_middleware_called(self):
        response = self.client.get('/url-1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(hasattr(connection, 'queries'))
