# -:- encoding: utf-8 -:-
from __future__ import print_function

from functools import wraps
from contextlib import contextmanager

import requests

import logging
log = logging.getLogger(__name__)


class SolrCloudException(Exception):
    def __init__(self, resp):
        try:
            # try to extract solr error message from JSON
            doc = resp.json()
            if 'error' in doc:
                err_msg = doc['error'].get('msg')
            elif 'failure' in doc:
                err_msg = str(doc['failure'])
            elif 'errors' in doc:
                err_msg = ';'.join(';'.join(e.get('errorMessages', [])) for e in doc['errors'])
            else:
                err_msg = resp.content
        except ValueError:
            err_msg = resp.content
        Exception.__init__(self, "error calling {}: {}".format(resp.url, err_msg))
        self.resp = resp


@contextmanager
def ignore_solr_error():
    try:
        yield
    except SolrCloudException as ex:
        log.debug('ignoring error: %s', ex)
        pass


def raise_on_non_200(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        resp = f(*args, **kwds)
        try:
            data = resp.json()
            if 'errors' in data or 'failure' in data:
                raise SolrCloudException(resp)
        except ValueError:
            # not valid json
            pass
        if resp.ok:
            return resp
        raise SolrCloudException(resp)
    return wrapper


class SolrCloud(object):
    def __init__(self, solr_url):
        self.solr_url = solr_url
        self._s = requests.Session()

    @raise_on_non_200
    def create_collection(self, collection, config_name=None, num_shards=2, replication_factor=2):
        params = {
            'action': 'CREATE',
            'name': collection,
            'numShards': num_shards,
            'replicationFactor': replication_factor,
            'maxShardsPerNode': 2,
        }
        if config_name:
            params['collection.configName'] = config_name
        return self._s.get(self.solr_url + '/admin/collections', params=params)

    @raise_on_non_200
    def delete_collection(self, collection):
        return self._s.get(self.solr_url + '/admin/collections', params={
            'action': 'DELETE',
            'name': collection,
        })

    @raise_on_non_200
    def config_collection(self, collection, data):
        return self._s.post("{}/{}/config".format(self.solr_url, collection), json=data)

    @raise_on_non_200
    def config_schema(self, collection, data):
        return self._s.post("{}/{}/schema".format(self.solr_url, collection), json=data)

    def disable_autocreate_fields(self, collection):
        return self.config_collection(collection, {
            "set-user-property": {"update.autoCreateFields": "false"}
        })

    @raise_on_non_200
    def list_aliases(self):
        return self._s.get(self.solr_url + '/admin/collections', params={'action': 'LISTALIASES'})

    @raise_on_non_200
    def list_collections(self):
        return self._s.get(self.solr_url + '/admin/collections', params={'action': 'LIST'})

    @raise_on_non_200
    def alias(self, collection, alias):
        return self._s.get(
            self.solr_url + '/admin/collections',
            params={'action': 'CREATEALIAS', 'name': alias, 'collections': collection},
        )

    @raise_on_non_200
    def update_csv(self, collection, fh):
        return self._s.post(
            '{}/{}/update'.format(self.solr_url, collection),
            headers={'Content-type': 'text/csv'},
            params={'commit': 'true'},
            data=fh
        )
