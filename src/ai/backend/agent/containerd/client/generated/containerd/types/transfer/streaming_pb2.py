"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/transfer/streaming.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n)containerd/types/transfer/streaming.proto\x12\x19containerd.types.transfer"\x14\n\x04Data\x12\x0c\n\x04data\x18\x01 \x01(\x0c"\x1e\n\x0cWindowUpdate\x12\x0e\n\x06update\x18\x01 \x01(\x05B\x1bZ\x19containerd/types/transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.transfer.streaming_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x19containerd/types/transfer'
    _globals['_DATA']._serialized_start = 72
    _globals['_DATA']._serialized_end = 92
    _globals['_WINDOWUPDATE']._serialized_start = 94
    _globals['_WINDOWUPDATE']._serialized_end = 124