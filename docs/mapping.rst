Mapping
=======


Concepts
--------

Geocodr supports multiple `classes` of objects. You can uses classes to separate different types of objects, for example parcel information, addresses or point of interest. End-users can select one or more classes when calling the API.

Each `class` contains one or more `collections`. You can use collections to build different indices for objects with different attributes. For example addresses have house numbers and street names, but neighborhoods have only a name and a city it belongs to. A Geocodr collection is tied to one Solr collection. 


The `tutorial <tutorial>`_ contained a single class (``address``) and two collections (``boroughs`` and ``streets``). If you had a dataset with all house numbers, then you would add that to a new collection (e.g. ``addresses`` or ``housenumbers``) belonging to the same ``address`` class.
A dataset with shops would belong in a different class (e.g. ``pois``).

Each collection is stored in a separate Solr collection. Each collection can have a different set of fields and you can configure which fields should be indexed and how they should be processed before indexing. This is configured in the Solr schema for each collection and is not specific to Geocodr. 

Geocodr queries each collection with your search query. These queries run in parallel. The results are merged back together to a single result set.
The sort order is defined by the scoring which can be adjusted by your collection definition.


Searching
---------

Solr schema
~~~~~~~~~~~

We use a simple analyzer for string fields like street or city names with a standard tokenizer and normalization filters applicable for our language.
You can improve results by harmonizing your data and queries with ``charFilter`` (``PatternReplaceCharFiltersFacotry``) as necessary. For example: The example schemas abbreviate the common suffix `Straße` (street) to `str`.

We use ``NGramFilterFactory`` and ``EdgeNGramFilterFactory`` for fuzzy and prefix matches. See below.

Please refer to the `geocodr-mv repository <https://github.com/rostock/geocodr-mv/tree/master/solr>`_ for a complex example.


Geocodr mapping
~~~~~~~~~~~~~~~

Geocodr loads the definition of your collections from a mapping file. The ``geocodr`` and ``geocodr-api`` tool use the ``--mapping`` option to pass the file name of this mapping file. 

The mapping file is a Python script. Each collection is a subclass of ``geocodr.search.Collection``. 

Most mapping options can be set by class variables on your custom collection classes.
Basic options are ``class_`` and ``name``.

Here is a minimal example::

   from geocodr.search import Collection 

   class Street(Collection):
      class_ = 'address'         # class for grouping similar collections
      class_title = 'Addresses'  # human readable class name
      name = 'streets'           # name of the Solr collection 
      title = 'Streets'          # human readable name of the collection


Please refer to the `geocodr-mv repository <https://github.com/rostock/geocodr-mv/blob/master/conf/geocodr_mapping.py>`_ for a complex mapping file.


Exact matches
~~~~~~~~~~~~~

You need to define ``qfield`` with a list (or tuple) of all fields that should be used for searching. Geocodr splits the query string into terms and each term needs to be found in at least one of the ``qfields``. You can apply different boosts by appending the boost value with ``^``.

For exact matches::

   class Street(Collection):
      qfields = (
         SimpleField('city_name') ^ 2.0,
         SimpleField('street_name') ^ 3.0,
      )


A query for `'rostock amberg'` will query Solr with a query similar to ``(city_name:rostock or street_name:rostock) and (city_name:amberg or street_name:amberg)``. Remember that Solr passes each term trough the tokenizer and filter of each field. Depending on your schema, these `exact` matches are still case insensitive, diacritics (like ä, é, ñ) will be normalized, etc..


Fuzzy matches
~~~~~~~~~~~~~

We use ``NGramField`` for fuzzy search, which accepts incomplete terms and spelling errors::

   class Street(Collection):
      qfields = (
         SimpleField('city_name') ^ 2.0,
         NGramField('city_name_ngram') ^ 1.0,
         SimpleField('street_name') ^ 3.0,
         NGramField('street_name_ngram') ^ 1.0,
      )


``NGramField`` requires a Solr field with ``NGramFilterFactory`` filter.
``NGramField`` builds 3-grams by default. A search term `amberg` generates the `amb`, `mbe`, `ber` and `erg` tokens. Solr would return results as soon as a single 3-gram is matched. Since this is not desired for our geocoding, Geocodr builds a Solr phrase search to get finer control of the results. For `amberg` we search for the phrases `amb mbe ber erg` and require that at least 3 phrases (n-grams) match. A longer search term tolerates more missing n-grams.

The boost for n-gram fields should be lower so that exact matches score higher.

Note that Solr analyzers and filters are not applied. You need to implement any filter in your own subclass.
``GermanNGramField`` is such a subclass for fields with ``NGramFilterFactory`` and ``GermanNormalizationFilterFactory``.


Prefix matches
~~~~~~~~~~~~~~

A ``PrefixField`` can be used to match (partial) post codes::


   class Postcodes(Collection):
      qfields = (
         PrefixField('postcode')),
      )

PrefixField requires a Solr field with EdgeNGramFilterFactory filter.
Terms are matched from left. The term ``123`` will generate a Solr query similar to ``postcode:123*``.

