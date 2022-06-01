from collections import defaultdict
import json
import argparse
from pymilvus import connections, list_collections
TIMEOUT = 120


def save_collections_by_marker(host="127.0.0.1", port="19530", marker="Checker"):
    # create connection
    connections.connect(host=host, port=port)
    all_collections = list_collections()
    all_collections = [c_name for c_name in all_collections if marker in c_name]
    m = defaultdict(list)
    for c_name in all_collections:
        prefix = c_name.split("_")[0]
        if len(m[prefix]) <= 2:
            m[prefix].append(c_name)
    selected_collections = []
    for v in m.values():
        selected_collections.extend(v)

    if len(selected_collections) == 0:
        selected_collections.append(None)
    data = {
        "all": selected_collections
    }
    with open("/tmp/ci_logs/all_collections.json", "w") as f:
        f.write(json.dumps(data))
    return selected_collections


parser = argparse.ArgumentParser(description='host ip')
parser.add_argument('--host', type=str, default='127.0.0.1', help='host ip')
args = parser.parse_args()
save_collections_by_marker(args.host)
