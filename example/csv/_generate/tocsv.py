import csv
import json
from shapely.geometry import shape
from shapely.prepared import prep
from shapely.wkt import dumps

boroughs = []

with open('statistische_bezirke.json') as fi, open('bezirke.csv', 'w') as fo:
  writer = csv.DictWriter(fo, fieldnames=['id', 'json', 'geometrie', 'gemeinde_name',
                                          'stat_bezirk_name'])
  writer.writeheader()
  for feature in json.load(fi)['features']:
    geom = shape(feature['geometry'])
    blob = json.dumps(feature['properties'])

    prop = {
      'json': blob,
      'id': feature['properties']['uuid'],
      'stat_bezirk_name': feature['properties']['bezeichnung'],
      'gemeinde_name': feature['properties']['gemeinde_name'],
      'geometrie': dumps(geom.simplify(0.00001), rounding_precision=6),
    }
    boroughs.append((prop['stat_bezirk_name'], prep(geom.buffer(0.0001, 2))))

    writer.writerow(prop)

with open('strassen.json') as fi, open('strassen.csv', 'w') as fo:
  writer = csv.DictWriter(fo,
                          fieldnames=['id', 'json', 'geometrie', 'gemeinde_name', 'strasse_name',
                                      'stat_bezirk_name'])
  writer.writeheader()
  for feature in json.load(fi)['features']:
    if not feature['properties']['strasse_name'].startswith('A'):
      continue
    geom = shape(feature['geometry'])
    blob = json.dumps(feature['properties'])

    prop = {
      'json': blob,
      'id': feature['properties']['uuid'],
      'strasse_name': feature['properties']['strasse_name'],
      'gemeinde_name': feature['properties']['gemeinde_name'],
      'geometrie': dumps(geom.simplify(0.00001), rounding_precision=6),
    }

    for borough, borough_geom in boroughs:
      if borough_geom.contains(geom):
        prop['stat_bezirk_name'] = borough

    writer.writerow(prop)
