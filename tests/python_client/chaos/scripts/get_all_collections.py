# Copyright (C) 2019-2020 Zilliz. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License
# is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied. See the License for the specific language governing permissions and limitations under the License.


from collections import defaultdict
import json
import argparse
from pymilvus import connections, list_collections
TIMEOUT = 120


def save_all_collections(host="127.0.0.1"):
    # create connection
    connections.connect(host=host, port="19530")
    all_collections = list_collections()
    all_collections = [c_name for c_name in all_collections if "Checker" in c_name]
    m = defaultdict(list)
    for c_name in all_collections:
        prefix = c_name.split("_")[0]
        if len(m[prefix]) <= 10:
            m[prefix].append(c_name)
    selected_collections = []
    for v in m.values():
        selected_collections.extend(v)
    data = {
        "all": selected_collections
    }
    print("selected_collections is")
    print(selected_collections)
    with open("/tmp/ci_logs/all_collections.json", "w") as f:
        f.write(json.dumps(data))


parser = argparse.ArgumentParser(description='host ip')
parser.add_argument('--host', type=str, default='127.0.0.1', help='host ip')
args = parser.parse_args()
save_all_collections(args.host)
