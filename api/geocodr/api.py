"""
The api module contains the geocodr web service.
"""

import gzip
import io
import json
import logging
import os

from concurrent.futures import ThreadPoolExecutor
from werkzeug.middleware.shared_data import SharedDataMiddleware
from werkzeug.routing import Map, Rule
from werkzeug.wrappers import Response

from . import solr
from .featurecollection import FeatureCollection
from .keys import APIKeys
from .mapping import load_collections
from .request import (
  DefaultRequestParams,
  GeocodrRequest,
  RequestError,
)


log = logging.getLogger(__name__)

# Query Solr for at least this many results. Large value is required for proper sorting
# and paging.
MIN_COLLECTION_ROWS = 1000


class Geocodr(object):

  def __init__(self, config):
    self.solr = solr.Solr(config['solr_url'])
    self.collections = load_collections(config['mapping'])
    self.apikeys = None
    if config.get('api_keys_csv'):
      self.apikeys = APIKeys(config['api_keys_csv'])
    self.enable_solr_basic_auth = config.get('enable_solr_basic_auth', False)
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
    except RequestError as e:
      return self.json_error(request, 400, e.reason)
    except ValueError as e:
      return self.json_error(request, 400, 'Invalid parameter value: ' + str(e))
    except Exception:
      log.exception("Dispatching query {}".format(request))
      return self.json_error(request, 500, 'Internal error')

  def json_error(self, request, code, msg):
    return self.json_resp(request, {'status': code, 'message': msg}, code=code)

  @staticmethod
  def json_resp(request, data, code=200):
    headers = {
      'Content-Type': 'application/json; charset=utf-8',
      'Access-Control-Allow-Origin': '*',
    }
    data = json.dumps(data, sort_keys=True, indent=2)

    if 'callback' in request.args:
      data = '{}({});'.format(request.args['callback'], data)
      headers['Content-Type'] = 'application/javascript'

    data = data.encode('utf-8')

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
        return self.json_error(request, 400, "Invalid class '{}'".format(cls))

  def on_query(self, request):
    if self.enable_solr_basic_auth and request.g.user_auth:
      # skip apikey validation if enable_solr_basic_auth is active and the user
      # provided user/password
      pass
    elif self.apikeys and not self.apikeys.is_permitted(request):
      # we have API keys and key is missing or invalid
      return self.json_error(request, 403, 'API key is invalid or not valid for this requests.')

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

    def query(curr_collection):
      if (
          not request.g.is_reverse
          and len(request.g.query.strip()) < curr_collection.min_query_length
      ):
        # return empty result for short queries
        return []

      if request.g.is_reverse:
        q = '*'
      else:
        q = curr_collection.query(request.g.query)

      kw = {}
      if spatial_filter:
        kw.update(
          spatial_filter.query_params(curr_collection.geometry_field)
        )

      resp = self.solr.query(
        collection=curr_collection.name,
        q=q,
        sort=curr_collection.sort,
        fl=curr_collection.field_list,
        rows=max(request.g.limit + request.g.offset, MIN_COLLECTION_ROWS),
        user_auth=request.g.user_auth,
        **kw
      )

      return curr_collection.to_features(
        resp['response']['docs'],
        dst_proj=dst_proj,
        distance_pt=distance_pt,
        shape=shape,
      )

    # query in parallel
    with ThreadPoolExecutor(max_workers=4) as e:
      futures = []
      for collection in self.collections:
        if collection.class_ not in req_classes:
          continue
        futures.append((collection.name, e.submit(query, collection)))

      for name, f in futures:
        try:
          features = f.result()
          fc.add_features(features)
        except solr.SolrUnauthenticatedError:
          return self.json_error(request, 400, 'Invalid user/password')
        except Exception:
          log.exception("Fetching result for collection '%s'", name)
          return self.json_error(request, 500, 'Internal error.')

    fc.sort(limit=request.g.limit, offset=request.g.offset, distance=request.g.is_reverse)

    if request.args.get('debug', '').lower() != 'true':
      fc.filter_internal_properties()

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
      '/static': config['static_files'],
    })
  return app


def main():
  logging.basicConfig(level=logging.INFO)

  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument("--host", default="127.0.0.1")
  parser.add_argument("--port", type=int, default=5000)
  parser.add_argument("--solr-url", default="http://localhost:8983/solr")
  parser.add_argument("--mapping", required=True, help='mapping file')
  parser.add_argument("--static-dir", help='optional: additional files to host at /static')
  parser.add_argument("--api-keys", help='optional: CSV file with permitted API keys and domains')
  parser.add_argument(
    "--enable-solr-basic-auth",
    action='store_true',
    help='optional: pass user/password params to Solr as HTTP Basic-Authentication'
  )
  parser.add_argument("--develop", action='store_true',
                      help='start in development mode (reload on code changes)')

  args = parser.parse_args()

  from werkzeug.serving import run_simple
  config = {
    'solr_url': args.solr_url,
    'mapping': args.mapping,
    'static_files': args.static_dir,
    'api_keys_csv': args.api_keys,
    'enable_solr_basic_auth': args.enable_solr_basic_auth,
  }
  app = create_app(config)
  if args.develop:
    run_simple(args.host, args.port, app,
               extra_files=[os.path.abspath(args.mapping)],
               use_debugger=True, use_reloader=True, threaded=True)
  else:
    import waitress
    waitress.serve(app, host=args.host, port=args.port)


if __name__ == '__main__':
  main()
