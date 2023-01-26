from shapely.geometry import LineString


def point_on_geom(geom):
  """
  Return a point on the geometry.

  The point is calculated as follows:
   - centroid if it intersects with the geometry
   - mid point for LineStrings
   - mid point of the longest intersection with an imaginary
     horizontal line in the center of a Polygon
   - the point_on_geom for the longest/largest geometry for
     MultiLineString/MultiPolygon
   - the Point closest to the centroid for MultiPoints
  """
  # check first if centroid is sufficient
  c = geom.centroid
  if geom.contains(c):
    return c

  if geom.type == 'Polygon':
    vcenter = (geom.bounds[1] + geom.bounds[3]) / 2
    hline = LineString([
      (geom.bounds[0] - 1.0, vcenter),
      (geom.bounds[2] + 1.0, vcenter),
    ])
    intersections = geom.intersection(hline)
    return point_on_geom(intersections)

  elif geom.type == 'MultiPolygon':
    max_area = 0
    largest = None
    for polygon in geom.geoms:
      area = polygon.area
      if area > max_area:
        max_area = area
        largest = polygon

    return point_on_geom(largest)

  elif geom.type == 'MultiLineString':
    max_len = 0
    longest = None
    for linestring in geom.geoms:
      length = linestring.length
      if length > max_len:
        max_len = length
        longest = linestring
    return point_on_geom(longest)

  elif geom.type == 'LineString':
    return geom.interpolate(0.5, normalized=True)

  elif geom.type == 'MultiPoint':
    min_dist = 1e99
    closest = None
    for point in geom.geoms:
      dist = point.distance(c)
      if dist < min_dist:
        min_dist = dist
        closest = point
    return closest

  return c
