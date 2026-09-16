from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class SessionStatus(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NOT_INITIALIZED: _ClassVar[SessionStatus]
    INITIALIZING: _ClassVar[SessionStatus]
    WAITING_FOR_AGENT: _ClassVar[SessionStatus]
    SUSPENDED: _ClassVar[SessionStatus]
    RESUMING: _ClassVar[SessionStatus]
    TERMINATED: _ClassVar[SessionStatus]
    PENDING: _ClassVar[SessionStatus]
    RUNNING: _ClassVar[SessionStatus]
    FINISHED: _ClassVar[SessionStatus]
    ERROR: _ClassVar[SessionStatus]
NOT_INITIALIZED: SessionStatus
INITIALIZING: SessionStatus
WAITING_FOR_AGENT: SessionStatus
SUSPENDED: SessionStatus
RESUMING: SessionStatus
TERMINATED: SessionStatus
PENDING: SessionStatus
RUNNING: SessionStatus
FINISHED: SessionStatus
ERROR: SessionStatus

class SessionMsg(_message.Message):
    __slots__ = ("session_id", "agent_name", "task_name", "start_time", "launch_status")
    SESSION_ID_FIELD_NUMBER: _ClassVar[int]
    AGENT_NAME_FIELD_NUMBER: _ClassVar[int]
    TASK_NAME_FIELD_NUMBER: _ClassVar[int]
    START_TIME_FIELD_NUMBER: _ClassVar[int]
    LAUNCH_STATUS_FIELD_NUMBER: _ClassVar[int]
    session_id: str
    agent_name: str
    task_name: str
    start_time: str
    launch_status: bool
    def __init__(self, session_id: _Optional[str] = ..., agent_name: _Optional[str] = ..., task_name: _Optional[str] = ..., start_time: _Optional[str] = ..., launch_status: bool = ...) -> None: ...

class QuerySessionStatusResult(_message.Message):
    __slots__ = ("session_msg", "session_status", "subject_id")
    SESSION_MSG_FIELD_NUMBER: _ClassVar[int]
    SESSION_STATUS_FIELD_NUMBER: _ClassVar[int]
    SUBJECT_ID_FIELD_NUMBER: _ClassVar[int]
    session_msg: SessionMsg
    session_status: SessionStatus
    subject_id: int
    def __init__(self, session_msg: _Optional[_Union[SessionMsg, _Mapping]] = ..., session_status: _Optional[_Union[SessionStatus, str]] = ..., subject_id: _Optional[int] = ...) -> None: ...
