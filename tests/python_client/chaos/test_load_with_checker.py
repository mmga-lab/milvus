import threading
import pytest
import json
from time import sleep
from minio import Minio
from pymilvus import connections
from chaos.checker import (CreateChecker,
                           InsertChecker,
                           FlushChecker,
                           SearchChecker,
                           QueryChecker,
                           IndexChecker,
                           DeleteChecker,
                           CompactChecker,
                           DropChecker,
                           LoadBalanceChecker,
                           BulkLoadChecker,
                           Op)
from common.cus_resource_opts import CustomResourceOperations as CusResource
from common.milvus_sys import MilvusSys
from utils.util_log import test_log as log
from utils.util_k8s import get_pod_ip_name_pairs, get_milvus_instance_name
from chaos import chaos_commons as cc
from common.common_type import CaseLabel
from common import common_func as cf
from chaos import constants


class TestChaosBase:
    expect_create = constants.SUCC
    expect_insert = constants.SUCC
    expect_flush = constants.SUCC
    expect_index = constants.SUCC
    expect_search = constants.SUCC
    expect_query = constants.SUCC
    expect_delete = constants.SUCC
    host = '127.0.0.1'
    port = 19530
    _chaos_config = None
    health_checkers = {}


class TestChaos(TestChaosBase):

    @pytest.fixture(scope="function", autouse=True)
    def connection(self, host, port):
        connections.connect("default", host=host, port=port)

        if connections.has_connection("default") is False:
            raise Exception("no connections")
        self.host = host
        self.port = port

    @pytest.fixture(scope="function", autouse=True)
    def init_health_checkers(self):
        c_name = cf.gen_unique_str("Checker_")
        checkers = {
            Op.insert: InsertChecker(collection_name=c_name),
            Op.flush: FlushChecker(collection_name=c_name),
            Op.query: QueryChecker(collection_name=c_name),
            Op.search: SearchChecker(collection_name=c_name),
            Op.delete: DeleteChecker(collection_name=c_name),
            Op.compact: CompactChecker(collection_name=c_name),
            Op.index: IndexChecker(collection_name=c_name),
        }
        self.health_checkers = checkers

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
    def test_load_generator(self):
        # start the monitor threads to check the milvus ops
        log.info("*********************Chaos Test Start**********************")
        log.info(connections.get_connection_addr('default'))
        cc.start_monitor_threads(self.health_checkers)

        log.info("start checkers")
        sleep(30)
        for k, v in self.health_checkers.items():
            v.check_result()
        sleep(600)
