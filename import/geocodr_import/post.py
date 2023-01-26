import argparse
import logging
import textwrap
import time

from .solr import (
  SolrCloud,
  ignore_solr_error,
)


log = logging.getLogger('geocodr_import.post')


def main():
  curr_help = """
    This tool updates SolrCloud collections by importing the complete data into
    a new collection and swapping aliases.

    The tool makes the following assumptions:
        - You are using SolrCloud.
        - The target --collection does not exists (an alias with this name can
            exist).
        - There is a config set with the same name as --collection stored in
            your ZooKeeper instance.
        - You are importing the complete dataset from a --csv file.

    Steps:
        - Select a new collection name, either `mycollectionname-1` or
            `mycollectionname-2`, depending on which name the the existing
            alias points to.
        - Remove any existing collection with the selected name.
        - Create the new collection by using the configset with the same
            name as --collection.
        - Post --csv file into new collection.
        - Create/modify alias named after --collection to the new collection.
        """
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
  )
  logging.getLogger('urllib3').setLevel(logging.WARN)
  logging.getLogger('requests').setLevel(logging.WARN)

  parser = argparse.ArgumentParser(
    epilog=textwrap.dedent(curr_help),
    formatter_class=argparse.RawDescriptionHelpFormatter,
  )
  parser.add_argument("--url", default="http://localhost:8983/solr")
  parser.add_argument("--csv", required=True, help='csv data file to import')
  parser.add_argument("--collection", required=True,
                      help='name of the collection to import')
  parser.add_argument("--config-name",
                      help='name of the config set (stored in ZooKeeper). '
                           'Defaults to the name of your collection.')

  parser.add_argument("--solr-num-shards", default=2,
                      help='number of shards for new collection')
  parser.add_argument("--solr-replication-factor", default=2,
                      help='replication factor for new collection')

  args = parser.parse_args()
  cs = SolrCloud(args.url)

  collection = args.collection
  if args.config_name:
    config_name = args.config_name
  else:
    config_name = collection

  start = time.time()

  if collection in cs.list_collections().json()['collections']:
    log.error('target collection %s exists.', collection)
    return

  # check if we should insert into collection-1 or collection-2
  resp = cs.list_aliases()
  current_collection = resp.json()['aliases'].get(collection)
  if current_collection and current_collection.endswith('-1'):
    new_collection = collection + '-2'
  else:
    new_collection = collection + '-1'

  with ignore_solr_error():
    log.info('deleting old collection %s', new_collection)
    cs.delete_collection(new_collection)

  log.info('creating new collection %s', new_collection)
  cs.create_collection(
    new_collection,
    config_name=config_name,
    num_shards=args.solr_num_shards,
    replication_factor=args.solr_replication_factor,
  )

  log.info('posting new data from %s', args.csv)
  with open(args.csv, 'rb') as f:
    cs.update_csv(new_collection, f)

  log.info('linking %s to %s', new_collection, collection)
  cs.alias(new_collection, collection)

  log.info('import took %.2fs', time.time() - start)


if __name__ == '__main__':
  main()
