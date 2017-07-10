# -*- coding: utf-8
from __future__ import unicode_literals, absolute_import

from django.conf.urls import url, include

from django_api_query_count.urls import urlpatterns as django_api_query_count_urls

urlpatterns = [
    url(r'^', include(django_api_query_count_urls, namespace='django_api_query_count')),
]
