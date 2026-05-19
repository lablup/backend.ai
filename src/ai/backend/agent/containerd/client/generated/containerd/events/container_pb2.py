"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/events/container.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from ...containerd.types import fieldpath_pb2 as containerd_dot_types_dot_fieldpath__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!containerd/events/container.proto\x12\x11containerd.events\x1a\x19google/protobuf/any.proto\x1a containerd/types/fieldpath.proto"\xa9\x01\n\x0fContainerCreate\x12\n\n\x02id\x18\x01 \x01(\t\x12\r\n\x05image\x18\x02 \x01(\t\x12;\n\x07runtime\x18\x03 \x01(\x0b2*.containerd.events.ContainerCreate.Runtime\x1a>\n\x07Runtime\x12\x0c\n\x04name\x18\x01 \x01(\t\x12%\n\x07options\x18\x02 \x01(\x0b2\x14.google.protobuf.Any"\xb1\x01\n\x0fContainerUpdate\x12\n\n\x02id\x18\x01 \x01(\t\x12\r\n\x05image\x18\x02 \x01(\t\x12>\n\x06labels\x18\x03 \x03(\x0b2..containerd.events.ContainerUpdate.LabelsEntry\x12\x14\n\x0csnapshot_key\x18\x04 \x01(\t\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x1d\n\x0fContainerDelete\x12\n\n\x02id\x18\x01 \x01(\tB\x1eZ\x18containerd/events;events\xa0\xf4\x1e\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.events.container_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x18containerd/events;events\xa0\xf4\x1e\x01'
    _globals['_CONTAINERUPDATE_LABELSENTRY']._loaded_options = None
    _globals['_CONTAINERUPDATE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_CONTAINERCREATE']._serialized_start = 118
    _globals['_CONTAINERCREATE']._serialized_end = 287
    _globals['_CONTAINERCREATE_RUNTIME']._serialized_start = 225
    _globals['_CONTAINERCREATE_RUNTIME']._serialized_end = 287
    _globals['_CONTAINERUPDATE']._serialized_start = 290
    _globals['_CONTAINERUPDATE']._serialized_end = 467
    _globals['_CONTAINERUPDATE_LABELSENTRY']._serialized_start = 422
    _globals['_CONTAINERUPDATE_LABELSENTRY']._serialized_end = 467
    _globals['_CONTAINERDELETE']._serialized_start = 469
    _globals['_CONTAINERDELETE']._serialized_end = 498