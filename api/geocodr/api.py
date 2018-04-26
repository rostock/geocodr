"""
The api module contains the geocodr web service.
"""
from __future__ import print_function

import json
import gzip
import io
from concurrent.futures import ThreadPoolExecutor
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response
from werkzeug.wsgi import SharedDataMiddleware

from geocodr import solr
from geocodr.featurecollection import FeatureCollection
from geocodr.mapping import load_collections
from geocodr.request import (
    DefaultRequestParams,
    GeocodrRequest,
)


import logging
log = logging.getLogger(__name__)


class Geocodr(object):

    def __init__(self, config):
        self.solr = solr.Solr(config['solr_url'])
        self.collections = load_collections(config['mapping'])
        self.data_proj = self.collections[0].src_proj
        self.default_params = DefaultRequestParams(
            data_proj=self.data_proj,
            reverse_radius=50,
        )
        self.url_map = Map([
            Rule('/query', endpoint='query'),
        ])

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, 'on_' + endpoint)(request, **values)
        except ValueError as e:
            return self.json_error(request, 400, e.message)
        except HTTPException as e:
            return e

    def json_error(self, request, code, msg):
        return self.json_resp(request, {'status': code, 'message': msg}, code=code)

    def json_resp(self, request, data, code=200):
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        }
        data = json.dumps(data, sort_keys=True, indent=2)

        if 'jsonp' in request.args:
            data = '{}({});'.format(request.args['jsonp'], data)
            headers['Content-Type'] = 'application/javascript'

        if 'gzip' in request.accept_encodings:
            data = gzip_data(data)
            headers['Content-Encoding'] = 'gzip'
            headers['Vary'] = 'Accept-Encoding'

        return Response(
            data,
            status=code,
            headers=headers,
        )

    def wsgi_app(self, environ, start_response):
        request = GeocodrRequest(environ, self.default_params)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def check_req_classes(self, request, req_classes):
        for cls in req_classes:
            for collection in self.collections:
                if cls == collection.class_:
                    break
            else:
                return self.json_error(request, 400, 'invalid class "{}"'.format(cls))

    def on_query(self, request):

        # collect all variables here so we can use them in concurrently from
        # multiple threads in query()
        dst_proj = request.g.dst_proj
        spatial_filter = request.g.spatial_filter
        distance_pt = spatial_filter.distance_pt() if spatial_filter else None
        shape = request.g.shape
        req_classes = request.g.classes

        err = self.check_req_classes(request, req_classes)
        if err:
            return err

        fc = FeatureCollection()

        def query(collection):
            if request.g.is_reverse:
                q = '*'
            else:
                q = collection.query(request.g.query)

            kw = {}
            if spatial_filter:
                kw.update(
                    spatial_filter.query_params(collection.geometry_field)
                )

            resp = self.solr.query(
                collection=collection.name,
                q=q,
                sort=collection.sort,
                fl=collection.field_list,
                rows=request.g.limit,
                **kw
            )

            return collection.to_features(
                resp['response']['docs'],
                dst_proj=dst_proj,
                distance_pt=distance_pt,
                shape=shape,
            )

        # query in parallel
        with ThreadPoolExecutor() as e:
            futures = []
            for collection in self.collections:
                if collection.class_ not in req_classes:
                    continue
                futures.append(e.submit(query, collection))

            for f in futures:
                try:
                    features = f.result()
                    fc.add_features(features)
                except Exception as ex:
                    log.error(ex)
                    return self.json_error(request, 500, 'internal error')

        fc.sort(limit=request.g.limit, distance=request.g.is_reverse)

        return self.json_resp(request, fc.as_mapping())


def gzip_data(data):
    buf = io.BytesIO()
    f = gzip.GzipFile(filename=None, mode='wb', compresslevel=6, fileobj=buf)
    f.write(data)
    f.close()
    return buf.getvalue()


def create_app(config):
    app = Geocodr(config)

    if config.get('static_files'):
        app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
            '/static':  config['static_files'],
        })
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=5000)
    parser.add_argument("--solr-url", default="http://localhost:8983/solr")
    parser.add_argument("--mapping", required=True, help='mapping file')
    parser.add_argument("--static-dir", help='optional: additional files to host at /static')

    args = parser.parse_args()

    from werkzeug.serving import run_simple
    config = {
        'solr_url': args.solr_url,
        'mapping': args.mapping,
        'static_files': args.static_dir,
    }
    app = create_app(config)
    run_simple(args.host, args.port, app, use_debugger=True, use_reloader=True, threaded=True)
