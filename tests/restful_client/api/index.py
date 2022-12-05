from decorest import GET, POST, DELETE
from decorest import HttpStatus, RestClient
from decorest import accept, body, content, endpoint, form
from decorest import header, multipart, on, query, stream, timeout


class Index(RestClient):

    def drop_index():
        pass

    def describe_index():
        pass

    def create_index():
        pass

    def get_index_build_progress():
        pass

    def get_index_state():
        pass