import os
import random
import string
import numpy as np
from enum import Enum
from common import common_type as ct
from utils.util_log import test_log as log


class ParamInfo:
    def __init__(self):
        self.param_host = ""
        self.param_port = ""

    def prepare_param_info(self, host, http_port):
        self.param_host = host
        self.param_port = http_port


param_info = ParamInfo()


class DataType(Enum):
    Bool: 1
    Int8: 2
    Int16: 3
    Int32: 4
    Int64: 5
    Float: 10
    Double: 11
    String: 20
    VarChar: 21
    BinaryVector: 100
    FloatVector: 101


def gen_unique_str(str_value=None):
    prefix = "".join(random.choice(string.ascii_letters + string.digits) for _ in range(8))
    return "test_" + prefix if str_value is None else str_value + "_" + prefix


def gen_field(name=ct.default_bool_field_name, description=ct.default_desc, type_params=None, index_params=None,
              data_type="Int64", is_primary_key=False, auto_id=False, dim=128, max_length=256):
    data_type_map = {
        "Bool": 1,
        "Int8": 2,
        "Int16": 3,
        "Int32": 4,
        "Int64": 5,
        "Float": 10,
        "Double": 11,
        "String": 20,
        "VarChar": 21,
        "BinaryVector": 100,
        "FloatVector": 101,
    }
    if data_type == "Int64":
        is_primary_key = True
        auto_id = True
    if type_params is None:
        type_params = []
    if index_params is None:
        index_params = []
    if data_type in ["FloatVector", "BinaryVector"]:
        type_params = [{"key": "dim", "value": str(dim)}]
    if data_type in ["String", "VarChar"]:
        type_params = [{"key": "max_length", "value": str(dim)}]
    return {
        "name": name,
        "description": description,
        "data_type": data_type_map.get(data_type, 0),
        "type_params": type_params,
        "index_params": index_params,
        "is_primary_key": is_primary_key,
        "auto_id": auto_id,
    }


def gen_schema(name, fields, description=ct.default_desc, auto_id=False):
    return {
        "name": name,
        "description": description,
        "auto_id": auto_id,
        "fields": fields,
    }


def gen_default_schema(data_types=None, dim=ct.default_dim, collection_name=None):
    if data_types is None:
        data_types = ["Int64", "Float", "VarChar", "FloatVector"]
    fields = []
    for data_type in data_types:
        if data_type in ["FloatVector", "BinaryVector"]:
            fields.append(gen_field(name=data_type, data_type=data_type, type_params=[{"key": "dim", "value": dim}]))
        else:
            fields.append(gen_field(name=data_type, data_type=data_type))
    return {
        "autoID": True,
        "fields": fields,
        "description": ct.default_desc,
        "name": collection_name,
    }


def gen_fields_data(schema=None, nb=ct.default_nb,):
    if schema is None:
        schema = gen_default_schema()
    fields = schema["fields"]
    fields_data = []
    for field in fields:
        if field["data_type"] == 1:
            fields_data.append([random.choice([True, False]) for i in range(nb)])
        elif field["data_type"] == 2:
            fields_data.append([random.randint(-128, 127) for i in range(nb)])
        elif field["data_type"] == 3:
            fields_data.append([random.randint(-32768, 32767) for i in range(nb)])
        elif field["data_type"] == 4:
            fields_data.append([random.randint(-2147483648, 2147483647) for i in range(nb)])
        elif field["data_type"] == 5:
            fields_data.append([random.randint(-9223372036854775808, 9223372036854775807) for i in range(nb)])
        elif field["data_type"] == 10:
            fields_data.append([np.float64(i) for i in range(nb)])  # json not support float32
        elif field["data_type"] == 11:
            fields_data.append([np.float64(i) for i in range(nb)])
        elif field["data_type"] == 20:
            fields_data.append([gen_unique_str((str(i))) for i in range(nb)])
        elif field["data_type"] == 21:
            fields_data.append([gen_unique_str(str(i)) for i in range(nb)])
        elif field["data_type"] == 100:
            dim = ct.default_dim
            for k, v in field["type_params"]:
                if k == "dim":
                    dim = int(v)
                    break
            fields_data.append(gen_binary_vectors(nb, dim))
        elif field["data_type"] == 101:
            dim = ct.default_dim
            for k, v in field["type_params"]:
                if k == "dim":
                    dim = int(v)
                    break
            fields_data.append(gen_float_vectors(nb, dim))
        else:
            log.error("Unknown data type.")
    fields_data_body = []
    for i, field in enumerate(fields):
        fields_data_body.append({
            "field_name": field["name"],
            "type": field["data_type"],
            "field": fields_data[i],
        })
    return fields_data_body


def gen_float_vectors(nb, dim):
    return [[np.float64(random.uniform(-1.0, 1.0)) for _ in range(dim)] for _ in range(nb)]  # json not support float32


def gen_binary_vectors(nb, dim):
    raw_vectors = []
    binary_vectors = []
    for _ in range(nb):
        raw_vector = [random.randint(0, 1) for _ in range(dim)]
        raw_vectors.append(raw_vector)
        # packs a binary-valued array into bits in a unit8 array, and bytes array_of_ints
        binary_vectors.append(bytes(np.packbits(raw_vector, axis=-1).tolist()))
    return binary_vectors


def gen_default_index_params(index_type=None):
    if index_type is None:
        index_type = ct.default_index
    extra_params = []
    for k, v in index_type.items():
        item = {"key": k, "value": v}
        extra_params.append(item)


    if index_type is None:
        index_type = ct.default_index
    if index_type == "IVF_FLAT":
        return {"index_type": index_type, "metric_type": "L2", "params": {"nlist": 64}}



def modify_file(file_path_list, is_modify=False, input_content=""):
    """
    file_path_list : file list -> list[<file_path>]
    is_modify : does the file need to be reset
    input_content ：the content that need to insert to the file
    """
    if not isinstance(file_path_list, list):
        log.error("[modify_file] file is not a list.")

    for file_path in file_path_list:
        folder_path, file_name = os.path.split(file_path)
        if not os.path.isdir(folder_path):
            log.debug("[modify_file] folder(%s) is not exist." % folder_path)
            os.makedirs(folder_path)

        if not os.path.isfile(file_path):
            log.error("[modify_file] file(%s) is not exist." % file_path)
        else:
            if is_modify is True:
                log.debug("[modify_file] start modifying file(%s)..." % file_path)
                with open(file_path, "r+") as f:
                    f.seek(0)
                    f.truncate()
                    f.write(input_content)
                    f.close()
                log.info("[modify_file] file(%s) modification is complete." % file_path_list)


if __name__ == '__main__':
    a = gen_binary_vectors(10, 128)
    print(a)
