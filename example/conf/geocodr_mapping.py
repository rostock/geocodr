# -:- encoding: utf-8 -:-
from __future__ import unicode_literals
import re

from geocodr import proj
from geocodr.search import (
    Collection as BaseCollection,
    NGramField,
    SimpleField,
    PrefixField,
    Only,
    PatternReplace,
)


class Collection(BaseCollection):
    # all geometries are in EPSG:4326
    src_proj = proj.epsg(4326)

    class_title_attrib = 'suchklasse'
    collection_title_attrib = 'objektgruppe'
    distance_attrib = 'entfernung'

    geometry_field = 'geometrie'

    # retrieve all fields from Solr, including score and full geometry as WKT
    field_list = '*,score,geometrie:[geo f=geometrie w=WKT]'


def ReplaceStrasse(field):
    """
    Wrap field with pattern replace. We replace straße suffix with str (all
    case-insensitive). This is already implemented in the Solr schema, but it
    does not work with our NGramField, as we build the grams on our own.
    A boost must be applied to the field, not this wrapped result.
    """
    return PatternReplace(
        r'(?i)stra(ß|ss)e\b', 'str.',
        PatternReplace(r'\Bstr.', ' str.', field)
    )

class Street(Collection):
    class_ = 'address'
    class_title = 'Addresses'
    name = 'streets'
    title = 'Streets'
    fields = ('strasse_name', 'gemeinde_name', 'stat_bezirk_name')
    qfields = (
        ReplaceStrasse(NGramField('strasse_name_ngram') ^ 1.0),
        SimpleField('strasse_name') ^ 3.0,
        NGramField('gemeinde_name_ngram') ^ 1.0,
        SimpleField('gemeinde_name') ^ 2.0,
        NGramField('stat_bezirk_name_ngram') ^ 1.0,
        SimpleField('stat_bezirk_name') ^ 3.0,
    )
    sort = 'score DESC, gemeinde_name ASC, stat_bezirk_name ASC, strasse_name ASC'
    collection_rank = 2

    def to_title(self, prop):
        parts = []
        parts.append(prop['gemeinde_name'])
        if prop['stat_bezirk_name']:
            parts.append(prop['stat_bezirk_name'])
        parts.append(prop['strasse_name'])
        return ', '.join(parts)




class Borough(Collection):
    class_ = 'address'
    class_title = 'Addresses'
    name = 'boroughs'
    title = 'Statistische Bezirke'
    fields = ('gemeinde_name', 'bezeichnung')
    qfields = (
        NGramField('bezeichnung_ngram') ^ 1.5,
        SimpleField('bezeichnung') ^ 3.5,
        NGramField('gemeinde_name_ngram') ^ 1.5,
        SimpleField('gemeinde_name') ^ 2.5,
    )
    sort = 'score DESC, gemeinde_name ASC, bezeichnung ASC'
    collection_rank = 1

    def to_title(self, prop):
        parts = []
        parts.append(prop['gemeinde_name'])
        if prop['bezeichnung']:
            parts.append(prop['bezeichnung'])
        return ', '.join(parts)


