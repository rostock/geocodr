Query API
=========


Geocodr offers an HTTP API to make requests against the index.

The base URL of the API is ``/query``.


Request methods
---------------

The API supports HTTP GET requests were all parameters are passed in the query string. The API also supports HTTP POST requests were the parameters are passed in a JSON body.

The GET and JSON method both use the same parameter names. All parameter names and values are case-sensitive.


Example GET request::

   curl "http://localhost:5000/query?type=search&class=address&query=rostock"


Example request with JSON::

   curl -X POST \
      --data '{"type": "search", "class": "address", "query": "rostock"}' \
      -H 'Content-type: application/json' \
      http://localhost:5000/query



Responses
---------

Geocodr always replies with a valid JSON document.

For errors, a document with status and message is returned. The status is identical to the returned HTTP status.

- 400 for invalid requests: Missing required parameter or invalid value.
- 401 for unauthorized requests: Missing or invalid API-key (see XXX)
- 500 for internal errors: Connection errors to Solr, etc.

Example request with missing parameter::

   % curl http://localhost:5000/query?query=rostock
   {
      "message": "type not in request",
      "status": 400
   }


Successful requests result in a GeoJSON document with a `FeatureCollection` with zero or more `Features`.
Features can contain all possible geometry types. This depends on the configuration of your data classes.
The features are sorted by score (best matches first) or by distance for reverse geocoding queries.

.. note:: All geometries are in the projection of the indexed data. Make requests with ``out_epsg=4326`` to get a GeoJSON as `specified in the standard <https://tools.ietf.org/html/rfc7946#section-4>`_ for interoperability.



General parameters
------------------

The following parameters are valid for all requests.


.. list-table::
   :widths: 10 20 40 30
   :header-rows: 1

   *  - Name
      - Example
      - Description
      - Required/Default
   *  - ``query``
      - `rostock bahnhofsstr`
      - The query string.
      - Yes
   *  - ``type``
      - ``search``
      - Type of request, either ``search`` or ``reverse``.
      - Yes
   *  - ``class``
      - `address,parcel`
      - One or more comma-separated classes to search for. Classes are defined in your Geocodr mapping.
      - Yes
   *  - ``limit``
      - `20`
      - Limit the number of results.
      - No. The configured default limit.
   *  - ``shape``
      - ``centroid``
      - One of ``geometry`` for the original geometry, ``centroid`` for a single point of the geometry or ``bbox`` for the bounding box of the geometry.
      - No. ``geometry``
   *  - ``out_epsg``
      - `3857`
      - The EPSG code for the GeoJSON output.
      - No. The configured projection of the data.

``shape=centroid`` always returns a point that is `on` the polygon or line string geometry.

Examples
~~~~~~~~

Query for "Jenaplan" school::
   
   curl "http://localhost:5000/query?type=search&class=school&query=jenaplan"

Query centroids in EPSG:4326 of all parcels starting with the specified identifier::
   
   curl "http://localhost:5000/query?type=search&class=parcel&shape=centroid\
   &query=132232001&out_epsg=4326"

Reverse geocoding
-----------------

The reverse geocoder returns features that intersect with a requested coordinate, or are within a specified radius of that required coordinate. Features are always sorted by distance from the requested coordinate.


.. list-table::
   :widths: 10 20 40 30
   :header-rows: 1

   *  - Name
      - Example
      - Description
      - Required/Default
   *  - ``type``
      - ``reverse``
      - Required for all reverse geocode requests.
      - Yes
   *  - ``class``
      -
      - See above (general parameters).
      - Yes
   *  - ``query``
      - `8.123,52.456`
      - Requested coordinate for reverse geocoding request. Axis order is always in long/lat or x/y. See also ``in_epsg``.
      - Yes
   *  - ``radius``
      - `20`
      - Return features that are within this radius in meters. ``limit`` still applies.
      - No. The configured default radius.
   *  - ``in_epsg``
      - `4326`
      - The EPSG code of the projection of the query coordinate.
      - Yes

Reverse geocoding requests can be combined with a spatial filter. The ``query`` and ``in_epsg`` parameters are ignored in this case.

Examples
~~~~~~~~

Query all features within 50 meters::
   
   curl "http://localhost:5000/query?type=reverse&class=address\
   &query=307663,6004522.21&in_epsg=25833&radius=50"

Spatial filter
--------------

You can restrict search results with a spatial filter. Only features that intersect the filter geometry are returned. Geocodr supports perimeter and bounding box filter.

Geocodr returns all features within the spatial filter, when the filter is added to a reverse geocoding request (``type=reverse``). The features are sorted by distance from the center of the perimeter of bounding box in this case.


Perimeter filter
~~~~~~~~~~~~~~~~

Restrict search result to a perimeter. 

.. list-table::
   :widths: 10 20 40 30
   :header-rows: 1

   *  - Name
      - Example
      - Description
      - Required/Default
   *  - ``peri_coord``
      - `8.123,52.456`
      - Center coordinate for the perimeter. Axis order is always in long/lat or x/y. See also ``peri_epsg``.
      - Yes
   *  - ``peri_radius``
      - `200`
      - Radius of the perimeter in meters.
      - Yes
   *  - ``peri_epsg``
      - `4326`
      - The EPSG code of the projection of the center coordinate.
      - No. The configured projection of the data.


Examples
^^^^^^^^

Limit results to a perimeter::

   curl "http://localhost:5000/query?type=search&class=address&query=neubukow\
   &peri_coord=280081.485,5992752.284&peri_radius=115.3&peri_epsg=25833"

Query up to ``limit`` features within this perimeter. Sorted by distance from center of the perimeter::

   curl "http://localhost:5000/query?type=reverse&class=address&query=required+but+ignored\
   &peri_coord=280081.485,5992752.284&peri_radius=115.3&peri_epsg=25833"

Bounding box filter
~~~~~~~~~~~~~~~~~~~

Restrict search result to a bounding box. 

.. list-table::
   :widths: 10 20 40 10 20
   :header-rows: 1

   *  - Name
      - Example
      - Description
      - Required
      - Default
   *  - ``bbox``
      - `8.123,52.456,8.234,52.567`
      - Bounding box coordinates as `xmin,ymin,xmax,ymax`. Axis order is always in long/lat or x/y. See also ``bbox_epsg``.
      - Yes
      -
   *  - ``bbox_epsg``
      - `4326`
      - The EPSG code of the projection of the center coordinate.
      - No
      - The configured projection of the data.


Examples
^^^^^^^^

Limit results to a bounding box::

   curl "http://localhost:5000/query?type=search&class=address\
   &query=neubukow&bbox=11.67596,54.03998,11.67763,54.04059&bbox_epsg=4326"

Query up to ``limit`` features within this bounding box. Sorted by distance from center of the bounding box::

   curl "http://localhost:5000/query?type=reverse&class=address\
   &query=required+but+ignored&bbox=11.67596,54.03998,11.67763,54.04059&bbox_epsg=4326\
   &limit=100"