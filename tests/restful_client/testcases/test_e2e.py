from base.client_base import TestBase
from utils.util_log import test_log as log


class TestDefault(TestBase):

    def test_e2e(self):
        collection_name = self.init_collection()
        log.info(f"collection name: {collection_name}")

        assert 1 == 1


