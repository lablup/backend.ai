"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/sandbox.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1econtainerd/types/sandbox.proto\x12\x10containerd.types\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x96\x04\n\x07Sandbox\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x122\n\x07runtime\x18\x02 \x01(\x0b2!.containerd.types.Sandbox.Runtime\x12"\n\x04spec\x18\x03 \x01(\x0b2\x14.google.protobuf.Any\x125\n\x06labels\x18\x04 \x03(\x0b2%.containerd.types.Sandbox.LabelsEntry\x12.\n\ncreated_at\x18\x05 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x06 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12=\n\nextensions\x18\x07 \x03(\x0b2).containerd.types.Sandbox.ExtensionsEntry\x12\x11\n\tsandboxer\x18\n \x01(\t\x1a>\n\x07Runtime\x12\x0c\n\x04name\x18\x01 \x01(\t\x12%\n\x07options\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01\x1aG\n\x0fExtensionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b2\x14.google.protobuf.Any:\x028\x01B\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.sandbox_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_SANDBOX_LABELSENTRY']._loaded_options = None
    _globals['_SANDBOX_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_SANDBOX_EXTENSIONSENTRY']._loaded_options = None
    _globals['_SANDBOX_EXTENSIONSENTRY']._serialized_options = b'8\x01'
    _globals['_SANDBOX']._serialized_start = 113
    _globals['_SANDBOX']._serialized_end = 647
    _globals['_SANDBOX_RUNTIME']._serialized_start = 465
    _globals['_SANDBOX_RUNTIME']._serialized_end = 527
    _globals['_SANDBOX_LABELSENTRY']._serialized_start = 529
    _globals['_SANDBOX_LABELSENTRY']._serialized_end = 574
    _globals['_SANDBOX_EXTENSIONSENTRY']._serialized_start = 576
    _globals['_SANDBOX_EXTENSIONSENTRY']._serialized_end = 647