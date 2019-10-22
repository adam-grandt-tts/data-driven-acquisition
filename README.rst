=============================
Data Driven Acquisition
=============================

.. image:: https://badge.fury.io/py/data-driven-acquisition.svg
    :target: https://badge.fury.io/py/data-driven-acquisition

.. image:: https://travis-ci.org/adam-grandt-tts/data-driven-acquisition.svg?branch=master
    :target: https://travis-ci.org/adam-grandt-tts/data-driven-acquisition

.. image:: https://codecov.io/gh/adam-grandt-tts/data-driven-acquisition/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/adam-grandt-tts/data-driven-acquisition

This system is a POC of a document management tool that will initiate acquisition document packages, and allow the acquisition work force to manage them as data. Handling some of the manual work of keeping the document up to date from an intuitive user interface.

Documentation
-------------

The full documentation is at https://data-driven-acquisition.readthedocs.io.

Quickstart
----------

Install Data Driven Acquisition::

    pip install data-driven-acquisition

Add it to your `INSTALLED_APPS`:

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
