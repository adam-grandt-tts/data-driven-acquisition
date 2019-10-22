=====
Usage
=====

To use Data Driven Acquisition in a project, add it to your `INSTALLED_APPS`:

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'data_driven_acquisition.apps.DataDrivenAcquisitionConfig',
        ...
    )

Add Data Driven Acquisition's URL patterns:

.. code-block:: python

    from data_driven_acquisition import urls as data_driven_acquisition_urls


    urlpatterns = [
        ...
        url(r'^', include(data_driven_acquisition_urls)),
        ...
    ]
