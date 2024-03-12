import random
import json
import time
from sklearn import preprocessing
from pathlib import Path
import pandas as pd
import numpy as np
from pymilvus import Collection
from utils.utils import gen_collection_name
from utils.util_log import test_log as logger
import pytest
from base.testbase import TestBase


@pytest.mark.L0
class TestImportJob(TestBase):

    def test_job_e2e(self):
        # create collection
        name = gen_collection_name()
        dim = 128
        payload = {
            "collectionName": name,
            "schema": {
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "book_intro", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}}
                ]
            },
            "indexParams": [{"fieldName": "book_intro", "indexName": "book_intro_vector", "metricType": "L2"}]
        }
        rsp = self.collection_client.collection_create(payload)

        # upload file to storage
        data = [{
            "book_id": i,
            "word_count": i,
            "book_describe": f"book_{i}",
            "book_intro": [random.random() for _ in range(dim)]}
            for i in range(10000)]

        # dump data to file
        file_name = "bulk_insert_data.json"
        file_path = f"/tmp/{file_name}"
        with open(file_path, "w") as f:
            json.dump(data, f)
        # upload file to minio storage
        self.storage_client.upload_file(file_path, file_name)

        # create import job
        payload = {
            "collectionName": name,
            "files": [[file_name]],
        }
        rsp = self.import_job_client.create_import_jobs(payload)
        # list import job
        payload = {
            "collectionName": name,
        }
        rsp = self.import_job_client.list_import_jobs(payload)

        # get import job progress
        for task in rsp['data']:
            task_id = task['jobID']
            finished = False
            t0 = time.time()

            while not finished:
                rsp = self.import_job_client.get_import_job_progress(task_id)
                if rsp['data']['state'] == "Completed":
                    finished = True
                time.sleep(5)
                if time.time() - t0 > 120:
                    assert False, "import job timeout"
        time.sleep(10)
        # query data
        payload = {
            "collectionName": name,
            "filter": f"book_id in {[i for i in range(1000)]}",
            "limit": 100,
            "offset": 0,
            "outputFields": ["*"]
        }
        rsp = self.vector_client.vector_query(payload)
        assert len(rsp['data']) == 100

    def test_job_import_multi_json_file(self):
        # create collection
        name = gen_collection_name()
        dim = 128
        payload = {
            "collectionName": name,
            "schema": {
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "book_intro", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}}
                ]
            },
            "indexParams": [{"fieldName": "book_intro", "indexName": "book_intro_vector", "metricType": "L2"}]
        }
        rsp = self.collection_client.collection_create(payload)

        # upload file to storage
        file_nums = 2
        file_names = []
        for file_num in range(file_nums):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            # dump data to file
            file_name = f"bulk_insert_data_{file_num}.json"
            file_path = f"/tmp/{file_name}"
            # create dir for file path
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f)
            # upload file to minio storage
            self.storage_client.upload_file(file_path, file_name)
            file_names.append([file_name])

        # create import job
        payload = {
            "collectionName": name,
            "files": file_names,
        }
        rsp = self.import_job_client.create_import_jobs(payload)
        # list import job
        payload = {
            "collectionName": name,
        }
        rsp = self.import_job_client.list_import_jobs(payload)

        # get import job progress
        for job in rsp['data']:
            job_id = job['jobID']
            finished = False
            t0 = time.time()

            while not finished:
                rsp = self.import_job_client.get_import_job_progress(job_id)
                if rsp['data']['state'] == "Completed":
                    finished = True
                time.sleep(5)
                if time.time() - t0 > 120:
                    assert False, "import job timeout"
        time.sleep(10)
        # assert data count
        c = Collection(name)
        assert c.num_entities == 2000
        # assert import data can be queried
        payload = {
            "collectionName": name,
            "filter": f"book_id in {[i for i in range(1000)]}",
            "limit": 100,
            "offset": 0,
            "outputFields": ["*"]
        }
        rsp = self.vector_client.vector_query(payload)
        assert len(rsp['data']) == 100

    def test_job_import_multi_parquet_file(self):
        # create collection
        name = gen_collection_name()
        dim = 128
        payload = {
            "collectionName": name,
            "schema": {
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "book_intro", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}}
                ]
            },
            "indexParams": [{"fieldName": "book_intro", "indexName": "book_intro_vector", "metricType": "L2"}]
        }
        rsp = self.collection_client.collection_create(payload)

        # upload file to storage
        file_nums = 2
        file_names = []
        for file_num in range(file_nums):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            # dump data to file
            file_name = f"bulk_insert_data_{file_num}.parquet"
            file_path = f"/tmp/{file_name}"
            # create dir for file path
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(data)
            df.to_parquet(file_path, index=False)
            # upload file to minio storage
            self.storage_client.upload_file(file_path, file_name)
            file_names.append([file_name])

        # create import job
        payload = {
            "collectionName": name,
            "files": file_names,
        }
        rsp = self.import_job_client.create_import_jobs(payload)
        # list import job
        payload = {
            "collectionName": name,
        }
        rsp = self.import_job_client.list_import_jobs(payload)

        # get import job progress
        for job in rsp['data']:
            job_id = job['jobID']
            finished = False
            t0 = time.time()

            while not finished:
                rsp = self.import_job_client.get_import_job_progress(job_id)
                if rsp['data']['state'] == "Completed":
                    finished = True
                time.sleep(5)
                if time.time() - t0 > 120:
                    assert False, "import job timeout"
        time.sleep(10)
        # assert data count
        c = Collection(name)
        assert c.num_entities == 2000
        # assert import data can be queried
        payload = {
            "collectionName": name,
            "filter": f"book_id in {[i for i in range(1000)]}",
            "limit": 100,
            "offset": 0,
            "outputFields": ["*"]
        }
        rsp = self.vector_client.vector_query(payload)
        assert len(rsp['data']) == 100

    def test_job_import_multi_numpy_file(self):
        # create collection
        name = gen_collection_name()
        dim = 128
        payload = {
            "collectionName": name,
            "schema": {
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "book_intro", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}}
                ]
            },
            "indexParams": [{"fieldName": "book_intro", "indexName": "book_intro_vector", "metricType": "L2"}]
        }
        rsp = self.collection_client.collection_create(payload)

        # upload file to storage
        file_nums = 2
        file_names = []
        for file_num in range(file_nums):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            file_list = []
            # dump data to file
            file_dir = f"bulk_insert_data_{file_num}"
            base_file_path = f"/tmp/{file_dir}"
            df = pd.DataFrame(data)
            # each column is a list and convert to a npy file
            for column in df.columns:
                file_path = f"{base_file_path}/{column}.npy"
                # create dir for file path
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                file_name = f"{file_dir}/{column}.npy"
                np.save(file_path, np.array(df[column].values.tolist()))
                # upload file to minio storage
                self.storage_client.upload_file(file_path, file_name)
                file_list.append(file_name)
            file_names.append(file_list)
        # create import job
        payload = {
            "collectionName": name,
            "files": file_names,
        }
        rsp = self.import_job_client.create_import_jobs(payload)
        # list import job
        payload = {
            "collectionName": name,
        }
        rsp = self.import_job_client.list_import_jobs(payload)

        # get import job progress
        for job in rsp['data']:
            job_id = job['jobID']
            finished = False
            t0 = time.time()

            while not finished:
                rsp = self.import_job_client.get_import_job_progress(job_id)
                if rsp['data']['state'] == "Completed":
                    finished = True
                time.sleep(5)
                if time.time() - t0 > 120:
                    assert False, "import job timeout"
        time.sleep(10)
        # assert data count
        c = Collection(name)
        assert c.num_entities == 2000
        # assert import data can be queried
        payload = {
            "collectionName": name,
            "filter": f"book_id in {[i for i in range(1000)]}",
            "limit": 100,
            "offset": 0,
            "outputFields": ["*"]
        }
        rsp = self.vector_client.vector_query(payload)
        assert len(rsp['data']) == 100

    def test_job_import_multi_file_type(self):
        # create collection
        name = gen_collection_name()
        dim = 128
        payload = {
            "collectionName": name,
            "schema": {
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "book_intro", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}}
                ]
            },
            "indexParams": [{"fieldName": "book_intro", "indexName": "book_intro_vector", "metricType": "L2"}]
        }
        rsp = self.collection_client.collection_create(payload)

        # upload file to storage
        file_nums = 2
        file_names = []

        # numpy file
        for file_num in range(file_nums):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            file_list = []
            # dump data to file
            file_dir = f"bulk_insert_data_{file_num}"
            base_file_path = f"/tmp/{file_dir}"
            df = pd.DataFrame(data)
            # each column is a list and convert to a npy file
            for column in df.columns:
                file_path = f"{base_file_path}/{column}.npy"
                # create dir for file path
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
                file_name = f"{file_dir}/{column}.npy"
                np.save(file_path, np.array(df[column].values.tolist()))
                # upload file to minio storage
                self.storage_client.upload_file(file_path, file_name)
                file_list.append(file_name)
            file_names.append(file_list)
        # parquet file
        for file_num in range(2,file_nums+2):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            # dump data to file
            file_name = f"bulk_insert_data_{file_num}.parquet"
            file_path = f"/tmp/{file_name}"
            # create dir for file path
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(data)
            df.to_parquet(file_path, index=False)
            # upload file to minio storage
            self.storage_client.upload_file(file_path, file_name)
            file_names.append([file_name])
        # json file
        for file_num in range(4, file_nums+4):
            data = [{
                "book_id": i,
                "word_count": i,
                "book_describe": f"book_{i}",
                "book_intro": [random.random() for _ in range(dim)]}
                for i in range(1000*file_num, 1000*(file_num+1))]

            # dump data to file
            file_name = f"bulk_insert_data_{file_num}.json"
            file_path = f"/tmp/{file_name}"
            with open(file_path, "w") as f:
                json.dump(data, f)
            # upload file to minio storage
            self.storage_client.upload_file(file_path, file_name)
            file_names.append([file_name])

        # create import job
        payload = {
            "collectionName": name,
            "files": file_names,
        }
        rsp = self.import_job_client.create_import_jobs(payload)
        # list import job
        payload = {
            "collectionName": name,
        }
        rsp = self.import_job_client.list_import_jobs(payload)

        # get import job progress
        for job in rsp['data']:
            job_id = job['jobID']
            finished = False
            t0 = time.time()

            while not finished:
                rsp = self.import_job_client.get_import_job_progress(job_id)
                if rsp['data']['state'] == "Completed":
                    finished = True
                time.sleep(5)
                if time.time() - t0 > 120:
                    assert False, "import job timeout"
        time.sleep(10)
        # assert data count
        c = Collection(name)
        assert c.num_entities == 6000
        # assert import data can be queried
        payload = {
            "collectionName": name,
            "filter": f"book_id in {[i for i in range(1000)]}",
            "limit": 100,
            "offset": 0,
            "outputFields": ["*"]
        }
        rsp = self.vector_client.vector_query(payload)
        assert len(rsp['data']) == 100


    @pytest.mark.parametrize("insert_round", [1])
    @pytest.mark.parametrize("auto_id", [True, False])
    @pytest.mark.parametrize("is_partition_key", [True, False])
    @pytest.mark.parametrize("enable_dynamic_schema", [True, False])
    @pytest.mark.parametrize("nb", [3000])
    @pytest.mark.parametrize("dim", [128])
    def test_job_import_binlog_file_type(self, nb, dim, insert_round, auto_id,
                                                      is_partition_key, enable_dynamic_schema):
        # todo: copy binlog file to backup bucket
        """
        Insert a vector with a simple payload
        """
        # create a collection
        name = gen_collection_name()
        payload = {
            "collectionName": name,
            "schema": {
                "autoId": auto_id,
                "enableDynamicField": enable_dynamic_schema,
                "fields": [
                    {"fieldName": "book_id", "dataType": "Int64", "isPrimary": True, "elementTypeParams": {}},
                    {"fieldName": "user_id", "dataType": "Int64", "isPartitionKey": is_partition_key,
                     "elementTypeParams": {}},
                    {"fieldName": "word_count", "dataType": "Int64", "elementTypeParams": {}},
                    {"fieldName": "book_describe", "dataType": "VarChar", "elementTypeParams": {"max_length": "256"}},
                    {"fieldName": "bool", "dataType": "Bool", "elementTypeParams": {}},
                    {"fieldName": "json", "dataType": "JSON", "elementTypeParams": {}},
                    {"fieldName": "int_array", "dataType": "Array", "elementDataType": "Int64",
                     "elementTypeParams": {"max_capacity": "1024"}},
                    {"fieldName": "varchar_array", "dataType": "Array", "elementDataType": "VarChar",
                     "elementTypeParams": {"max_capacity": "1024", "max_length": "256"}},
                    {"fieldName": "bool_array", "dataType": "Array", "elementDataType": "Bool",
                     "elementTypeParams": {"max_capacity": "1024"}},
                    {"fieldName": "text_emb", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}},
                    {"fieldName": "image_emb", "dataType": "FloatVector", "elementTypeParams": {"dim": f"{dim}"}},
                ]
            },
            "indexParams": [
                {"fieldName": "text_emb", "indexName": "text_emb", "metricType": "L2"},
                {"fieldName": "image_emb", "indexName": "image_emb", "metricType": "L2"}
            ]
        }
        rsp = self.collection_client.collection_create(payload)
        assert rsp['code'] == 200
        rsp = self.collection_client.collection_describe(name)
        logger.info(f"rsp: {rsp}")
        assert rsp['code'] == 200
        # insert data
        for i in range(insert_round):
            data = []
            for i in range(nb):
                if auto_id:
                    tmp = {
                        "user_id": i,
                        "word_count": i,
                        "book_describe": f"book_{i}",
                        "bool": random.choice([True, False]),
                        "json": {"key": i},
                        "int_array": [i],
                        "varchar_array": [f"varchar_{i}"],
                        "bool_array": [random.choice([True, False])],
                        "text_emb": preprocessing.normalize([np.array([random.random() for _ in range(dim)])])[
                            0].tolist(),
                        "image_emb": preprocessing.normalize([np.array([random.random() for _ in range(dim)])])[
                            0].tolist(),
                    }
                else:
                    tmp = {
                        "book_id": i,
                        "user_id": i,
                        "word_count": i,
                        "book_describe": f"book_{i}",
                        "bool": random.choice([True, False]),
                        "json": {"key": i},
                        "int_array": [i],
                        "varchar_array": [f"varchar_{i}"],
                        "bool_array": [random.choice([True, False])],
                        "text_emb": preprocessing.normalize([np.array([random.random() for _ in range(dim)])])[
                            0].tolist(),
                        "image_emb": preprocessing.normalize([np.array([random.random() for _ in range(dim)])])[
                            0].tolist(),
                    }
                if enable_dynamic_schema:
                    tmp.update({f"dynamic_field_{i}": i})
                data.append(tmp)
            payload = {
                "collectionName": name,
                "data": data,
            }
            rsp = self.vector_client.vector_insert(payload)
            assert rsp['code'] == 200
            assert rsp['data']['insertCount'] == nb
        # query data to make sure the data is inserted
        rsp = self.vector_client.vector_query({"collectionName": name, "filter": "user_id > 0", "limit": 50})
        assert rsp['code'] == 200
        assert len(rsp['data']) == 50
        # get collection id
        c = Collection(name)
        res = c.describe()
        collection_id = res["collection_id"]
        # copy binlog to backup bucket
        rsp = self.storage_client.copy_file("milvus-bucket", "file/", "binlog")





@pytest.mark.L0
class TestImportJobNegative(TestBase):
    pass



