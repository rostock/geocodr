import csv

from urllib.parse import urlparse

from .request import RequestError


class APIKeys(object):
  def __init__(self, fname):
    self.fname = fname
    self.keys = self._load()

  def _load(self):
    keys = {}
    with open(self.fname, 'r') as f:
      reader = csv.DictReader(f)
      for row in reader:
        if row['key'].startswith('#'):
          continue
        key = row['key'].strip()
        domains = row['domains'].strip().split(';')
        if domains == ['']:
          domains = None  # wildcard
        keys[key] = domains
    return keys

  def is_permitted(self, request):
    if 'key' not in request.args:
      raise RequestError("Missing 'key' parameter")
    key = request.args['key']

    if key not in self.keys:
      return False

    domains = self.keys[key]
    if not domains:
      # empty domains for "wildcard" permission
      return True

    referrer = request.referrer

    # missing or invalid referrer are accepted, as they might be altered by
    # a (privacy) proxy
    if not referrer:
      return True
    try:
      host = urlparse(referrer).hostname
    except AttributeError:
      return True
    if not host:
      return True

    for d in domains:
      if host == d or host.endswith('.' + d):
        return True

    if host in ('127.0.0.1', 'localhost'):
      return True

    return False
