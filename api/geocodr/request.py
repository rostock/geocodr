"""
The request module contains classes for parsing geocodr requests (JSON and HTTP GET).
"""

import json

import shapely.geometry

from werkzeug.utils import cached_property
from werkzeug.wrappers import Request

from geocodr import proj
from geocodr.solr import strip_special_chars
from geocodr.search import SpatialFilter


class RequestError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return self.reason


class DefaultRequestParams(object):
    def __init__(self, data_proj=proj.epsg(25833), reverse_radius=50):
        self.data_proj = data_proj
        self.reverse_radius = reverse_radius


class GeocodrParams(object):
    """
    GeocodrParams parses all request parameters for a (reverse) geocoding
    request. The actual parameter values come from either JSONParams or
    GETParams.
    """
    def __init__(self, params, defaults):
        self.params = params
        self.defaults = defaults

    @cached_property
    def query(self):
        return strip_special_chars(self.params.get('query'))

    @cached_property
    def type(self):
        t = self.params.get('type')
        if t not in ('search', 'reverse'):
            raise RequestError("Invalid request type. Supported: search or reverse. Got: '{}'".format(t))
        return t

    @cached_property
    def is_reverse(self):
        return self.type == 'reverse'

    @cached_property
    def reverse_radius(self):
        return int(self.params.get('radius', self.defaults.reverse_radius))

    @cached_property
    def limit(self):
        return max(int(self.params.get('limit', default=100)), 1)

    @cached_property
    def classes(self):
        return self.params.get('class').split(',')

    @cached_property
    def shape(self):
        shape = self.params.get('shape', 'geometry')
        if shape not in ('geometry', 'centroid', 'bbox'):
            raise RequestError("Invalid shape value. Supported: geometry, centroid or bbox. Got: '{}'".format(shape))
        return shape

    @cached_property
    def dst_proj(self):
        if (self.type == 'reverse'
            and not ('bbox' in self.params or 'peri_coord' in self.params)):
            # param required for reverse (but not for bbox/peri)
            epsg = self.params.get('in_epsg')
        else:
            epsg = self.params.get('out_epsg', default=None)

        if epsg:
            return proj.epsg(epsg)

    @cached_property
    def spatial_filter(self):
        if 'peri_coord' in self.params:
            coord, radius = self.peri_params()
            return SpatialFilter(pt=coord, d=radius)
        if 'bbox' in self.params:
            bbox = self.bbox_params()
            return SpatialFilter(bbox=bbox)
        if self.type == 'reverse':
            coord, radius = self.reverse_params()
            return SpatialFilter(pt=coord, d=radius)

    def peri_params(self):
        # peri_radius and peri_epsg are required params
        coord = self.params.get('peri_coord')
        x, y = (float(x) for x in coord.split(','))
        pt = shapely.geometry.Point(x, y)
        radius = float(self.params.get('peri_radius'))
        peri_epsg = self.params.get('peri_epsg')
        peri_proj = proj.epsg(peri_epsg)
        pt = proj.transform(peri_proj, self.defaults.data_proj, pt)
        return (pt.x, pt.y), radius

    def bbox_params(self):
        # bbox_epsg is a required param
        bbox = map(float, self.params.get('bbox').split(','))
        bbox = shapely.geometry.box(*bbox)
        bbox_epsg = self.params.get('bbox_epsg')
        bbox_proj = proj.epsg(bbox_epsg)
        bbox = proj.transform(bbox_proj, self.defaults.data_proj, bbox)
        return bbox.bounds

    def reverse_params(self):
        coord = self.params.get('query')
        x, y = (float(x) for x in coord.split(','))
        pt = shapely.geometry.Point(x, y)
        in_epsg = self.params.get('in_epsg')
        in_proj = proj.epsg(in_epsg)
        pt = proj.transform(in_proj, self.defaults.data_proj, pt)
        return (pt.x, pt.y), self.reverse_radius


RaiseMissing = object()


class JSONParams(object):
    def __init__(self, doc):
        self.doc = doc

    def __contains__(self, key):
        return key in self.doc

    def get(self, key, default=RaiseMissing):
        if default is RaiseMissing:
            if key in self.doc:
                return self.doc[key]
            else:
                raise RequestError("Parameter '{}' is required for this request.".format(key))
        else:
            return self.doc.get(key, default)


class GETParams(object):
    def __init__(self, args):
        self.args = args

    def __contains__(self, key):
        return key in self.args

    def get(self, key, default=RaiseMissing):
        if default is RaiseMissing:
            if key in self.args:
                return self.args[key]
            else:
                raise RequestError("Parameter '{}' is required for this request.".format(key))
        else:
            return self.args.get(key, default)


class GeocodrRequest(Request):
    # accept up to 4MB of transmitted data.
    max_content_length = 1024 * 1024 * 4

    def __init__(self, environ, default_params={}, **kw):
        self.default_params = default_params
        Request.__init__(self, environ, **kw)

    @cached_property
    def json(self):
        if self.headers.get('content-type') == 'application/json':
            return json.loads(self.data.decode('utf-8'))

    @cached_property
    def g(self):
        if self.json:
            return GeocodrParams(JSONParams(self.json),
                                 defaults=self.default_params)
        else:
            return GeocodrParams(GETParams(self.args),
                                 defaults=self.default_params)
