from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class StartupMsg(_message.Message):
    __slots__ = ("agent_name", "task_name", "ue_address", "generic_rpc_port", "grpc_port")
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    UE_ADDRESS_FIELD_NUMBER: _ClassVar[int]
    GENERIC_RPC_PORT_FIELD_NUMBER: _ClassVar[int]
    GRPC_PORT_FIELD_NUMBER: _ClassVar[int]
    agent_name: str
    task_name: str
    ue_address: str
    generic_rpc_port: str
    grpc_port: str
    def __init__(self, agent_name: _Optional[str] = ..., task_name: _Optional[str] = ..., ue_address: _Optional[str] = ..., generic_rpc_port: _Optional[str] = ..., grpc_port: _Optional[str] = ...) -> None: ...

class TaskDifficultyMsg(_message.Message):
    __slots__ = ("vision", "language", "motion", "recognition", "study", "value")
    VISION_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    MOTION_FIELD_NUMBER: _ClassVar[int]
    RECOGNITION_FIELD_NUMBER: _ClassVar[int]
    STUDY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    vision: int
    language: int
    motion: int
    recognition: int
    study: int
    value: int
    def __init__(self, vision: _Optional[int] = ..., language: _Optional[int] = ..., motion: _Optional[int] = ..., recognition: _Optional[int] = ..., study: _Optional[int] = ..., value: _Optional[int] = ...) -> None: ...
