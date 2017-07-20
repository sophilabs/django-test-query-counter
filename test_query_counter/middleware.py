from django.core.exceptions import MiddlewareNotUsed
from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext
from test_query_counter.apps import RequestQueryCountConfig


class Middleware(object):
    """
    Intercepts queries in a request and put it in the query container provided
    by the RequestQueryCountConfig, during the wrapped test setUp method.

    The middleware is intended to be automatically added

    If the query container is None, then the middleware is not executed.
    """

    def __init__(self, get_response=None):
        if get_response is None or not RequestQueryCountConfig.enabled():
            raise MiddlewareNotUsed()
        self.get_response = get_response

    def __call__(self, request):
        container = RequestQueryCountConfig.get_testcase_container()
        if container is None:
            # It is not necessary to capture queries
            return self.get_response(request)

        with CaptureQueriesContext(connections[DEFAULT_DB_ALIAS]) as context:
            response = self.get_response(request)

        query_container = RequestQueryCountConfig.get_testcase_container()
        query_container.add(request, context.captured_queries)

        return response
