import argparse
import json
import sys

from concurrent.futures import ThreadPoolExecutor

from . import solr
from .featurecollection import FeatureCollection
from .mapping import load_collections


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--url",
    default="http://localhost:8983/solr",
  )
  parser.add_argument(
    "--debug",
    action='store_true',
    help="be more verbose and show doc IDs",
  )
  parser.add_argument(
    "--explain",
    action='append',
    help='explain the scoring of the given doc ID',
  )
  parser.add_argument(
    "--geojson",
    action='store_true',
    help='return results as GeoJSON',
  )
  parser.add_argument(
    "--limit",
    type=int,
    default=50,
    help='limit number of results for each collection',
  )
  parser.add_argument(
    "--offset",
    type=int,
    default=0,
    help='start with nth result',
  )
  parser.add_argument(
    "--peri-coord",
    help='coordinate for perimeter filter',
  )
  parser.add_argument(
    "--peri-radius",
    default=10,
    help='radius of perimeter filter',
  )
  parser.add_argument(
    "--bbox",
    help='bbox for spatial filter',
  )
  parser.add_argument(
    "--mapping",
    required=True,
    help='solr collections configuration',
  )
  parser.add_argument(
    "--class",
    dest='classes',
    action='append',
    help='name of the collection classes '
         '(all collections from --mapping are searched if not set)',
  )
  parser.add_argument("query")

  args = parser.parse_args()

  s = solr.Solr(url=args.url)

  collections = load_collections(args.mapping)

  query_kw = {}
  if args.debug or args.explain:
    query_kw['debugQuery'] = 'on'
  if args.explain:
    query_kw['explainOther'] = ' '.join('id:' + curr_id for curr_id in args.explain)

  spatial_filter = None
  if args.peri_coord:
    x, y = map(float, args.peri_coord.split(','))
    spatial_filter = solr.SpatialFilter(pt=(x, y), d=args.peri_radius)
  if args.bbox:
    bbox = map(float, args.bbox.split(','))
    spatial_filter = solr.SpatialFilter(bbox=bbox)

  def print_explain(resp, curr_collection):
    for k, v in resp['debug'].get('explainOther', {}).items():
      if k in (args.explain or ()):
        for doc in resp['response']['docs']:
          if k == doc['id']:
            # build feature to get final title
            curr_features = curr_collection.to_features([doc])
            title = curr_features[0]['properties']['_title_']
            print(k, title, file=sys.stderr)
        print(v, file=sys.stderr)
        print('-' * 80, file=sys.stderr)

  result = FeatureCollection()

  args.query = solr.strip_special_chars(args.query)

  def query(curr_collection):
    q = curr_collection.query(args.query)

    if spatial_filter:
      fp = spatial_filter.query_params(curr_collection.geometry_field)
      query_kw.update(fp)
      if not q:
        q = '*'

    resp = s.query(
      collection=curr_collection.name,
      q=q,
      # q=args.query,
      sort=curr_collection.sort,
      fl=curr_collection.field_list,
      rows=max(args.limit + args.offset, 1000),  # see MIN_COLLECTION_ROWS in api.py

      **query_kw
    )

    distance_pt = None
    if spatial_filter:
      distance_pt = spatial_filter.distance_pt()

    curr_features = curr_collection.to_features(
      resp['response']['docs'],
      distance_pt=distance_pt,
    )

    # print(resp['debug']['parsedquery'])
    if args.explain:
      print_explain(resp, curr_collection)

    return curr_features

  with ThreadPoolExecutor(max_workers=4) as e:
    futures = []
    for collection in collections:
      if args.classes and collection.class_ not in args.classes:
        continue
      futures.append(e.submit(query, collection))

    for f in futures:
      features = f.result()
      result.add_features(features)

  result.sort(limit=args.limit, offset=args.offset)

  if args.geojson:
    print(json.dumps(result.as_mapping(), indent=2, sort_keys=True))
  else:
    print("Found {} results, returning {} (offset {})".format(
      result.total_features, len(result.features), result.offset))
    for feature in result.features:
      if args.debug:
        print(u'{:50s} {:9.6f}  {:18s} {}'.format(
          feature['properties']['_title_'],
          feature['properties']['_score_'],
          feature['properties']['_collection_'],
          feature['properties']['_id_'],
        ))
      else:
        print(
          feature['properties']['_title_'],
        )


if __name__ == '__main__':
  main()
