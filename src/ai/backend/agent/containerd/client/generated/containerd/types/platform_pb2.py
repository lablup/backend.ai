"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/platform.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fcontainerd/types/platform.proto\x12\x10containerd.types"Q\n\x08Platform\x12\n\n\x02os\x18\x01 \x01(\t\x12\x14\n\x0carchitecture\x18\x02 \x01(\t\x12\x0f\n\x07variant\x18\x03 \x01(\t\x12\x12\n\nos_version\x18\x04 \x01(\tB\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.platform_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_PLATFORM']._serialized_start = 53
    _globals['_PLATFORM']._serialized_end = 134