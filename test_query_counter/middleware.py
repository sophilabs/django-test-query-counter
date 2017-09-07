import json
import traceback
from time import time

from django.core.exceptions import MiddlewareNotUsed
from django.db import DEFAULT_DB_ALIAS, connections
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

    def wrap_cursor(self, connection, request):
        if not hasattr(connection, '_drqc_cursor'):
            connection._drqc_cursor = connection.cursor

            def cursor(*args, **kwargs):
                return CursorProxy(
                    connection._drqc_cursor(*args, **kwargs),
                    connection,
                    request,
                    RequestQueryCountConfig.stacktraces_enabled(),
                    self
                )

            connection.cursor = cursor
            return cursor

    def on_query(self, request, query_info):
        container = RequestQueryCountManager.get_testcase_container()
        if container:
            container.add(request, [query_info])

    def unwrap_cursor(self, connection):
        if hasattr(connection, '_drqc_cursor'):
            del connection._drqc_cursor
            del connection.cursor

    def process_request(self, request):
        if RequestQueryCountManager.get_testcase_container():
            # Took from django.test.utils.CaptureQueriesContext
            self.wrap_cursor(self.connection, request)

    def process_response(self, request, response):
        if RequestQueryCountManager.get_testcase_container():
            # Took from django.test.utils.CaptureQueriesContext
            self.unwrap_cursor(self.connection)

        return response


class CursorProxy(object):
    """
    Wraps a cursor and logs queries.
    """

    def __init__(self, cursor, db, request, enable_stacktraces, logger):
        self.cursor = cursor
        # Instance of a BaseDatabaseWrapper subclass
        self.logger = logger
        self.enable_stacktraces = enable_stacktraces
        self.request = request

    def _record(self, method, sql, params):
        start_time = time()
        try:
            return method(sql, params)
        finally:
            stop_time = time()
            duration = (stop_time - start_time) * 1000
            if self.enable_stacktraces:
                stacktrace = traceback.format_stack()
            else:
                stacktrace = []

            try:
                _params = json.dumps([self._decode(p) for p in params])
            except:
                _params = ""

            alias = getattr(self.db, 'alias', 'default')
            conn = self.db.connection
            vendor = getattr(conn, 'vendor', 'unknown')

            params = {
                'vendor': vendor,
                'alias': alias,
                'duration': duration,
                'sql': sql,
                'params': _params,
                'stacktrace': stacktrace,
                'start_time': start_time,
                'stop_time': stop_time,
            }

            # We keep `sql` to maintain backwards compatibility
            self.logger.on_query(self.request, params)

    def callproc(self, procname, params=None):
        return self._record(self.cursor.callproc, procname, params)

    def execute(self, sql, params=None):
        return self._record(self.cursor.execute, sql, params)

    def executemany(self, sql, param_list):
        return self._record(self.cursor.executemany, sql, param_list)

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
