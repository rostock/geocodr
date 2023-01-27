Tutorial
========


This document describes how to get started with Geocodr.


This tutorial assumes that you have a working Geocodr and Solr Cloud installation.

For Geocodr, make sure that the ``geocodr`` command works, otherwise read :doc:`install`.
For Solr, we assume that you followed the `Getting Started With SolrCloud <https://lucene.apache.org/solr/guide/7_3/getting-started-with-solrcloud.html>`_ tutorial and that Solr is running on `localhost:8983` and the internal Zookeeper runs on `localhost:2181`. Adopt the host names and ports if your installation differs.


.. note:: We will create all required Solr collections in this tutorial (i.e. it is sufficient to run ``bin/solr -e cloud -noprompt``).

.. note:: The SolrCloud installation from `Getting Started with SolrCloud` is not meant for production. Please refer to the Solr documentation for production setups.

Example data
------------

The ``example`` directory contains a minimal set of Solr schema documents, Geocodr mappings and example data.
The example dataset uses Open Data (CC0) from the city Rostock in German. Please note that field names are in German.

We will create two collections:

- `boroughs` with polygon geometries of statistical boroughs with the city name (gemeinde_name) and borough name (stat_bezirk_name).
- `streets` with line geometries of streets with street name (strasse_name), city name (gemeinde_name) and borough name (stat_bezirk_name).

Both collections will also contain a geometry as WKT and a JSON dump of all available fields for retrieval (but not for search).

Both collections will belong to the same `address` class.

We will use the schema files ``example/solr/boroughs-schema.xml`` and ``example/solr/streets-schema.xml``. These are standard Solr XML schemas.

For Geocodr, it does not matter how the schema is managed and how the data is imported into Solr. However, you can use the ``geocodr-zk`` and ``geocodr-post`` tools for a simplified workflow. This workflow requires that your input data is available as CSV and that it is sufficient to make complete re-imports, instead of live updates.


Create config sets
------------------

We use ``geocodr-zk`` to upload our configurations for both collections. The following command creates the `boroughs` and `streets` config sets [#cs]_ in Zookeeper and uploads the ``solrconfig.xml`` and the correspondent schema file.

.. [#cs] Config sets are `described in the Solr documentation <https://lucene.apache.org/solr/guide/7_3/config-sets.html>`_. However, the config sets are managed with Zookeeper for SolrCloud and not as files in ``$SOLR_HOME/configsets``.

::

   geocodr-zk --zk-hosts localhost:2181 --config-dir example/solr/ --push ALL


.. warning:: You can update existing config sets with the same command. Be aware that Solr will remove your index if you make changes to you schema as soon as you restart Solr or reload the Solr collection. You should re-import the data immediately with ``geocodr-post`` to be safe.

Import data
-----------

We use ``geocodr-post`` to upload the example data into the appropriate collection.

::

   geocodr-post --url http://localhost:8983/solr --csv example/csv/boroughs.csv --collection boroughs
   geocodr-post --url http://localhost:8983/solr --csv example/csv/streets.csv --collection streets


Please note that the first call imports the boroughs into the `boroughs-1` collection. If the data is successfully imported, then it will create an alias `boroughs` pointing to `boroughs-1`. A second call will import the boroughs into the `boroughs-2` collection and it will update the alias atomically to point to the new collection. Further calls will alternate between the `-1` and `-2` suffix. This allows you to re-import the data in production without any downtime.


First queries
-------------

Geocodr comes with a command line tool for testing and debugging.


Query for the borough `Stadtmitte`::

   % geocodr --mapping example/conf/geocodr_mapping.py 'stadtmitte'
   Rostock, Hanse- und Universitätsstadt, Stadtmitte I
   Rostock, Hanse- und Universitätsstadt, Stadtmitte II
   Rostock, Hanse- und Universitätsstadt, Stadtmitte III
   Rostock, Hanse- und Universitätsstadt, Stadtmitte IV
   Rostock, Hanse- und Universitätsstadt, Stadtmitte V
   Rostock, Hanse- und Universitätsstadt, Stadtmitte I, Aalstecherstr.
   Rostock, Hanse- und Universitätsstadt, Stadtmitte I, Am Kanonsberg
   Rostock, Hanse- und Universitätsstadt, Stadtmitte I, An der Oberkante
   ...


.. note:: In our example dataset larger statistical boroughs are splitted and enumerated with roman numbers. The dataset contains only street starting with 'A'.


To output the result as GeoJSON call::

   % geocodr --mapping example/conf/geocodr_mapping.py 'stadtmitte' --geojson
   {
   "features": [
      {
         "geometry": {
         "coordinates": [
            [
               [
               12.142946,
               54.092925
               ],
   ...



Fuzzy search::

   % geocodr --mapping example/conf/geocodr_mapping.py 'schulzestrasse'
   Rostock, Hanse- und Universitätsstadt, Reutershagen IV, Alfred-Schulze-Str.
   Rostock, Hanse- und Universitätsstadt, Brinckmansdorf III, Albert-Schulz-Str.

Multiple terms::

   % geocodr --mapping example/conf/geocodr_mapping.py 'schulzestrasse reuter'
   Rostock, Hanse- und Universitätsstadt, Reutershagen IV, Alfred-Schulze-Str.


Debugging
~~~~~~~~~

The ``--debug`` option shows the score and the ID of each match. You can pass an ID to the ``--explain`` option to see how the score was calculated by Solr.::

   % geocodr --mapping example/conf/geocodr_mapping.py 'schulze hinri' --debug --explain 3034daaa-3ef5-11e5-9ffb-0050569b7e95
   3034daaa-3ef5-11e5-9ffb-0050569b7e95 Rostock, Hanse- und Universitätsstadt, Hinrichshagen, An der alten Baumschule

   7.0742044 = sum of:
   2.3968432 = max of:
      2.3968432 = sum of:
         0.5397643 = weight(strasse_name_ngram:sch in 45) [SchemaSimilarity], result of:
         0.5397643 = score(doc=45,freq=1.0 = termFreq=1.0
   ), product of:
            0.2 = boost
            1.9924302 = idf, computed as log(1 + (docCount - docFreq + 0.5) / (docFreq + 0.5)) from:
               10.0 = docFreq
               76.0 = docCount
            1.3545375 = tfNorm, computed as (freq * (k1 + 1)) / (freq + k1 * (1 - b + b * fieldLength / avgFieldLength)) from:
               1.0 = termFreq=1.0
               1.2 = parameter k1
               0.75 = parameter b
               8.328947 = avgFieldLength
               3.0 = fieldLength
         0.92853945 = weight(strasse_name_ngram:chu in 45) [SchemaSimilarity], result of:
         0.92853945 = score(doc=45,freq=1.0 = termFreq=1.0
   ), product of:
   ...

HTTP API
--------

``geocodr-api`` starts a web server. Refer to :doc:`api` for full documentation of the API.

You can start the server with::

   geocodr-api --mapping example/conf/geocodr_mapping.py


You can use your browser or a tool like ``curl`` to make queries to the API::

   curl "http://127.0.0.1:5000/query?type=search&class=address&query=schulzestr"


``geocodr-api`` uses `Waitress, a production-quality pure-Python web server <https://docs.pylonsproject.org/projects/waitress/en/latest/>`_. However, it is still recommended to put it behind an HTTP Proxy (like Nginx or Apache mod_proxy) for features like HTTPS.

For development of Geocodr and configuring your Geocodr mapping, you can use the ``geocodr-api --develop`` option. This will automatically reload Geocodr when the application or your mapping file was changed.

.. _tutorial_api_key:

API keys
~~~~~~~~

Geocodr allows to restrict API requests to calls with a valid API key. :ref:`See API documentation.<api_key>`

Checking for API keys can be enabled with the ``--api-keys`` option. The option takes a CSV file with all valid API keys.

The CSV file requires the fields ``key`` and ``domains``. ``domains`` is semicolon separated list of one or more domains. Only requests originating from these domains are permitted. This is done by checking the HTTP ``referer`` header. Sub domains of the configured domains are permitted.


Example CSV file::

   key,domains
   key1,example.org
   multikey,example.org;example.com

.. note:: The ``referer`` header can be forged, so this only limits where the API can be used in public, but it does not prevent automated scripts, etc..


.. _tutorial_user_password:

User/Password Authentication
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Geocodr can pass client provided usernames and passwords to Solr if you enable this with the ``--enable-solr-basic-auth`` option.

Please refer to the `Solr documentation on how to enable Basic Authentication. <https://lucene.apache.org/solr/guide/7_3/basic-authentication-plugin.html>`_
Basic Authentication can be used on combination with the `Rule-Based Authorization Plugin <https://lucene.apache.org/solr/guide/7_3/rule-based-authorization-plugin.html>`_ for fine grained access control to specific collections.


For convenience, you can use the ``geocodr-zk`` to pull and push the ``security.json`` file.

To pull the ``security.json`` file to ``example/solr/``::

   geocodr-zk --zk-hosts localhost:2181 --config-dir example/solr/ --pull --security

To push the ``security.json`` file from ``example/solr/``::

   geocodr-zk --zk-hosts localhost:2181 --config-dir example/solr/ --push --security


Adding users can be accomplished by editing and `pushing` the ``security.json`` file, or by using the Solr REST-API::

   curl http://localhost:8983/solr/admin/authentication -H 'Content-type:application/json' \
      -d '{"set-user": {"tom" : "TomIsCool",
                        "harry":"HarrysSecret"}}'


Unauthenticated Requests
^^^^^^^^^^^^^^^^^^^^^^^^

To permit requests without user/password (e.g. in combination with API key), you can either use the ``"blockUnknown": false`` option of the ``solr.BasicAuthPlugin``.
Or, you can set a default username and password in the ``--solr-url`` (e.g. ``--solr-url http://user:passwd@localhost:8983/solr``). Username and passwords provided via the API will override these default values.

