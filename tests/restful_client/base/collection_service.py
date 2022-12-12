from api.collection import Collection
from models import common, schema, milvus, server


TIMEOUT = 30


class CollectionService:

    def __init__(self, endpoint=None, timeout=None):
        if timeout is None:
            timeout = TIMEOUT
        if endpoint is None:
            endpoint = "http://localhost:9091/api/v1"
        self._collection = Collection(endpoint=endpoint, timeout=timeout)

    def create_collection(self, collection_name, consistency_level=1, schema=None, shards_num=1):

        payload = milvus.CreateCollectionRequest(collection_name=collection_name,
                                                 consistency_level=consistency_level,
                                                 schema=schema,
                                                 shards_num=shards_num)
        payload = payload.dict()
        return self._collection.create_collection(payload)

    def has_collection(self, collection_name, time_stamp=0):
        payload = milvus.HasCollectionRequest(collection_name=collection_name, time_stamp=time_stamp)
        payload = payload.dict()
        return self._collection.has_collection(payload)

    def drop_collection(self, collection_name):
        payload = milvus.DropCollectionRequest(collection_name=collection_name)
        payload = payload.dict()
        return self._collection.drop_collection(payload)

    def describe_collection(self, collection_name, collection_id=None, time_stamp=0):
        payload = milvus.DescribeCollectionRequest(collection_name=collection_name,
                                                   collectionID=collection_id,
                                                   time_stamp=time_stamp)
        payload = payload.dict()
        return self._collection.describe_collection(payload)

    def load_collection(self, collection_name, replica_number=1):
        payload = milvus.LoadCollectionRequest(collection_name=collection_name, replica_number=replica_number)
        payload = payload.dict()
        return self._collection.load_collection(payload)

    def release_collection(self, collection_name):
        payload = milvus.ReleaseCollectionRequest(collection_name=collection_name)
        payload = payload.dict()
        return self._collection.release_collection(payload)

    def get_collection_statistics(self, collection_name):
        payload = milvus.GetCollectionStatisticsRequest(collection_name=collection_name)
        payload = payload.dict()
        return self._collection.get_collection_statistics(payload)

    def show_collections(self, collection_names=None, type=None):
        payload = milvus.ShowCollectionsRequest(collection_names=collection_names, type=type)
        payload = payload.dict()
        return self._collection.show_collections(payload)
