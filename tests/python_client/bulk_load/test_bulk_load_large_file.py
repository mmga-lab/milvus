import logging
import time
import pytest
import random
from base.client_base import TestcaseBase
from common import common_func as cf
from common import common_type as ct
from common.common_type import CaseLabel, CheckTasks, BulkLoadStates
from utils.util_log import test_log as log
from bulk_load_data import (
    prepare_bulk_load_json_files,
    prepare_bulk_load_numpy_files,
    DataField as df,
    DataErrorType,
)
from pymilvus import (
    connections,
    list_collections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)

default_vec_only_fields = [df.vec_field]
default_multi_fields = [
    df.vec_field,
    df.int_field,
    df.string_field,
    df.bool_field,
    df.float_field,
]
default_vec_n_int_fields = [df.vec_field, df.int_field]


def entity_suffix(entities):
    if entities // 1000000 > 0:
        suffix = f"{entities // 1000000}m"
    elif entities // 1000 > 0:
        suffix = f"{entities // 1000}k"
    else:
        suffix = f"{entities}"
    return suffix


class TestBulkLoad(TestcaseBase):
    def test_float_vector_only(self):
        """
        collection: auto_id, customized_id
        collection schema: [pk, float_vector]
        Steps:
        1. create collection
        2. import data
        3. verify the data entities equal the import data
        4. load the collection
        5. verify search successfully
        6. verify query successfully
        """

        # intFeBig = np.load("/Users/zilliz/workspace/milvus/tests/python_client/assets/bulk_load/intFeBig.npy")
        # intFieBig2 = np.load("/Users/zilliz/workspace/milvus/tests/python_client/assets/bulk_load/intFeSmall.npy")
        # floatFieBig = np.load("/Users/zilliz/workspace/milvus/tests/python_client/assets/bulk_load/floatFeBig.npy")
        # print(len(intFeBig))
        # print(len(intFieBig2))
        # print(len(floatFieBig))
        connections.connect(host="10.101.103.246")
        c_name = "bulkloadbig"
        default_fields = [
            FieldSchema(name="intFieBig", dtype=DataType.INT64, is_primary=True),
            FieldSchema(
                name="intFieBig2",
                dtype=DataType.INT64,
            ),
            FieldSchema(name="floatFieBig", dtype=DataType.FLOAT_VECTOR, dim=1),
        ]
        default_schema = CollectionSchema(
            fields=default_fields, description="test collection"
        )
        collection = Collection(name=c_name, schema=default_schema)
        files = ["floatFieBig.npy", "intFieBig.npy", "intFieBig2.npy"]
        # import data
        t0 = time.time()
        task_ids = utility.bulk_load(
            collection_name=c_name, partition_name="", is_row_based=False, files=files
        )
        print(f"task_ids: {task_ids}")
        logging.info(f"bulk load task ids:{task_ids}")
        tt = time.time() - t0
        print(tt)
        time_cnt = 0
        while time_cnt < 3600:
            state = utility.get_bulk_load_state(task_ids[0])
            print(state)
            time.sleep(10)
            time_cnt += 10
            print("#"*30)
            print(f"has waited {time_cnt} seconds")
        num_entities = collection.num_entities
        print(num_entities)
            
