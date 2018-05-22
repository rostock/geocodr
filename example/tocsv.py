import shapely.geometry
import shapely.wkt
import json
import csv


with open('strassen.json') as fi, open('strassen.csv', 'w') as fo:
    writer = csv.DictWriter(fo, fieldnames=['id', 'json', 'geometrie', 'gemeinde_name', 'strasse_name'])
    writer.writeheader()
    for feature in json.load(fi)['features']:
        geom = shapely.geometry.asShape(feature['geometry'])
        blob = json.dumps(feature['properties'])
        prop = {
            'json': blob,
            'id': feature['properties']['uuid'],
            'strasse_name': feature['properties']['strasse_name'],
            'gemeinde_name': feature['properties']['gemeinde_name'],
            'geometrie': shapely.wkt.dumps(geom.simplify(0.00001), rounding_precision=6),
        }
        if prop['strasse_name'].startswith('A'):
            writer.writerow(prop)


with open('statistische_bezirke.json') as fi, open('bezirke.csv', 'w') as fo:
    writer = csv.DictWriter(fo, fieldnames=['id', 'json', 'geometrie', 'gemeinde_name', 'bezeichnung'])
    writer.writeheader()
    for feature in json.load(fi)['features']:
        geom = shapely.geometry.asShape(feature['geometry'])
        blob = json.dumps(feature['properties'])
        prop = {
            'json': blob,
            'id': feature['properties']['uuid'],
            'bezeichnung': feature['properties']['bezeichnung'],
            'gemeinde_name': feature['properties']['gemeinde_name'],
            'geometrie': shapely.wkt.dumps(geom.simplify(0.00001), rounding_precision=6),
        }
        writer.writerow(prop)


