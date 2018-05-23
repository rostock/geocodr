.. Geocodr documentation master file, created by
   sphinx-quickstart on Wed May 16 09:36:05 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Geocodr's documentation!
===================================


What Geocodr is/isn't
---------------------

What does Geocodr provide:

- A frontend for Solr
- Search and sort through multiple collections
- Return valid GeoJSON
- Support different data, input and output projections
- Return BBOX and centroids (Point on Polygon) for result geometries
- Reverse Geocoding
- Optimized query parser and Solr schema for fuzzy search in geodata
- Flexible mapping to add your own custom data (parcel data, POIs, political boundaries, etc).


Geocodr is `not` an off-the-shelf solution for all geocoding needs. There are a few assumptions:

Geocodr requires that you have an understanding of how Solr works (fields, field types, etc.) and how you manage a SolrCloud installation.

The optional import helper tools require that you can provide your data as a CSV file with geometries encoded as WKT.
However, you can use any Solr input source if you manage the Solr schema and the import on your own.

Geocodr is made for state or country wide datasets. The optional helper tools always makes full re-imports and does not support updates. You need to use other import and update methods for larger datasets.

There is no special support to handle address formats for different languages.

All objects (addresses, streets, etc.) need to be indexed in Solr with complete information about the object itself. For example, an address needs street name, city and postcode. Geocodr is not able to determine the city of an address by the intersection of a city polygon.
This makes it unsuitable for OpenStreetMap data, at least without any further pre-processing.


We recommend you to read the :doc:`api` documentation to get an idea about the capabilities. You should follow trough the :doc:`tutorial` to get an idea how to get started with Geocodr. The :doc:`mapping` section describes how to adapt Geocodr to search in your data.


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   install
   tutorial
   api
   mapping

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
