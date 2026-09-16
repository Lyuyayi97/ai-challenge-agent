from arena.message import basic_type_pb2 as _basic_type_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class QuestionMsg(_message.Message):
    __slots__ = ("question_text", "options", "is_reply_received", "subject_index", "reply_text", "is_reply_correct")
    QUESTION_TEXT_FIELD_NUMBER: _ClassVar[int]
    OPTIONS_FIELD_NUMBER: _ClassVar[int]
    IS_REPLY_RECEIVED_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_INDEX_FIELD_NUMBER: _ClassVar[int]
    REPLY_TEXT_FIELD_NUMBER: _ClassVar[int]
    IS_REPLY_CORRECT_FIELD_NUMBER: _ClassVar[int]
    question_text: str
    options: _containers.RepeatedCompositeFieldContainer[_basic_type_pb2.Pair]
    is_reply_received: bool
    subject_index: int
    reply_text: str
    is_reply_correct: bool
    def __init__(self, question_text: _Optional[str] = ..., options: _Optional[_Iterable[_Union[_basic_type_pb2.Pair, _Mapping]]] = ..., is_reply_received: bool = ..., subject_index: _Optional[int] = ..., reply_text: _Optional[str] = ..., is_reply_correct: bool = ...) -> None: ...
