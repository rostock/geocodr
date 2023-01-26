"""
The mapping module contains function to load custom geocodr mappings.
"""

import inspect

from .search import Collection


def load_collections(fname):
  """
  Open a geocodr mapping file and return all geocodr.search.Collection
  subclasses.
  """
  collections = []
  with open(fname, 'r') as f:
    code = compile(f.read(), fname, 'exec')
    ns = {}
    exec(code, ns)

  src_proj = None
  for v in ns.values():
    if (
        inspect.isclass(v)
        and issubclass(v, Collection)
        and v != Collection
        and v.name
    ):
      coll = v()
      if src_proj:
        assert coll.src_proj == src_proj, \
          'all Collections need the same src_proj'
      else:
        src_proj = coll.src_proj
      collections.append(coll)

  return collections
