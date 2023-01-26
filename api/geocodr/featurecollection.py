"""
The featurecollection module provides a class for GeoJSON responses.
"""


class FeatureCollection(object):
  def __init__(self):
    self.features = []
    self.total_features = 0
    self.offset = 0

  def add_features(self, features):
    self.features.extend(features)
    self.total_features += len(features)

  def sort(self, limit=0, offset=0, distance=False):
    """
    Sort all features in-place by _score_ and _sort_tiebreaker_ property.
    If distance is provided, features are sorted by _distance_ and
    _collection_rank_. If `limit` is provided, only keep `limit` features
    (after sorting).
    """
    if distance:
      self.features.sort(
        key=lambda x: (x['properties']['_distance_'],
                       x['properties']['_collection_rank_']),
      )
    else:
      self.features.sort(
        key=lambda x: (-x['properties']['_score_'],
                       x['properties']['_sort_tiebreaker_']),
      )

    if limit:
      self.features = self.features[offset:limit + offset]
    elif offset:
      self.features = self.features[offset:]

    self.offset = offset

  def filter_internal_properties(self):
    for feature in self.features:
      prop = feature['properties']
      for k in list(prop.keys()):
        if k and k[0] == '_' and k != '_title_':
          del prop[k]

  def as_mapping(self):
    return {
      'type': 'FeatureCollection',
      'features': self.features,
      'properties': {
        'features_total': self.total_features,
        'features_returned': len(self.features),
        'features_offset': self.offset,
      },
    }
