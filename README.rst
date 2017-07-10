=============================
Django API Query Count
=============================

.. image:: https://badge.fury.io/py/django-api-query-count.svg
    :target: https://badge.fury.io/py/django-api-query-count

.. image:: https://travis-ci.org/igui/django-api-query-count.svg?branch=master
    :target: https://travis-ci.org/igui/django-api-query-count

.. image:: https://codecov.io/gh/igui/django-api-query-count/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/igui/django-api-query-count

A Django Toolkit for controlling Query count when testing

Documentation
-------------

The full documentation is at https://django-api-query-count.readthedocs.io.

Quickstart
----------

Install Django API Query Count::

    pip install django-api-query-count

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'django_api_query_count.apps.DjangoApiQueryCountConfig',
        ...
    )

Add Django API Query Count's URL patterns:

.. code-block:: python

    from django_api_query_count import urls as django_api_query_count_urls


    urlpatterns = [
        ...
        url(r'^', include(django_api_query_count_urls)),
        ...
    ]

Features
--------

* TODO

Running Tests
-------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install tox
    (myenv) $ tox

Credits
-------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
