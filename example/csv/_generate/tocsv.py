import shapely.geometry
import shapely.wkt
import shapely.prepared
import json
import csv


boroughs = []

with open('statistische_bezirke.json') as fi, open('bezirke.csv', 'w') as fo:
    writer = csv.DictWriter(fo, fieldnames=['id', 'json', 'geometrie', 'gemeinde_name', 'stat_bezirk_name'])
    writer.writeheader()
    for feature in json.load(fi)['features']:
        geom = shapely.geometry.asShape(feature['geometry'])
        blob = json.dumps(feature['properties'])

        prop = {
            'json': blob,
            'id': feature['properties']['uuid'],
            'stat_bezirk_name': feature['properties']['bezeichnung'],
            'gemeinde_name': feature['properties']['gemeinde_name'],
            'geometrie': shapely.wkt.dumps(geom.simplify(0.00001), rounding_precision=6),
        }
        boroughs.append((prop['stat_bezirk_name'], shapely.prepared.prep(geom.buffer(0.0001, 2))))

        writer.writerow(prop)

with open('strassen.json') as fi, open('strassen.csv', 'w') as fo:
    writer = csv.DictWriter(fo, fieldnames=['id', 'json', 'geometrie', 'gemeinde_name', 'strasse_name', 'stat_bezirk_name'])
    writer.writeheader()
    for feature in json.load(fi)['features']:
        if not feature['properties']['strasse_name'].startswith('A'):
            continue
        geom = shapely.geometry.asShape(feature['geometry'])
        blob = json.dumps(feature['properties'])


        prop = {
            'json': blob,
            'id': feature['properties']['uuid'],
            'strasse_name': feature['properties']['strasse_name'],
            'gemeinde_name': feature['properties']['gemeinde_name'],
            'geometrie': shapely.wkt.dumps(geom.simplify(0.00001), rounding_precision=6),
        }

        for borough, borough_geom in boroughs:
            if borough_geom.contains(geom):
                prop['stat_bezirk_name'] = borough


        writer.writerow(prop)

