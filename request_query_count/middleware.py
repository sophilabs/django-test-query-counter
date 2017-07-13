from django.db import DEFAULT_DB_ALIAS, connections
from django.test.utils import CaptureQueriesContext

from request_query_count.apps import RequestQueryCountConfig


class Middleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not RequestQueryCountConfig.enabled():
            # It is not necessary to capture queries
            return self.get_response(request)

        with CaptureQueriesContext(connections[DEFAULT_DB_ALIAS]) as context:
            response = self.get_response(request)

        query_container = RequestQueryCountConfig.get_testcase_container()
        query_container.add(request, context.captured_queries)

        return response
