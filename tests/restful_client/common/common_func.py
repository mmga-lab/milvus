from enum import Enum
from common import common_type as ct


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



def gen_field():
    pass


def gen_bool_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_string_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_int8_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_int16_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_int32_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_int64_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_float_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_double_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_float_vec_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }


def gen_binary_vec_field(name=ct.default_bool_field_name, description=ct.default_desc, is_param=False, auto_id=False):
    return {
        "name": name,
        "description": description,
        "data_type": DataType.Bool.value,
        "is_primary_key": is_param,
        "autoID": auto_id,
    }
