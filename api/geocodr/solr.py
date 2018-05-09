"""
solr module provides an API for communication with Solr
"""
import re

import requests


class SolrException(Exception):
    def __init__(self, resp):
        try:
            # try to extrace solr error message from JSON
            doc = resp.json()
            if 'error' in doc:
                err_msg = doc['error'].get('msg')
            elif 'errors' in doc:
                err_msg = ';'.join(';'.join(e.get('errorMessages', []))
                                   for e in doc['errors'])
            else:
                err_msg = resp.content
        except ValueError:
            err_msg = resp.content
        Exception.__init__(self, u"error calling {}: {}".format(
            resp.url, err_msg))
        self.resp = resp


class Solr(object):
    """
    Solr provides a connection pool for queries to a Solr server.
    """
    def __init__(self, url):
        self.url = url
        self._s = requests.Session()
        a = requests.adapters.HTTPAdapter(max_retries=3, pool_maxsize=100)
        self._s.mount('http://', a)
        self._s.mount('https://', a)

    def query(self, collection, q, **kw):
        """
        Send query `q` for `collection` to Solr. Returns the JSON response as a dict.
        Additional `kw` parameters are sent as further GET parameters.
        Raises `SolrException` on error.
        """
        kw['q'] = q
        resp = self._s.get(
            '{}/{}/select'.format(self.url, collection), params=kw)
        if not resp.ok:
            raise SolrException(resp)
        return resp.json()

re_special_chars = re.compile(ur'[-+&|!(){}[\]^"~*?:\\/\']')
re_whitespace = re.compile('\s+')

def strip_special_chars(query):
    """
    Replaces any Solr special character with a single whitespace.

    >>> strip_special_chars(' o-+|n!)l([]\\\\"y:?/\\'  ')
    'o n l y'
    """
    query = re_special_chars.sub(' ', query)
    query = re_whitespace.sub(' ', query)
    return query.strip()
