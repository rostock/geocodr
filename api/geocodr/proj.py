"""
The proj module contains functions to transform geometries between projections.
"""

import pyproj
import shapely.ops

from functools import partial


def epsg(code):
  """
  Return Proj object for given EPSG `code`.
  """
  try:
    return pyproj.CRS('{}'.format(code))
  except RuntimeError:
    raise ValueError('unknown {}'.format(code))


def transform(src, dst, geom):
  """
  Transform `geom` from `src` projection into `dst` projection.
  Returns a new geometry.
  """
  project = partial(
    pyproj.transform,
    src,
    dst,
  )
  return shapely.ops.transform(project, geom)
