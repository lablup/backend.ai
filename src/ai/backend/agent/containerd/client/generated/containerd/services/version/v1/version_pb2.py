"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/version/v1/version.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,containerd/services/version/v1/version.proto\x12\x1econtainerd.services.version.v1\x1a\x1bgoogle/protobuf/empty.proto"4\n\x0fVersionResponse\x12\x0f\n\x07version\x18\x01 \x01(\t\x12\x10\n\x08revision\x18\x02 \x01(\t2]\n\x07Version\x12R\n\x07Version\x12\x16.google.protobuf.Empty\x1a/.containerd.services.version.v1.VersionResponseB(Z&containerd/services/version/v1;versionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.version.v1.version_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z&containerd/services/version/v1;version'
    _globals['_VERSIONRESPONSE']._serialized_start = 109
    _globals['_VERSIONRESPONSE']._serialized_end = 161
    _globals['_VERSION']._serialized_start = 163
    _globals['_VERSION']._serialized_end = 256