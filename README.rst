=============================
Django Test Query Counter
=============================

.. image:: https://badge.fury.io/py/django-test-query-counter.svg
    :target: https://badge.fury.io/py/django-test-query-counter

.. image:: https://travis-ci.org/igui/django-test-query-counter
.svg?branch=master
    :target: https://travis-ci.org/igui/django-test-query-counter

.. image:: https://codecov.io/gh/igui/django-test-query-counter/branch/master
/graph/badge.svg
    :target: https://codecov.io/gh/igui/django-test-query-counter

A Django Toolkit for controlling Query count when testing

Documentation
-------------

The full documentation is at https://django-test-query-counter.readthedocs.io.

Quickstart
----------

Install Django Test Query Counter::

    pip install django-request-query-count

Add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'request_query_count',
        ...
    )

Add Django Test Query Counter's URL patterns:

.. code-block:: python

    from test_query_counter import urls as test_query_counter_urls


    urlpatterns = [
        ...
        url(r'^', include(test_query_counter_urls)),
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
