"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/runtimeoptions/v1/api.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,containerd/types/runtimeoptions/v1/api.proto\x12\x11runtimeoptions.v1"E\n\x07Options\x12\x10\n\x08type_url\x18\x01 \x01(\t\x12\x13\n\x0bconfig_path\x18\x02 \x01(\t\x12\x13\n\x0bconfig_body\x18\x03 \x01(\x0cB3Z1containerd/types/runtimeoptions/v1;runtimeoptionsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.runtimeoptions.v1.api_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z1containerd/types/runtimeoptions/v1;runtimeoptions'
    _globals['_OPTIONS']._serialized_start = 67
    _globals['_OPTIONS']._serialized_end = 136