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




class TestAllOperations(TestChaosBase):

    @pytest.fixture(scope="function", autouse=True)
    def connection(self, host, port):
        connections.add_connection(default={"host": host, "port": port})
        connections.connect(alias='default')

        if connections.has_connection("default") is False:
            raise Exception("no connections")
        self.host = host
        self.port = port
        self.instance_name = get_milvus_instance_name(constants.CHAOS_NAMESPACE, host)

    # @pytest.fixture(scope="class", autouse=True)
    # def save_collection_name(self, host, port):
    #     selected_collections = cc.save_collections_by_marker(host=host, port=port, marker="Checker")
    #     log.info(f"Check the following collections: {selected_collections}")

    @pytest.fixture(scope="function", params=cc.get_all_collections())
    def collection_name(self, request):
        if request.param == [] or request.param == "":
            pytest.skip("The collection name is invalid")
        yield request.param

    def init_health_checkers(self, c_name=None):
        c_name = c_name
        checkers = {
            Op.insert: InsertFlushChecker(collection_name=c_name),
            Op.flush: InsertFlushChecker(collection_name=c_name, flush=True),
            Op.index: IndexChecker(collection_name=c_name),
            Op.search: SearchChecker(collection_name=c_name),
            Op.query: QueryChecker(collection_name=c_name),
            Op.delete: DeleteChecker(collection_name=c_name),
            Op.compact: CompactChecker(collection_name=c_name),
            Op.load_balance: LoadBalanceChecker(collection_name=c_name),
            Op.bulk_load: BulkLoadChecker(collection_name=c_name)
        }
        self.health_checkers = checkers
        self.prepare_bulk_load()

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
        if row_based:
            prefix = ""
        file_name = f"nb_{nb}_bulk_load_data_source.json"
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
        sleep(2)
        log.info(f'Alive threads: {threading.enumerate()}')

    @pytest.mark.tags(CaseLabel.L3)
    def test_all_operations(self, _collection_name=None):
        # start the monitor threads to check the milvus ops
        log.info("*********************Chaos Test Start**********************")
        log.info(connections.get_connection_addr('default'))
        self.init_health_checkers(c_name=_collection_name)
        cc.start_monitor_threads(self.health_checkers)

        # wait 20s
        sleep(constants.WAIT_PER_OP * 10)

        # assert statistic:all ops 100% succ
        log.info("******1st assert before chaos: ")
        assert_statistic(self.health_checkers)

        log.info("*********************Chaos Test Completed**********************")
