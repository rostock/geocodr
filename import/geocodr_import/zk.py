# -:- encoding: utf-8 -:-
from __future__ import print_function

from glob import glob
from os import path
from functools import wraps
from contextlib import contextmanager

from kazoo.client import KazooClient
import requests

import logging
log = logging.getLogger(__name__)

def main():
    import argparse
    import logging
    import runpy
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('urllib3').setLevel(logging.WARN)
    logging.getLogger('requests').setLevel(logging.WARN)
    logging.getLogger('kazoo').setLevel(logging.WARN)

    parser = argparse.ArgumentParser()
    parser.add_argument("--zk-hosts", default="localhost:2128")
    parser.add_argument("--list-configs", action='store_true', help='list remote and local configs and exit')
    parser.add_argument("--pull", action='store_true', help='pull configs and exit')
    parser.add_argument("--push", action='store_true', help='push configs and exit')
    parser.add_argument("--delete", action='store_true', help='delete configs and exit')
    parser.add_argument("--mapping", required=False, help='mapping file')
    parser.add_argument("--config-dir", required=True, help='directory for configs')
    parser.add_argument('configs', metavar='CONFIG', nargs='*',
                    help='config names')
    parser.add_argument("--security", action='store_true',
                        help='--pull or --push this file to/from security.json and exit')


    args = parser.parse_args()

    # mapping = runpy.run_path(args.mapping)

    client = KazooClient(hosts=args.zk_hosts)
    client.start()

    if args.configs == ['ALL']:
        args.configs = []
        for config in glob(path.join(args.config_dir, '*-schema.xml')):
            args.configs.append(path.basename(config)[:-len('-schema.xml')])

    if args.security:
        if args.pull:
            content, md = client.get('/security.json')
            with open(path.join(args.config_dir, 'security.json'), 'wb') as f:
                f.write(content)
        elif args.push:
            with open(path.join(args.config_dir, 'security.json'), 'rb') as f:
                content = f.read()
            client.set('/security.json', content)
        else:
            log.error("--security option requires --pull or --push")
            return

    if args.list_configs:
        for config in client.get_children('/configs'):
            print('remote\t' + config)
        for config in glob(path.join(args.config_dir, '*-schema.xml')):
            config = path.basename(config)[:-len('-schema.xml')]
            print('local\t' + config)
    elif args.pull:
        for config in args.configs:
            content, md = client.get('/configs/{}/managed-schema'.format(config))
            with open(path.join(args.config_dir, config + '-schema.xml'), 'wb') as f:
                f.write(content)
            content, md = client.get('/configs/{}/solrconfig.xml'.format(config))
            with open(path.join(args.config_dir, 'solrconfig.xml'), 'wb') as f:
                f.write(content)
    elif args.push:
        for config in args.configs:
            with open(path.join(args.config_dir, config + '-schema.xml'), 'rb') as f:
                content = f.read()
            p = '/configs/{}/managed-schema'.format(config)
            client.ensure_path(p)
            client.set(p, content)

            with open(path.join(args.config_dir, 'solrconfig.xml'), 'rb') as f:
                content = f.read()
            p = '/configs/{}/solrconfig.xml'.format(config)
            client.ensure_path(p)
            client.set(p, content)
    elif args.delete:
        for config in args.configs:
            p = '/configs/{}'.format(config)
            client.delete(p, recursive=True)

    client.ensure_path('/configs/new/managed-schema')
    client.set('/configs/new/managed-schema', b'')

if __name__ == '__main__':
    main()
