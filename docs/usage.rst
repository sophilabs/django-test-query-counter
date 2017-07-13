=====
Usage
=====

To use Django API Query Count in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'request_query_count.apps.DjangoApiQueryCountConfig',
        ...
    )

Add Django API Query Count's URL patterns:

.. code-block:: python

    from request_query_count import urls as request_query_count_urls


    urlpatterns = [
        ...
        url(r'^', include(request_query_count_urls)),
        ...
    ]
