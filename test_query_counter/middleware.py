from django.core.exceptions import MiddlewareNotUsed
from django.core.signals import request_started
from django.db import DEFAULT_DB_ALIAS, connections, reset_queries
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.manager import RequestQueryCountManager

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django < 1.10
    # Works perfectly for everyone using MIDDLEWARE_CLASSES
    MiddlewareMixin = object


class Middleware(MiddlewareMixin):
    """
    Intercepts queries in a request and put it in the query container provided
    by the RequestQueryCountConfig, during the wrapped test setUp method.

    The middleware is intended to be automatically added

    If the query container is None, then the middleware is not executed.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not RequestQueryCountConfig.enabled():
            raise MiddlewareNotUsed()
        self.force_debug_cursor = False
        self.initial_queries = 0
        self.final_queries = None
        self.connection = connections[DEFAULT_DB_ALIAS]

    def process_request(self, _):
        if RequestQueryCountManager.get_testcase_container():
            # Took from django.test.utils.CaptureQueriesContext
            self.force_debug_cursor = self.connection.force_debug_cursor
            self.connection.force_debug_cursor = True
            self.initial_queries = len(self.connection.queries_log)
            self.final_queries = None
            request_started.disconnect(reset_queries)

    def process_response(self, request, response):
        if RequestQueryCountManager.get_testcase_container():
            # Took from django.test.utils.CaptureQueriesContext
            self.connection.force_debug_cursor = self.force_debug_cursor
            request_started.connect(reset_queries)
            final_queries = len(self.connection.queries_log)
            captured_queries = self.connection.queries[
                self.initial_queries:final_queries
            ]

            query_container = RequestQueryCountManager.get_testcase_container()
            query_container.add(request, captured_queries)

        return response
