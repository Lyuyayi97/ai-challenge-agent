from google.protobuf import struct_pb2 as _struct_pb2
from arena.message import basic_type_pb2 as _basic_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ExtraInfoList(_message.Message):
    __slots__ = ("extra_info",)
    EXTRA_INFO_FIELD_NUMBER: _ClassVar[int]
    extra_info: _containers.RepeatedCompositeFieldContainer[_basic_type_pb2.Pair]
    def __init__(self, extra_info: _Optional[_Iterable[_Union[_basic_type_pb2.Pair, _Mapping]]] = ...) -> None: ...

class ExtraMsg(_message.Message):
    __slots__ = ("extra_msg", "extra_info_list")
    EXTRA_MSG_FIELD_NUMBER: _ClassVar[int]
    EXTRA_INFO_LIST_FIELD_NUMBER: _ClassVar[int]
    extra_msg: _struct_pb2.Struct
    extra_info_list: ExtraInfoList
    def __init__(self, extra_msg: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., extra_info_list: _Optional[_Union[ExtraInfoList, _Mapping]] = ...) -> None: ...
