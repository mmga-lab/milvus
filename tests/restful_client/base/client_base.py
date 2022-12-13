from decorest import HttpStatus, RestClient

from base.collection_service import CollectionService
from base.index_service import IndexService
from base.entity_service import EntityService

from utils.util_log import test_log as log

class Base:
    """init base class"""
    def setup_class(self):
        log.info("setup class")

    def teardown_class(self):
        log.info("teardown class")

    def setup_method(self, method):
        log.info(("*" * 35) + " setup " + ("*" * 35))
        log.info("[setup_method] Start setup test case %s." % method.__name__)

    def teardown_method(self, method):
        log.info("[teardown_method] Start teardown test case %s." % method.__name__)
        log.info(("*" * 35) + " teardown " + ("*" * 35))


class TestBase(Base):
    """init test base class"""

    def __init__(self):
        self.entity_service = None

    def init_client(self, host, http_port):
        self.host = host
        self.http_port = http_port
        self.end_point = "http://" + self.host + ":" + str(self.http_port) + "/api/v1"
        self.rest_client = RestClient(self.end_point, timeout=30)
        self.collection_service = CollectionService(self.rest_client)
        self.index_service = IndexService(self.rest_client)
        self.entity_service = EntityService(self.rest_client)



