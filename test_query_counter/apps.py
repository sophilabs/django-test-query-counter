# -*- coding: utf-8
import inspect
import json
import os
import os.path
import threading

from django.apps import AppConfig
from django.conf import settings
from django.test import TransactionTestCase
from django.test.utils import get_runner
from django.utils.module_loading import import_string

from test_query_counter.query_count import (TestCaseQueryContainer,
                                            TestResultQueryContainer)

local = threading.local()


class RequestQueryCountConfig(AppConfig):

    LOCAL_TESTCASE_CONTAINER_NAME = 'querycount_test_case_container'

    name = 'test_query_counter'
    verbose_name = 'Request Query Count'

    setting_name = 'TEST_QUERY_COUNTER'

    default_settings = {
        'ENABLE': True,
        'ENABLE_STACKTRACES': True,
        'DETAIL_PATH': 'reports/query_count_detail.json',
        'SUMMARY_PATH': 'reports/query_count.json'
    }

    @classmethod
    def get_setting(cls, setting_name):
        return (getattr(settings, cls.setting_name, {})
                .get(setting_name, cls.default_settings[setting_name]))

    @classmethod
    def stacktraces_enabled(cls):
        return cls.get_setting('ENABLE_STACKTRACES')

    @classmethod
    def enabled(cls):
        return cls.get_setting('ENABLE')

    @classmethod
    def get_testcase_container(cls):
        return getattr(local, cls.LOCAL_TESTCASE_CONTAINER_NAME, None)

    @classmethod
    def is_middleware_class(cls, middleware_path):
        from test_query_counter.middleware import Middleware

        try:
            middleware_cls = import_string(middleware_path)
        except ImportError:
            return
        return (
            inspect.isclass(middleware_cls) and
            issubclass(middleware_cls, Middleware)
        )

    @classmethod
    def add_middleware(cls):
        middleware_setting = getattr(settings, 'MIDDLEWARE', None)
        setting_name = 'MIDDLEWARE'
        if middleware_setting is None:
            middleware_setting = settings.MIDDLEWARE_CLASSES
            setting_name = 'MIDDLEWARE_CLASSES'

        # add the middleware only if it was not added before
        if not any(map(cls.is_middleware_class, middleware_setting)):
            setattr(
                settings,
                setting_name,
                (
                    middleware_setting + (
                        'test_query_counter.middleware.Middleware',
                    )
                )
            )

    @classmethod
    def wrap_set_up(cls, set_up):
        def wrapped(self, *args, **kwargs):
            result = set_up(self, *args, **kwargs)
            if cls.enabled():
                setattr(local, cls.LOCAL_TESTCASE_CONTAINER_NAME,
                        TestCaseQueryContainer())
            return result

        return wrapped

    @classmethod
    def wrap_tear_down(cls, tear_down):
        def wrapped(self, *args, **kwargs):
            if not hasattr(cls, 'test_result_container') or not cls.enabled():
                return tear_down(self, *args, *kwargs)

            container = cls.get_testcase_container()

            test_method = getattr(self, self._testMethodName)

            exclusions = (
                getattr(self.__class__, "__querycount_exclude__", []) +
                getattr(test_method, "__querycount_exclude__", [])
            )

            all_queries = cls.test_result_container
            current_queries = container.filter_by(exclusions)
            all_queries.add(self.id(), current_queries)

            return tear_down(self, *args, *kwargs)

        return wrapped

    @classmethod
    def patch_test_case(cls):
        TransactionTestCase.setUp = cls.wrap_set_up(TransactionTestCase.setUp)
        TransactionTestCase.tearDown = cls.wrap_tear_down(
            TransactionTestCase.tearDown)

    @classmethod
    def save_json(cls, setting_name, container, detail):
        summary_path = os.path.realpath(cls.get_setting(setting_name))
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)

        with open(summary_path, 'w') as json_file:
            json.dump(container.get_json(detail=detail), json_file,
                      ensure_ascii=False, indent=4, sort_keys=True)

    @classmethod
    def wrap_testrunner_run(cls, func):
        def wrapped(self, *args, **kwargs):
            if not cls.enabled():
                return

            cls.test_result_container = TestResultQueryContainer()

            result = func(self, *args, **kwargs)

            cls.save_json('SUMMARY_PATH', cls.test_result_container, False)
            cls.save_json('DETAIL_PATH', cls.test_result_container, True)

            result.queries = cls.test_result_container
            del cls.test_result_container

            return result

        return wrapped

    @classmethod
    def patch_runner(cls):
        # FIXME: this is incompatible with --parallel and --test-runner
        # command arguments
        django_test_runner = get_runner(settings)
        test_runner = django_test_runner.test_runner
        test_runner.run = cls.wrap_testrunner_run(test_runner.run)

    def ready(self):
        if self.enabled():
            self.add_middleware()
            self.patch_test_case()
            self.patch_runner()
