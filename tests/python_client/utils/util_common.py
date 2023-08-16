import glob
import time
from yaml import full_load
import json
import pandas as pd
from utils.util_log import test_log as log

def gen_experiment_config(yaml):
    """load the yaml file of chaos experiment"""
    with open(yaml) as f:
        _config = full_load(f)
        f.close()
    return _config


def findkeys(node, kv):
    # refer to https://stackoverflow.com/questions/9807634/find-all-occurrences-of-a-key-in-nested-dictionaries-and-lists
    if isinstance(node, list):
        for i in node:
            for x in findkeys(i, kv):
               yield x
    elif isinstance(node, dict):
        if kv in node:
            yield node[kv]
        for j in node.values():
            for x in findkeys(j, kv):
                yield x


def update_key_value(node, modify_k, modify_v):
    # update the value of modify_k to modify_v
    if isinstance(node, list):
        for i in node:
            update_key_value(i, modify_k, modify_v)
    elif isinstance(node, dict):
        if modify_k in node:
            node[modify_k] = modify_v
        for j in node.values():
            update_key_value(j, modify_k, modify_v)
    return node


def update_key_name(node, modify_k, modify_k_new):
    # update the name of modify_k to modify_k_new
    if isinstance(node, list):
        for i in node:
            update_key_name(i, modify_k, modify_k_new)
    elif isinstance(node, dict):
        if modify_k in node:
            value_backup = node[modify_k]
            del node[modify_k]
            node[modify_k_new] = value_backup
        for j in node.values():
            update_key_name(j, modify_k, modify_k_new)
    return node


def get_collections(file_name="all_collections.json"):
    try:
        with open(f"/tmp/ci_logs/{file_name}", "r") as f:
            data = json.load(f)
            collections = data["all"]
    except Exception as e:
        log.error(f"get_all_collections error: {e}")
        return []
    return collections


def get_deploy_test_collections():
    try:
        with open("/tmp/ci_logs/deploy_test_all_collections.json", "r") as f:
            data = json.load(f)
            collections = data["all"]
    except Exception as e:
        log.error(f"get_all_collections error: {e}")
        return []
    return collections


def get_chaos_test_collections():
    try:
        with open("/tmp/ci_logs/chaos_test_all_collections.json", "r") as f:
            data = json.load(f)
            collections = data["all"]
    except Exception as e:
        log.error(f"get_all_collections error: {e}")
        return []
    return collections


def wait_signal_to_apply_chaos():
    all_db_file = glob.glob("/tmp/ci_logs/event_records*.parquet")
    log.info(f"all files {all_db_file}")
    ready_apply_chaos = True
    timeout = 10*60
    t0 = time.time()
    for f in all_db_file:
        while True and (time.time() - t0 < timeout):
            df = pd.read_parquet(f)
            result = df[(df['event_name'] == 'init_chaos') & (df['event_status'] == 'ready')]
            if len(result) > 0:
                log.info(f"{f}: {result}")
                ready_apply_chaos = True
                break
            else:
                ready_apply_chaos = False
    return ready_apply_chaos






def initialize_request_records():
    con = duckdb.connect('/tmp/ci_logs/request_records.db', read_only=False)
    log.info(f"create table request_records")
    con.execute(
        "CREATE TABLE IF NOT EXISTS request_records (operation_name VARCHAR, collection_name VARCHAR, start_time TIMESTAMP , time_cost FLOAT, result VARCHAR)")
    con.execute(
        "CREATE TABLE IF NOT EXISTS event_records (event_type VARCHAR, event_operation VARCHAR, event_name VARCHAR, event_time TIMESTAMP , target VARCHAR)")
    return con


def initialize_event_records():
    con = duckdb.connect('/tmp/ci_logs/event_records.db', read_only=False)
    log.info(f"create table event_records")
    con.execute(
        "CREATE TABLE IF NOT EXISTS event_records (event_type VARCHAR, event_operation VARCHAR, event_name VARCHAR, event_time TIMESTAMP , target VARCHAR)")
    return con


def get_read_only_duckdb_connect():
    con = duckdb.connect('/tmp/ci_logs/duckdb.db', read_only=True)
    return con


def analyze_chaos_test_result():
    con = get_read_only_duckdb_connect()
    # get chaos start time
    table_name = "event_records"
    query = f"SELECT event_time FROM {table_name} WHERE event_operation = 'create'"
    res = con.execute(query).fetchall()
    chaos_start_time = res[0][0]
    log.info(f"chaos start time: {chaos_start_time}")
    # get chaos end time
    query = f"SELECT event_time FROM {table_name} WHERE event_operation = 'delete'"
    res = con.execute(query).fetchall()
    chaos_end_time = res[0][0]
    log.info(f"chaos end time: {chaos_end_time}")
    # get all request records
    table_name = "request_records"
    query = f"SELECT * FROM {table_name}"
    res = con.execute(query).fetchall()
    # analyze the result
    chaos_test_result = {}
    chaos_test_result["chaos_start_time"] = chaos_start_time
    chaos_test_result["chaos_end_time"] = chaos_end_time
    chaos_test_result["request_records"] = []
    for r in res:
        request_record = {}
        request_record["operation_name"] = r[0]
        request_record["collection_name"] = r[1]
        request_record["start_time"] = r[2]
        request_record["time_cost"] = r[3]
        request_record["result"] = r[4]
        chaos_test_result["request_records"].append(request_record)
    log.info(f"chaos_test_result: {chaos_test_result}")
    with open("/tmp/ci_logs/chaos_test_result.json", "w") as f:
        json.dump(chaos_test_result, f)
    return chaos_test_result


if __name__ == "__main__":
    d = { "id" : "abcde",
        "key1" : "blah",
        "key2" : "blah blah",
        "nestedlist" : [
        { "id" : "qwerty",
            "nestednestedlist" : [
            { "id" : "xyz", "keyA" : "blah blah blah" },
            { "id" : "fghi", "keyZ" : "blah blah blah" }],
            "anothernestednestedlist" : [
            { "id" : "asdf", "keyQ" : "blah blah" },
            { "id" : "yuiop", "keyW" : "blah" }] } ] }
    print(list(findkeys(d, 'id')))
    update_key_value(d, "none_id", "ccc")
    print(d)
