"""
The proj module contains functions to transform geometries between projections.
"""

import pyproj
import shapely.ops


def epsg(code):
  """
  Return Proj object for given EPSG `code`.
  """
  try:
    return pyproj.CRS.from_epsg(code)
  except RuntimeError:
    raise ValueError('unknown EPSG:{}'.format(code))


def transform(src, dst, geom):
  """
  Transform `geom` from `src` projection into `dst` projection.
  Returns a new geometry.
  """
  project = pyproj.Transformer.from_crs(
    src,
    dst,
    always_xy=True
  ).transform
  return shapely.ops.transform(project, geom)
