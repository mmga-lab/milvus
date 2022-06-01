import threading

import pytest
import os
import time
import json
from time import sleep
from minio import Minio
from pymilvus import connections
from chaos.checker import (CreateChecker, InsertFlushChecker, SearchChecker, QueryChecker, IndexChecker, DeleteChecker,
                           CompactChecker, DropChecker, LoadBalanceChecker, BulkLoadChecker,
                           Op)
from common.cus_resource_opts import CustomResourceOperations as CusResource
from common.milvus_sys import MilvusSys
from utils.util_log import test_log as log
from utils.util_k8s import wait_pods_ready, get_pod_list, get_pod_ip_name_pairs, get_milvus_instance_name
from utils.util_common import findkeys
from chaos import chaos_commons as cc
from common.common_type import CaseLabel
from common import common_func as cf
from chaos import constants
from delayed_assert import expect, assert_expectations


def assert_statistic(checkers, expectations={}):
    for k in checkers.keys():
        # expect succ if no expectations
        succ_rate = checkers[k].succ_rate()
        total = checkers[k].total()
        average_time = checkers[k].average_time
        if expectations.get(k, '') == constants.FAIL:
            log.info(f"Expect Fail: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
            expect(succ_rate < 0.49 or total < 2,
                   f"Expect Fail: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
        else:
            log.info(f"Expect Succ: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")
            expect(succ_rate > 0.90 or total > 2,
                   f"Expect Succ: {str(k)} succ rate {succ_rate}, total: {total}, average time: {average_time:.4f}")


def check_cluster_nodes(chaos_config):
     
    # if all pods will be effected, the expect is all fail. 
    # Even though the replicas is greater than 1, it can not provide HA, so cluster_nodes is set as 1 for this situation.
    if "all" in chaos_config["metadata"]["name"]:
        return 1
    
    selector = findkeys(chaos_config, "selector")
    selector = list(selector)
    log.info(f"chaos target selector: {selector}")
    # assert len(selector) == 1
    selector = selector[0]  # chaos yaml file must place the effected pod selector in the first position
    namespace = selector["namespaces"][0]
    labels_dict = selector["labelSelectors"]
    labels_list = []
    for k, v in labels_dict.items():
        labels_list.append(k+"="+v)
    labels_str = ",".join(labels_list)
    pods = get_pod_list(namespace, labels_str)
    return len(pods)


def record_results(checkers):
    res = ""
    for k in checkers.keys():
        check_result = checkers[k].check_result()
        res += f"{str(k):10} {check_result}\n"
    return res


class TestChaosBase:
    expect_create = constants.SUCC
    expect_insert = constants.SUCC
    expect_flush = constants.SUCC
    expect_index = constants.SUCC
    expect_search = constants.SUCC
    expect_query = constants.SUCC
    host = '127.0.0.1'
    port = 19530
    _chaos_config = None
    health_checkers = {}

    def parser_testcase_config(self, chaos_yaml, chaos_config):
        cluster_nodes = check_cluster_nodes(chaos_config)
        tests_yaml = constants.TESTS_CONFIG_LOCATION + 'testcases.yaml'
        tests_config = cc.gen_experiment_config(tests_yaml)
        test_collections = tests_config.get('Collections', None)
        for t in test_collections:
            test_chaos = t.get('testcase', {}).get('chaos', {})
            if test_chaos in chaos_yaml:
                expects = t.get('testcase', {}).get('expectation', {}).get('cluster_1_node', {})
                # for the cluster_n_node
                if cluster_nodes > 1:
                    expects = t.get('testcase', {}).get('expectation', {}).get('cluster_n_node', {})
                log.info(f"yaml.expects: {expects}")
                self.expect_create = expects.get(Op.create.value, constants.SUCC)
                self.expect_insert = expects.get(Op.insert.value, constants.SUCC)
                self.expect_flush = expects.get(Op.flush.value, constants.SUCC)
                self.expect_index = expects.get(Op.index.value, constants.SUCC)
                self.expect_search = expects.get(Op.search.value, constants.SUCC)
                self.expect_query = expects.get(Op.query.value, constants.SUCC)
                log.info(f"self.expects: create:{self.expect_create}, insert:{self.expect_insert}, "
                         f"flush:{self.expect_flush}, index:{self.expect_index}, "
                         f"search:{self.expect_search}, query:{self.expect_query}")
                return True

        return False


class TestChaos(TestChaosBase):

    @pytest.fixture(scope="function", autouse=True)
    def connection(self, host, port):
        connections.add_connection(default={"host": host, "port": port})
        connections.connect(alias='default')
        
        if connections.has_connection("default") is False:
            raise Exception("no connections")
        self.host = host
        self.port = port
        self.instance_name = get_milvus_instance_name(constants.CHAOS_NAMESPACE, host)



    @pytest.fixture(scope="function", autouse=True)
    def init_health_checkers(self):
        c_name = None
        checkers = {
            Op.create: CreateChecker(collection_name=c_name),
            Op.insert: InsertFlushChecker(collection_name=c_name),
            Op.flush: InsertFlushChecker(collection_name=c_name, flush=True),
            Op.index: IndexChecker(collection_name=c_name),
            Op.search: SearchChecker(collection_name=c_name),
            Op.query: QueryChecker(collection_name=c_name),
            Op.delete: DeleteChecker(collection_name=c_name),
            Op.compact: CompactChecker(collection_name=c_name),
            Op.drop: DropChecker(collection_name=c_name),
            Op.load_balance: LoadBalanceChecker(collection_name=c_name),
            Op.bulk_load: BulkLoadChecker(collection_name=c_name)
        }
        self.health_checkers = checkers

    @pytest.fixture(scope="function", autouse=True)
    def prepare_bulk_load(self, nb=30000, row_based=True):
        if Op.bulk_load not in self.health_checkers:
            log.info("bulk_load checker is not in  health checkers, skip prepare bulk load")
            return
        log.info("bulk_load checker is in  health checkers, prepare data firstly")
        release_name = self.instance_name
        minio_ip_pod_pair = get_pod_ip_name_pairs("chaos-testing", f"release={release_name}, app=minio")
        ms = MilvusSys()
        minio_ip = list(minio_ip_pod_pair.keys())[0]
        minio_port = "9000"
        minio_endpoint = f"{minio_ip}:{minio_port}"
        bucket_name = ms.index_nodes[0]["infos"]["system_configurations"]["minio_bucket_name"]
        schema = cf.gen_default_collection_schema()
        data = cf.gen_default_list_data_for_bulk_load(nb=nb)
        fields_name = [field.name for field in schema.fields]
        if not row_based:
            data_dict = dict(zip(fields_name, data))
        if row_based:
            entities = []
            for i in range(nb):
                entity_value = [field_values[i] for field_values in data]
                entity = dict(zip(fields_name, entity_value))
                entities.append(entity)
            data_dict = {"rows": entities}
        file_name = "bulk_load_data_source.json"
        files = [file_name]
        # TODO: npy file type is not supported so far
        log.info("generate bulk load file")
        with open(file_name, "w") as f:
            f.write(json.dumps(data_dict))
        log.info("upload file to minio")
        client = Minio(minio_endpoint, access_key="minioadmin", secret_key="minioadmin", secure=False)
        client.fput_object(bucket_name, file_name, file_name)
        self.health_checkers[Op.bulk_load].update(schema=schema, files=files, row_based=row_based)
        log.info("prepare data for bulk load done")

    def teardown(self):
        chaos_res = CusResource(kind=self._chaos_config['kind'],
                                group=constants.CHAOS_GROUP,
                                version=constants.CHAOS_VERSION,
                                namespace=constants.CHAOS_NAMESPACE)
        meta_name = self._chaos_config.get('metadata', None).get('name', None)
        chaos_res.delete(meta_name, raise_ex=False)
        sleep(2)
        log.info(f'Alive threads: {threading.enumerate()}')

    @pytest.mark.tags(CaseLabel.L3)
    @pytest.mark.parametrize('', cc.get_chaos_yamls())
    @pytest.mark.parametrize('chaos_yaml', cc.get_chaos_yamls())
    def test_chaos(self, chaos_yaml):
        # start the monitor threads to check the milvus ops
        log.info("*********************Chaos Test Start**********************")
        log.info(f"chaos_yaml: {chaos_yaml}")
        log.info(connections.get_connection_addr('default'))
        cc.start_monitor_threads(self.health_checkers)

        # parse chaos object
        chaos_config = cc.gen_experiment_config(chaos_yaml)
        release_name = constants.RELEASE_NAME
        log.info(f"release_name: {release_name}")
        chaos_config['metadata']['name'] = release_name
        kind = chaos_config['kind']
        meta_name = chaos_config.get('metadata', None).get('name', None)
        chaos_config_str = json.dumps(chaos_config)
        chaos_config_str = chaos_config_str.replace("milvus-chaos", release_name)
        chaos_config = json.loads(chaos_config_str)
        self._chaos_config = chaos_config  # cache the chaos config for tear down
        log.info(f"chaos_config: {chaos_config}")
        # parse the test expectations in testcases.yaml
        if self.parser_testcase_config(chaos_yaml, chaos_config) is False:
            log.error("Fail to get the testcase info in testcases.yaml")
            assert False

        # init report
        dir_name = "./reports"
        file_name = f"./reports/{meta_name}.log"
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        # wait 20s
        sleep(constants.WAIT_PER_OP * 2)

        # assert statistic:all ops 100% succ
        log.info("******1st assert before chaos: ")
        assert_statistic(self.health_checkers)
        try:
            with open(file_name, "a+") as f:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"{meta_name}-{ts}\n")
                f.write("1st assert before chaos:\n")
                f.write(record_results(self.health_checkers))
        except Exception as e:
            log.info(f"Fail to write to file: {e}")
        # apply chaos object
        chaos_res = CusResource(kind=chaos_config['kind'],
                                group=constants.CHAOS_GROUP,
                                version=constants.CHAOS_VERSION,
                                namespace=constants.CHAOS_NAMESPACE)
        chaos_res.create(chaos_config)
        log.info("chaos injected")
        # verify the chaos is injected
        log.info(f"kubectl get {kind} {meta_name} -n {constants.CHAOS_NAMESPACE}")
        os.system(f"kubectl get {kind} {meta_name} -n {constants.CHAOS_NAMESPACE}")
        sleep(constants.WAIT_PER_OP * 2)
        # reset counting
        cc.reset_counting(self.health_checkers)

        # wait 120s
        sleep(constants.CHAOS_DURATION)
        log.info(f'Alive threads: {threading.enumerate()}')

        # assert statistic
        log.info("******2nd assert after chaos injected: ")
        assert_statistic(self.health_checkers,
                         expectations={Op.create: self.expect_create,
                                       Op.insert: self.expect_insert,
                                       Op.flush: self.expect_flush,
                                       Op.index: self.expect_index,
                                       Op.search: self.expect_search,
                                       Op.query: self.expect_query
                                       })
        try:
            with open(file_name, "a+") as f:
                f.write("2nd assert after chaos injected:\n")
                f.write(record_results(self.health_checkers))
        except Exception as e:
            log.error(f"Fail to write the report: {e}")
        # delete chaos
        chaos_res.delete(meta_name)
        log.info("chaos deleted")
        # verify the chaos is deleted
        log.info(f"kubectl get {kind} {meta_name} -n {constants.CHAOS_NAMESPACE}")
        os.system(f"kubectl get {kind} {meta_name} -n {constants.CHAOS_NAMESPACE}")
        log.info(f'Alive threads: {threading.enumerate()}')
        sleep(2)
        # wait all pods ready
        log.info(f"wait for pods in namespace {constants.CHAOS_NAMESPACE} with label app.kubernetes.io/instance={meta_name}")
        wait_pods_ready(constants.CHAOS_NAMESPACE, f"app.kubernetes.io/instance={meta_name}")
        log.info(f"wait for pods in namespace {constants.CHAOS_NAMESPACE} with label release={meta_name}")
        wait_pods_ready(constants.CHAOS_NAMESPACE, f"release={meta_name}")
        log.info("all pods are ready")
        # reconnect if needed
        sleep(constants.WAIT_PER_OP * 2)
        cc.reconnect(connections, alias='default')
        # reset counting again
        cc.reset_counting(self.health_checkers)
        # wait 50s (varies by feature)
        sleep(constants.WAIT_PER_OP * 5)
        # assert statistic: all ops success again
        log.info("******3rd assert after chaos deleted: ")
        assert_statistic(self.health_checkers)
        try:
            with open(file_name, "a+") as f:
                f.write("3rd assert after chaos deleted:\n")
                f.write(record_results(self.health_checkers))
        except Exception as e:
            log.info(f"Fail to write the report: {e}")
        # assert all expectations
        assert_expectations()

        log.info("*********************Chaos Test Completed**********************")
