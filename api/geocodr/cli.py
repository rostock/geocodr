from __future__ import print_function

from concurrent.futures import ThreadPoolExecutor
import json
import sys
import argparse

from geocodr import solr
from geocodr.featurecollection import FeatureCollection
from geocodr.mapping import load_collections


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
        query_kw['explainOther'] = ' '.join('id:'+id for id in args.explain)

    spatial_filter = None
    if args.peri_coord:
        x, y = map(float, args.peri_coord.split(','))
        spatial_filter = solr.SpatialFilter(pt=(x, y), d=args.peri_radius)
    if args.bbox:
        bbox = map(float, args.bbox.split(','))
        spatial_filter = solr.SpatialFilter(bbox=bbox)

    def print_explain(resp, collection):
        for k, v in resp['debug'].get('explainOther', {}).items():
            if k in (args.explain or ()):
                for doc in resp['response']['docs']:
                    if k == doc['id']:
                        # build feature to get final title
                        features = collection.to_features([doc])
                        title = features[0]['properties']['_title_']
                        print(k, title, file=sys.stderr)
                print(v, file=sys.stderr)
                print('-' * 80, file=sys.stderr)

    result = FeatureCollection()

    def query(collection):
        q = collection.query(args.query)

        if spatial_filter:
            fp = spatial_filter.query_params(collection.geometry_field)
            query_kw.update(fp)
            if not q:
                q = '*'

        resp = s.query(
            collection=collection.name,
            q=q,
            # q=args.query,
            sort=collection.sort,
            fl=collection.field_list,
            rows=args.limit,

            **query_kw
        )

        distance_pt = None
        if spatial_filter:
            distance_pt = spatial_filter.distance_pt()

        features = collection.to_features(
            resp['response']['docs'],
            distance_pt=distance_pt,
        )

        # print(resp['debug']['parsedquery'])
        if args.explain:
            print_explain(resp, collection)

        return features

    with ThreadPoolExecutor(max_workers=4) as e:
        futures = []
        for collection in collections:
            if args.classes and collection.class_ not in args.classes:
                continue
            futures.append(e.submit(query, collection))

        for f in futures:
            features = f.result()
            result.add_features(features)

    result.sort(limit=args.limit)

    if args.geojson:
        print(json.dumps(result.as_mapping()))
    else:
        for feature in result.features:
            print(
                feature['properties']['_title_'],
                feature['properties']['_score_'],
                feature['properties']['_id_'],
                feature['properties']['_collection_'],
            )


if __name__ == '__main__':
    main()
