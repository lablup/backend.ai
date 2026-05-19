"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/streaming/v1/streaming.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n0containerd/services/streaming/v1/streaming.proto\x12 containerd.services.streaming.v1\x1a\x19google/protobuf/any.proto"\x18\n\nStreamInit\x12\n\n\x02id\x18\x01 \x01(\t2E\n\tStreaming\x128\n\x06Stream\x12\x14.google.protobuf.Any\x1a\x14.google.protobuf.Any(\x010\x01B,Z*containerd/services/streaming/v1;streamingb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.streaming.v1.streaming_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z*containerd/services/streaming/v1;streaming'
    _globals['_STREAMINIT']._serialized_start = 113
    _globals['_STREAMINIT']._serialized_end = 137
    _globals['_STREAMING']._serialized_start = 139
    _globals['_STREAMING']._serialized_end = 208