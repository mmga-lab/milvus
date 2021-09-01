import docker

from pymilvus import (
    connections, FieldSchema, CollectionSchema, DataType,
    Collection, list_collections,
)

from utils import *

connections.connect()

list_containers()

get_collections()

load_and_search()

create_index()

load_and_search()
