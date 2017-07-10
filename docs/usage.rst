=====
Usage
=====

To use Django API Query Count in a project, add it to your `INSTALLED_APPS`:

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
