# -:- encoding: utf-8 -:-

"""
The search module provides classes for custom Collections and Fields.
"""

import re
import json

import shapely.geometry
import shapely.wkt

from geocodr import proj
from geocodr.lib.geom import point_on_geom
from geocodr.solr import strip_special_chars


class Collection(object):
    name = ''
    title = 'Unknown collection'
    class_ = 'unknown_class'
    class_title = 'Unknown class'

    jsonblob_field = 'json'

    """
    fields are always loaded from the result doc and will overwrite properties
    from jsonblob_field.
    """
    fields = ()

    qfields = ()
    geometry_field = 'geometry'
    field_list = '*,score,geometry:[geo f=geometry w=WKT]'
    src_proj = None

    sort = 'score DESC'
    sort_fields = ()

    # collection_rank defines sort order for reverse geocoder results where
    # distance is the same (e.g. multiple polygons for different admin
    # levels).
    collection_rank = 9e99

    class_title_attrib = '_class_title_'
    class_title_attrib = '_class_title_'
    collection_title_attrib = '_collection_title_'
    distance_attrib = '_distance_'

    def sort_tiebreaker(self, doc):
        """
        Sort order for docs with same score.

        Note: Solr sort does not work for tokenized fields.
        We use sort_fields by default as a tie breaker for identical scores.
        """
        if self.sort_fields:
            return tuple(doc[f] for f in self.sort_fields)
        return None

    def to_features(self, docs, dst_proj=proj.epsg(4326),
                    distance_pt=None, shape='geometry'):
        if distance_pt:
            distance_pt = shapely.geometry.Point(*distance_pt)

        features = []

        for doc in docs:
            prop = {}

            if self.jsonblob_field:
                prop = json.loads(doc[self.jsonblob_field])

            geom = shapely.wkt.loads(doc[self.geometry_field])

            if distance_pt:
                dist = 0
                if not geom.contains(distance_pt):
                    dist = geom.distance(distance_pt)
                prop[self.distance_attrib] = dist
                # also add as _distance_ for sorting reverse geocoder results
                prop['_distance_'] = dist
                prop['_collection_rank_'] = self.collection_rank

            if dst_proj and self.src_proj and \
                    dst_proj.srs != self.src_proj.srs:
                geom = proj.transform(self.src_proj, dst_proj, geom)

            for f in self.fields:
                prop[f] = doc.get(f)

            prop['_score_'] = doc['score']
            prop['_sort_tiebreaker_'] = self.sort_tiebreaker(doc)
            prop['_id_'] = doc['id']
            prop['_collection_'] = self.name
            prop['_class_'] = self.class_
            prop['_title_'] = self.to_title(prop)
            prop[self.collection_title_attrib] = self.title
            prop[self.class_title_attrib] = self.class_title

            if shape == 'centroid':
                geom = point_on_geom(geom.centroid)
            elif shape == 'bbox':
                geom = geom.envelope

            feature = {
                'type': 'Feature',
                'geometry': shapely.geometry.mapping(geom),
                'properties': prop,
            }
            features.append(feature)
        return features

    def to_title(self, prop):
        """
        Concatenate fields from search result for human-readable title.
        """
        parts = []
        for f in self.fields:
            if prop.get(f):
                parts.append(prop[f])
        return u', '.join(parts)

    def queries_for_term(self, term):
        """
        Build queries for given `term`. The same term is searched in all
        `qfields` (OR) by default.
        If one or more fields are marked as `exclusive` and if they return a
        query, then we only search in these fields (useful if a Field
        implementation detects that the value should only be searched in one
        field, e.g. a housnumber or zipcode).
        """
        parts = []
        for f in self.qfields:
            part = f.query(term)
            if not part:
                continue
            parts.append(part)

        # Only use exclusive parts (fields wrapped with Only) if at least one
        # part is marked as exclusive.
        if any(is_exclusive(part) for part in parts):
            parts = [p for p in parts if is_exclusive(p)]

        return u' OR '.join(parts)

    def query(self, query):
        query = strip_special_chars(query)
        qparts = []
        for term in query.split(u' '):
            if not term:
                continue
            qparts.append(
                u'_query_:"{{!maxscore tie=0}}({})"'.format(
                    self.queries_for_term(term))
            )
        return u'{}'.format(u' AND '.join(qparts))


class Class(object):
    collections = []


class Field(object):
    boost = 1.0

    def query(self, term):
        raise NotImplementedError()

    def __xor__(self, boost):
        self.boost = boost
        return self


class NGramField(Field):
    def __init__(self, field, min_gram=3, max_gram=3):
        self.field = field
        self.min_gram = min_gram
        self.max_gram = max_gram

    def tokenize(self, input):
        grams = []
        for n in range(self.min_gram, self.max_gram+1):
            grams.extend(u''.join(g)
                         for g in zip(*[input[i:] for i in range(n)]))
        return grams

    def query(self, term):
        grams = self.tokenize(term)
        if not grams:
            return
        # mm 4<-2 -> if more then 4 terms, match at least all but 2 (e.g. 3 of 5)
        return u"{{!edismax qf={0} v='{1}' mm='2<-1 4<-2 6<-3 8<-4'}}^{2:.2}".format(
            self.field,
            u' '.join(grams),
            1.0/len(grams)*self.boost,
        )


class EdgeNGramField(Field):
    def __init__(self, field, min_gram=3, max_gram=8):
        self.field = field
        self.min_gram = min_gram
        self.max_gram = max_gram

    def tokenize(self, input):
        grams = []
        for n in range(self.min_gram, self.max_gram+1):
            grams.append(input[:n])
        return grams

    def query(self, term):
        grams = self.tokenize(term)
        return u"{{!edismax qf={0} v='{1}' mm='100%'}}".format(
            self.field, u' '.join(grams))


class SimpleField(Field):
    def __init__(self, field):
        self.field = field

    def query(self, term):
        q = u'{}:{}'.format(self.field, term)
        if self.boost != 1.0:
            q += '^{:.2}'.format(self.boost)
        return q


class PrefixField(Field):
    def __init__(self, field, min_term=4):
        self.field = field
        self.min_term = min_term

    def query(self, term):
        if len(term) < self.min_term:
            return
        q = u'{}:{}*'.format(self.field, term)
        if self.boost != 1.0:
            q += u'^{:.2}'.format(self.boost)
        return q


class Only(Field):
    def __init__(self, regexp, qfield):
        self.regexp = re.compile(regexp)
        self.qfield = qfield

    def query(self, term):
        if self.regexp.match(term):
            return Exclusive(self.qfield.query(term))


class PatternReplace(Field):
    """
    PatternReplace wraps an existing field and replaces regexp with repl before
    creating the query with qfield.query.
    A boost must be applied to the qfield and not this wrapper.
    """
    def __init__(self, regexp, repl, qfield):
        self.regexp = re.compile(regexp)
        self.repl = repl
        self.qfield = qfield

    def query(self, term):
        term = self.regexp.sub(self.repl, term)
        return self.qfield.query(term)


class Exclusive(str):
    """
    Mark a query as exclusive, i.e. ignore other queries for the same term.
    """
    pass


def is_exclusive(query):
    """
    Check whether a query is exclusive, i.e. if other queries for the same term
    should be ignored.
    """
    return isinstance(query, Exclusive)



class SpatialFilter(object):
    def __init__(self, bbox=None, pt=None, d=10):
        if bbox and pt:
            raise ValueError('spatial query requires bbox _or_ pt and d')

        self.bbox = bbox
        self.pt = pt
        self.d = d

    def distance_pt(self):
        """
        Returns coordinates for distance calculation (pt, or center of bbox).
        """
        if self.pt:
            return self.pt

        return ((self.bbox[0] + self.bbox[2]) / 2.0,
                (self.bbox[1] + self.bbox[3]) / 2.0)

    def query_params(self, sfield):
        if self.pt:
            return {
                'fq': '{{!geofilt sfield={}}}'.format(sfield),
                'pt': '{},{}'.format(self.pt[1], self.pt[0]),
                'd': '{}'.format(self.d),
            }

        return {
            'fq':
            ' {}:["{} {}" TO "{} {}"]'.format(sfield, self.bbox[0],
                                              self.bbox[1], self.bbox[2],
                                              self.bbox[3]),
        }


