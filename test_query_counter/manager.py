# -*- coding: utf-8
import inspect
import json
import os
import os.path
import threading

from django.conf import settings
from django.test import SimpleTestCase
from django.test.utils import get_runner
from django.utils.module_loading import import_string
from test_query_counter.apps import RequestQueryCountConfig
from test_query_counter.query_count import (TestCaseQueryContainer,
                                            TestResultQueryContainer)

local = threading.local()


class RequestQueryCountManager(object):
    LOCAL_TESTCASE_CONTAINER_NAME = 'querycount_test_case_container'
    queries = None

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
        middleware_class_name = 'test_query_counter.middleware.Middleware'
        middleware_setting = getattr(settings, 'MIDDLEWARE', None)
        setting_name = 'MIDDLEWARE'
        if middleware_setting is None:
            middleware_setting = settings.MIDDLEWARE_CLASSES
            setting_name = 'MIDDLEWARE_CLASSES'

        # add the middleware only if it was not added before
        if not any(map(cls.is_middleware_class, middleware_setting)):
            if isinstance(middleware_setting, list):
                new_middleware_setting = (
                    middleware_setting +
                    [middleware_class_name]
                )
            elif isinstance(middleware_setting, tuple):
                new_middleware_setting = (
                    middleware_setting +
                    (middleware_class_name,)
                )
            else:
                err_msg = "{} is missing from {}.".format(
                    middleware_class_name,
                    setting_name
                )
                raise TypeError(err_msg)

            setattr(settings, setting_name, new_middleware_setting)

    @classmethod
    def wrap_pre_set_up(cls, set_up):
        def wrapped(self, *args, **kwargs):
            result = set_up(self, *args, **kwargs)
            if RequestQueryCountConfig.enabled():
                setattr(local, cls.LOCAL_TESTCASE_CONTAINER_NAME,
                        TestCaseQueryContainer())
            return result

        return wrapped

    @classmethod
    def wrap_post_tear_down(cls, tear_down):
        def wrapped(self, *args, **kwargs):
            if (not hasattr(cls, 'queries') or not
                    RequestQueryCountConfig.enabled()):
                return tear_down(self, *args, **kwargs)

            container = cls.get_testcase_container()

            test_method = getattr(self, self._testMethodName)

            exclusions = (
                getattr(self.__class__, "__querycount_exclude__", []) +
                getattr(test_method, "__querycount_exclude__", [])
            )

            all_queries = cls.queries
            current_queries = container.filter_by(exclusions)
            all_queries.add(self.id(), current_queries)

            return tear_down(self, *args, **kwargs)

        return wrapped

    @classmethod
    def patch_test_case(cls):
        SimpleTestCase._pre_setup = cls.wrap_pre_set_up(
            SimpleTestCase._pre_setup
        )
        SimpleTestCase._post_teardown = cls.wrap_post_tear_down(
            SimpleTestCase._post_teardown
        )

    @classmethod
    def save_json(cls, setting_name, container, detail):
        summary_path = os.path.realpath(RequestQueryCountConfig.get_setting(
            setting_name))
        os.makedirs(os.path.dirname(summary_path), exist_ok=True)

        with open(summary_path, 'w') as json_file:
            json.dump(container.get_json(detail=detail), json_file,
                      ensure_ascii=False, indent=4, sort_keys=True)

    @classmethod
    def wrap_setup_test_environment(cls, func):
        def wrapped(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not RequestQueryCountConfig.enabled():
                return result
            cls.queries = TestResultQueryContainer()
            return result

        return wrapped

    @classmethod
    def wrap_teardown_test_environment(cls, func):
        def wrapped(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if not RequestQueryCountConfig.enabled():
                return result
            cls.save_json('SUMMARY_PATH', cls.queries, False)
            cls.save_json('DETAIL_PATH', cls.queries, True)
            cls.queries = None
            return result

        return wrapped

    @classmethod
    def patch_runner(cls):
        # FIXME: this is incompatible with --parallel and --test-runner
        # command arguments
        test_runner = get_runner(settings)

        if (not hasattr(test_runner, 'setup_test_environment') or not
                hasattr(test_runner, 'teardown_test_environment')):
            return

        test_runner.setup_test_environment = cls.wrap_setup_test_environment(
            test_runner.setup_test_environment
        )
        test_runner.teardown_test_environment = \
            cls.wrap_teardown_test_environment(
                test_runner.teardown_test_environment
            )

    @classmethod
    def set_up(cls):
        cls.add_middleware()
        cls.patch_test_case()
        cls.patch_runner()
