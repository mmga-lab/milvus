from collections import defaultdict
import json
import os
import threading
import glob
from pymilvus import connections, list_collections
from chaos import constants
from yaml import full_load
from utils.util_log import test_log as log


def check_config(chaos_config):
    if not chaos_config.get('kind', None):
        raise Exception("kind must be specified")
    if not chaos_config.get('spec', None):
        raise Exception("spec must be specified")
    if "action" not in chaos_config.get('spec', None):
        raise Exception("action must be specified in spec")
    if "selector" not in chaos_config.get('spec', None):
        raise Exception("selector must be specified in spec")
    return True


def reset_counting(checkers={}):
    """reset checker counts for all checker threads"""
    for ch in checkers.values():
        ch.reset()


def gen_experiment_config(yaml):
    """load the yaml file of chaos experiment"""
    with open(yaml) as f:
        _config = full_load(f)
        f.close()
    return _config


def start_monitor_threads(checkers={}):
    """start the threads by checkers"""
    for k, ch in checkers.items():
        t = threading.Thread(target=ch.keep_running, args=(), name=k, daemon=True)
        t.start()


def get_env_variable_by_name(name):
    """ get env variable by name"""
    try:
        env_var = os.environ[name]
        log.debug(f"env_variable: {env_var}")
        return str(env_var)
    except Exception as e:
        log.debug(f"fail to get env variables, error: {str(e)}")
        return None


def get_chaos_yamls():
    """get chaos yaml file(s) from configured environment path"""
    chaos_env = get_env_variable_by_name(constants.CHAOS_CONFIG_ENV)
    if chaos_env is not None:
        if os.path.isdir(chaos_env):
            log.debug(f"chaos_env is a dir: {chaos_env}")
            return glob.glob(chaos_env + 'chaos_*.yaml')
        elif os.path.isfile(chaos_env):
            log.debug(f"chaos_env is a file: {chaos_env}")
            return [chaos_env]
        else:
            # not a valid directory, return default
            pass
    log.debug("not a valid directory or file, return default chaos config path")
    return glob.glob(constants.TESTS_CONFIG_LOCATION + constants.ALL_CHAOS_YAMLS)


def reconnect(connections, alias='default'):
    """trying to connect by connection alias"""
    res = connections.get_connection_addr(alias)
    connections.remove_connection(alias)
    return connections.connect(alias, host=res["host"], port=res["port"])

def save_collections_by_marker(host="127.0.0.1", port="19530", marker="Checker"):
    # create connection
    connections.connect(host=host, port=port)
    all_collections = list_collections()
    all_collections = [c_name for c_name in all_collections if marker in c_name]
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
    return selected_collections


def get_all_collections():
    try:
        with open("/tmp/ci_logs/all_collections.json", "r") as f:
            data = json.load(f)
            all_collections = data["all"]
    except Exception as e:
        log.error(f"get_all_collections error: {e}")
        return []
    return all_collections
