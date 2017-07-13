# -*- coding: utf-8
from __future__ import absolute_import, unicode_literals

import django

DEBUG = True
USE_TZ = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '66666666666666666666666666666666666666666666666666'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ROOT_URLCONF = 'tests.urls'

INSTALLED_APPS = [
    'django_jenkins',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sites',
    'django',
    'request_query_count',
]

SITE_ID = 1

if django.VERSION >= (1, 10):
    MIDDLEWARE = (
        'request_query_count.middleware.Middleware',
    )
else:
    MIDDLEWARE_CLASSES = (
        'request_query_count.middleware.Middleware',
    )
