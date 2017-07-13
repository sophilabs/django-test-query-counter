# -*- coding: utf-8
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Error, register
from django.utils import inspect
from django.utils.module_loading import import_string

from request_query_count.query_count import Middleware


class RequestQueryCountConfig(AppConfig):
    name = 'request_query_count'
    verbose_name = 'Request Query Count'

    def ready(self):
        pass


@register
def check_middleware(_app_configs, **_kwargs):
    errors = []

    setting = getattr(settings, 'MIDDLEWARE', None)
    setting_name = 'MIDDLEWARE'
    if setting is None:
        setting = settings.MIDDLEWARE_CLASSES
        setting_name = 'MIDDLEWARE_CLASSES'

    if not any(is_middleware_class(Middleware, middleware)
               for middleware in enumerate(setting)):
        errors.append(
            Error(
                "debug_toolbar.middleware.DebugToolbarMiddleware is missing "
                "from %s." % setting_name,
                hint="Add debug_toolbar.middleware.DebugToolbarMiddleware to "
                "%s." % setting_name,
            )
        )
    return errors


def is_middleware_class(middleware_class, middleware_path):
    try:
        middleware_cls = import_string(middleware_path)
    except ImportError:
        return
    return (
        inspect.isclass(middleware_cls) and
        issubclass(middleware_cls, middleware_class)
    )
