=====
Usage
=====

To use Django API Query Count in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'test_query_counter.apps.DjangoApiQueryCountConfig',
        ...
    )

Add Django API Query Count's URL patterns:

.. code-block:: python

    from test_query_counter import urls as test_query_counter_urls


    urlpatterns = [
        ...
        url(r'^', include(test_query_counter_urls)),
        ...
    ]
