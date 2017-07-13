# -*- coding: utf-8
import json
import os
import os.path
import threading

from django.apps import AppConfig
from django.conf import settings
from django.test import TransactionTestCase
from django.test.utils import get_runner

from request_query_count.query_count import (TestCaseQueryContainer,
                                             TestResultQueryContainer)

local = threading.local()


class RequestQueryCountConfig(AppConfig):
    LOCAL_TESTCASE_CONTAINER_NAME = 'querycount_test_case_container'
    LOCAL_RESULT_CONTAINER_NAME = 'querycount_result_container'

    name = 'request_query_count'
    verbose_name = 'Request Query Count'

    setting_name = 'REQUEST_QUERY_COUNT'

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
        return getattr(local, cls.LOCAL_TESTCASE_CONTAINER_NAME)

    @classmethod
    def add_middleware(cls):
        setting = getattr(settings, 'MIDDLEWARE', None)
        setting_name = 'MIDDLEWARE'
        if setting is None:
            setting = settings.MIDDLEWARE_CLASSES
            setting_name = 'MIDDLEWARE_CLASSES'

        setattr(
            settings,
            setting_name,
            setting + ('request_query_count.middleware.Middleware',)
        )

    @classmethod
    def wrap_set_up(cls, set_up):
        def wrapped(self, *args, **kwargs):
            result = set_up(self, *args, **kwargs)
            setattr(local, cls.LOCAL_TESTCASE_CONTAINER_NAME,
                    TestCaseQueryContainer())
            return result

        return wrapped

    @classmethod
    def wrap_tear_down(cls, tear_down):
        def wrapped(self, *args, **kwargs):
            if not hasattr(cls, 'test_result_container'):
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
