Installation
============


Geocodr is a Python application and requires Python 2.7, 3.4 or higher.


Use the following commands to install all dependencies and Geocodr::

   git clone https://github.com/rostock/geocodr.git
   cd geocodr
   # install dependencies
   pip install -r api/requirements.txt
   pip install -r import/requirements.txt
   # dependencies for running tests with pytest
   pip install -r api/requirements-test.txt

   # install Geocodr and import tools
   pip install -e api
   pip install -e import

This method `links` the source directory of Geocodr and any changes to the source code are immediately available to the Geocodr tools and API.

.. note:: It is recommended to `use Virtualenv for installation <https://virtualenv.pypa.io/en/stable/>`_.


Commands
--------

Geocodr comes with the command line query tool ``geocodr`` and the web API ``geocodr-api``. The optional import helper provides the ``geocodr-zk`` and ``geocodr-post`` tools. Each command provides a ``--help`` option. Call ``geocodr --help`` to see if the installation was successful. 


Packaging
---------

You can build packages for installation on a server with the following command::

   (cd api && python setup.py bdist_wheel)
   (cd import && python setup.py bdist_wheel)


The built packages are placed in ``{api,import}/dist`` and can be installed with ``pip install geocodr*.whl``.


Solr
----

Geocodr assumes that you already have an existing SolrCloud and ZooKeeper installation. 


Tests
-----

Geocodr comes with a small test suite. You can run the tests with ``pytest api``.
The `geocodr-mv repository <https://github.com/rostock/geocodr-mv>`_ contains an extensive suite of acceptance tests. These tests depend on non-public datasets, but they are a good start to write your own acceptance tests for your own data and your own configuration. 

Next
----

See our :doc:`tutorial` on how to get started with Geocodr.

