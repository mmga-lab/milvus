from api.collection import Collection


class TestDefault:


    def test_e2e(self):
        collection = Collection()
        payload = {
            "collection_name": "test",
            "dimension": 128,
            "index_file_size": 1024,
            "metric_type": "L2"
        }
        collection.create_collection(payload)

        collection.drop_collection(payload)
