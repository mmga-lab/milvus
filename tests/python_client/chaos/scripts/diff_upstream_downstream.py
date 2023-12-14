"""
db --> collection --> partition

status:
entities num
load status
index status


then load partition
query all data
compare result

"""

from loguru import logger
import json
import pandas as pd
import collections.abc
from deepdiff import DeepDiff
from pymilvus import connections, Collection, db, list_collections
import threading


def convert_deepdiff(diff):
    if isinstance(diff, dict):
        return {k: convert_deepdiff(v) for k, v in diff.items()}
    elif isinstance(diff, collections.abc.Set):
        return list(diff)
    return diff


def flatten_dict(d, parent_key='', sep='_', depth=0, max_depth=3):
    """
    Flatten a nested dictionary up to a specified depth.

    :param d: The dictionary to flatten.
    :param parent_key: The base key for the flattened keys.
    :param sep: Separator to use between keys.
    :param depth: Current depth in the dictionary.
    :param max_depth: Maximum depth to flatten.
    :return: A flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict) and depth < max_depth - 1:
            items.extend(flatten_dict(v, new_key, sep, depth + 1, max_depth).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_collection_info(info, db_name, c_name):
    info[db_name][c_name] = {}
    c = Collection(c_name)
    info[db_name][c_name]['name'] = c.name
    logger.info(c.num_entities)
    info[db_name][c_name]['num_entities'] = c.num_entities
    logger.info(c.schema)
    info[db_name][c_name]['schema'] = len([f.name for f in c.schema.fields])
    logger.info(c.indexes)
    info[db_name][c_name]['indexes'] = [x.index_name for x in c.indexes]
    logger.info(c.partitions)
    info[db_name][c_name]['partitions'] = len([p.name for p in c.partitions])
    try:
        replicas = len(c.get_replicas().groups)
    except Exception as e:
        logger.warning(e)
        replicas = 0

    logger.info(replicas)
    info[db_name][c_name]['replicas'] = replicas


def get_cluster_info(host, port, user, password):
    try:
        connections.disconnect(alias='default')
    except Exception as e:
        logger.warning(e)
    if user and password:
        connections.connect(host=host, port=port, user=user, password=password)
    else:
        connections.connect(host=host, port=port)
    info = {}
    all_db = db.list_database()
    logger.info(all_db)
    for db_name in all_db:
        info[db_name] = {}
        db.using_database(db_name)
        all_collection = list_collections()
        logger.info(all_collection)
        threads = []
        for collection_name in all_collection:
            t = threading.Thread(target=get_collection_info, args=(info, db_name, collection_name))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

    logger.info(json.dumps(info, indent=2))
    return info


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='connection info')
    parser.add_argument('--upstream_host', type=str, default='10.100.36.179', help='milvus host')
    parser.add_argument('--downstream_host', type=str, default='10.100.36.178', help='milvus host')
    parser.add_argument('--port', type=str, default='19530', help='milvus port')
    parser.add_argument('--user', type=str, default='', help='milvus user')
    parser.add_argument('--password', type=str, default='', help='milvus password')
    args = parser.parse_args()
    upstream = get_cluster_info(args.upstream_host, args.port, args.user, args.password)
    downstream = get_cluster_info(args.downstream_host, args.port, args.user, args.password)
    logger.info(f"upstream info: {json.dumps(upstream, indent=2)}")
    logger.info(f"downstream info: {json.dumps(downstream, indent=2)}")
    diff = DeepDiff(upstream, downstream)
    diff = convert_deepdiff(diff)
    logger.info(f"diff: {json.dumps(diff, indent=2)}")
    with open("diff.json", "w") as f:
        json.dump(diff, f, indent=2)

    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', 500)
    # logger.info("compare with first layer")
    # flat_up = flatten_dict(upstream, max_depth=1)
    # flat_down = flatten_dict(downstream, max_depth=1)
    # df_compare = pd.DataFrame([flat_up, flat_down], index=['upstream', 'downstream']).T
    # df_compare["same"] = df_compare["upstream"] == df_compare["downstream"]
    # pd.set_option('display.max_rows', None)
    # logger.info(f"\n{df_compare}")
    # logger.info("compare with second layer")
    # flat_up = flatten_dict(upstream, max_depth=2)
    # flat_down = flatten_dict(downstream, max_depth=2)
    # df_compare = pd.DataFrame([flat_up, flat_down], index=['upstream', 'downstream']).T
    # df_compare["same"] = df_compare["upstream"] == df_compare["downstream"]
    # logger.info(f"\n{df_compare}")
    # logger.info("compare with third layer")
    # flat_up = flatten_dict(upstream)
    # flat_down = flatten_dict(downstream)
    # df_compare = pd.DataFrame([flat_up, flat_down], index=['upstream', 'downstream']).T
    # df_compare["same"] = df_compare["upstream"] == df_compare["downstream"]
    # pd.set_option('display.max_rows', None)
    # pd.set_option('display.max_colwidth', 1000)
    # logger.info(f"\n{df_compare}")
