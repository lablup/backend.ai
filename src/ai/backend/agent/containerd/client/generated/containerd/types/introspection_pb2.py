"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/introspection.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n$containerd/types/introspection.proto\x12\x10containerd.types\x1a\x19google/protobuf/any.proto"M\n\x0eRuntimeRequest\x12\x14\n\x0cruntime_path\x18\x01 \x01(\t\x12%\n\x07options\x18\x02 \x01(\x0b2\x14.google.protobuf.Any"3\n\x0eRuntimeVersion\x12\x0f\n\x07version\x18\x01 \x01(\t\x12\x10\n\x08revision\x18\x02 \x01(\t"\x96\x02\n\x0bRuntimeInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x121\n\x07version\x18\x02 \x01(\x0b2 .containerd.types.RuntimeVersion\x12%\n\x07options\x18\x03 \x01(\x0b2\x14.google.protobuf.Any\x12&\n\x08features\x18\x04 \x01(\x0b2\x14.google.protobuf.Any\x12C\n\x0bannotations\x18\x05 \x03(\x0b2..containerd.types.RuntimeInfo.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.introspection_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_RUNTIMEINFO_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_RUNTIMEINFO_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_RUNTIMEREQUEST']._serialized_start = 85
    _globals['_RUNTIMEREQUEST']._serialized_end = 162
    _globals['_RUNTIMEVERSION']._serialized_start = 164
    _globals['_RUNTIMEVERSION']._serialized_end = 215
    _globals['_RUNTIMEINFO']._serialized_start = 218
    _globals['_RUNTIMEINFO']._serialized_end = 496
    _globals['_RUNTIMEINFO_ANNOTATIONSENTRY']._serialized_start = 446
    _globals['_RUNTIMEINFO_ANNOTATIONSENTRY']._serialized_end = 496