geocodr
=======

Introduction
------------

*Geocodr*…

- is a frontend for `Apache Solr <https://solr.apache.org//>`_
- lets you search and sort through multiple collections
- returns valid GeoJSON
- supports different data, input and output projections
- returns BBOX and centroids (point on polygon) for result geometries
- supports reverse geocoding
- implements an optimized query parser and *Apache Solr* schema for fuzzy search in geodata
- provides flexible mapping to add your own custom data (parcel data, POIs, political boundaries, etc)


*Geocodr* is **not** an off-the-shelf solution for all geocoding needs. There are a few assumptions:

*Geocodr* requires that you have an understanding of how *Apache Solr* works (fields, field types, etc.) and how you manage a *SolrCloud* installation.

The optional import helper tools require that you can provide your data as a CSV file with geometries encoded as WKT. However, you can use any *Apache Solr* input source if you manage the *Apache Solr* schema and the import on your own.

*Geocodr* is made for state or country wide datasets. The optional helper tools always makes full re-imports and does not support updates. You need to use other import and update methods for larger datasets.

There is no special support to handle address formats for different languages.

All objects (addresses, streets, etc.) need to be indexed in *Apache Solr* with complete information about the object itself. For example, an address needs street name, city and postcode. *Geocodr* is not able to determine the city of an address by the intersection of a city polygon. This makes it unsuitable for *OpenStreetMap* data, at least without any further pre-processing.

We recommend you to read the :doc:`api` documentation to get an idea about the capabilities. You should follow trough the :doc:`tutorial` to get an idea how to get started with *geocodr.* The :doc:`mapping` section describes how to adapt *geocodr* to search in your data.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   tutorial
   api
   mapping

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
