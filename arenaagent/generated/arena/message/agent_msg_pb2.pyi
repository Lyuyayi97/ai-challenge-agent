from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AgentMsg(_message.Message):
    __slots__ = ("name", "ue_server_ip", "ue_server_port", "ue_proto_server_port", "spawn_loc", "spawn_rot", "character_name", "fov", "width", "height")
    NAME_FIELD_NUMBER: _ClassVar[int]
    UE_SERVER_IP_FIELD_NUMBER: _ClassVar[int]
    UE_SERVER_PORT_FIELD_NUMBER: _ClassVar[int]
    UE_PROTO_SERVER_PORT_FIELD_NUMBER: _ClassVar[int]
    SPAWN_LOC_FIELD_NUMBER: _ClassVar[int]
    SPAWN_ROT_FIELD_NUMBER: _ClassVar[int]
    CHARACTER_NAME_FIELD_NUMBER: _ClassVar[int]
    FOV_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    name: str
    ue_server_ip: str
    ue_server_port: str
    ue_proto_server_port: str
    spawn_loc: str
    spawn_rot: str
    character_name: str
    fov: str
    width: str
    height: str
    def __init__(self, name: _Optional[str] = ..., ue_server_ip: _Optional[str] = ..., ue_server_port: _Optional[str] = ..., ue_proto_server_port: _Optional[str] = ..., spawn_loc: _Optional[str] = ..., spawn_rot: _Optional[str] = ..., character_name: _Optional[str] = ..., fov: _Optional[str] = ..., width: _Optional[str] = ..., height: _Optional[str] = ...) -> None: ...
