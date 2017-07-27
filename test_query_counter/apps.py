# -*- coding: utf-8
from django.apps import AppConfig
from django.conf import settings


class RequestQueryCountConfig(AppConfig):
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

    def ready(self):
        if self.enabled():
            from test_query_counter.manager import RequestQueryCountManager
            RequestQueryCountManager.set_up()
