import pytest


def pytest_addoption(parser):
    parser.addoption("--host", action="store", default="127.0.0.1", help="Milvus host")
    parser.addoption("--http_port", action="store", default="9091", help="Milvus http port")


@pytest.fixture
def host(request):
    return request.config.getoption("--host")


@pytest.fixture
def http_port(request):
    return request.config.getoption("--http_port")


