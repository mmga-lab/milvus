import time

import pytest
from minio import Minio
import json
from pymilvus import connections, utility, Collection, BulkLoadState
from common import common_func as cf
from utils.util_log import test_log as log
from common.milvus_sys import MilvusSys
from utils.util_k8s import get_milvus_instance_name, get_pod_ip_name_pairs


class TestBulkLoad:

    @pytest.fixture(scope="function", autouse=True)
    def connection(self, host, port):
        connections.add_connection(default={"host": host, "port": port})
        connections.connect(alias='default')

        if connections.has_connection("default") is False:
            raise Exception("no connections")
        self.instance_name = get_milvus_instance_name("chaos-testing", host)

    @pytest.mark.parametrize("is_row_based", [True])
    @pytest.mark.parametrize("nb", [1000])
    def test_bulk_load(self, is_row_based, nb):

        # init schema
        log.info("init schema")
        schema = cf.gen_default_collection_schema()
        data = cf.gen_default_list_data_for_bulk_load(nb=1000)
        fields_name = [field.name for field in schema.fields]
        # generate data
        log.info("generate bulk load file")
        if not is_row_based:
            data_dict = dict(zip(fields_name, data))
        if is_row_based:
            entities = []
            for i in range(nb):
                entity_value = [field_values[i] for field_values in data]
                entity = dict(zip(fields_name, entity_value))
                entities.append(entity)
            data_dict = {"rows": entities}
        file_name = "/tmp/ci_logs/bulk_load_data_source.json"
        log.info("generate bulk load file")
        with open(file_name, "w") as f:
            f.write(json.dumps(data_dict, indent=4))
        # update data
        log.info("upload file to minio")
        ms = MilvusSys()
        minio_ip_pod_pair = get_pod_ip_name_pairs(
            "chaos-testing", f"release={self.instance_name}, app=minio")
        minio_ip = list(minio_ip_pod_pair.keys())[0]
        bucket_name = ms.index_nodes[0]["infos"]["system_configurations"]["minio_bucket_name"]
        minio_port = "9000"
        minio_endpoint = f"{minio_ip}:{minio_port}"
        client = Minio(minio_endpoint, access_key="minioadmin",
                       secret_key="minioadmin", secure=False)
        client.fput_object(bucket_name, file_name, file_name)
        # bulk load data
        log.info("bulk load data")
        file_names = [file_name]
        c_name = cf.gen_unique_str("BulkLoadChecker_")
        collection = Collection(name="hello_milvus", schema=schema)
        task_ids = utility.bulk_load(collection_name="hello_milvus",
                                    is_row_based=is_row_based,
                                    files=file_names)
        log.info(f"task_ids: {task_ids}")
        time_cnt = 0
        tasks = utility.list_bulk_load_tasks()
        for task in tasks:
            log.info(f"The task {task.task_id} state is {task.state_name}")

        log.info("#"*15)
        time.sleep(5)
        tasks = utility.list_bulk_load_tasks()
        for task in tasks:
            log.info(f"The task {task.task_id} state is {task.state_name}")

        while time_cnt <= 60:
            time.sleep(10)
            time_cnt += 10
            for id in task_ids:
                state = utility.get_bulk_load_state(task_id=id)
                log.info(f"{state=}")
        log.info(f"num_entities: {collection.num_entities}")
