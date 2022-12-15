from decorest import HttpStatus, RestClient
from models.schema import CollectionSchema
from base.collection_service import CollectionService
from base.index_service import IndexService
from base.entity_service import EntityService

from utils.util_log import test_log as log
from common import common_func as cf
from common import common_type as ct

class Base:
    """init base class"""

    endpoint = None
    collection_service = None
    index_service = None
    entity_service = None

    def setup_class(self):
        log.info("setup class")

    def teardown_class(self):
        log.info("teardown class")

    def setup_method(self, method):
        log.info(("*" * 35) + " setup " + ("*" * 35))
        log.info("[setup_method] Start setup test case %s." % method.__name__)
        host = cf.param_info.param_host
        port = cf.param_info.param_port
        self.endpoint = "http://" + host + ":" + str(port) + "/api/v1"
        self.collection_service = CollectionService(self.endpoint)
        self.index_service = IndexService(self.endpoint)
        self.entity_service = EntityService(self.endpoint)

    def teardown_method(self, method):
        log.info("[teardown_method] Start teardown test case %s." % method.__name__)
        log.info(("*" * 35) + " teardown " + ("*" * 35))


class TestBase(Base):
    """init test base class"""

    def init_collection(self, name=None, schema=None, nb=ct.default_nb, **kwargs):
        collection_name = cf.gen_unique_str("test") if name is None else name
        if schema is None:
            schema = cf.gen_default_schema(collection_name=collection_name)
        res = self.collection_service.create_collection(collection_name=collection_name, schema=schema)
        log.info(res)
        res = self.entity_service.insert(collection_name=collection_name, fields_data=cf.gen_fields_data(schema, nb=nb),
                                         num_rows=nb)
        log.info(res)
        res = self.entity_service.flush(collection_names=[collection_name])
        log.info(res)
        # create index
        index_params = cf.gen_default_index_params()
        res = self.index_service.create_index(collection_name=collection_name)
        return collection_name




