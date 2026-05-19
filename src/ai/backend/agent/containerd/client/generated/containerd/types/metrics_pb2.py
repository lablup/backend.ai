"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/metrics.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1econtainerd/types/metrics.proto\x12\x10containerd.types\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto"g\n\x06Metric\x12-\n\ttimestamp\x18\x01 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\n\n\x02id\x18\x02 \x01(\t\x12"\n\x04data\x18\x03 \x01(\x0b2\x14.google.protobuf.AnyB\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.metrics_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_METRIC']._serialized_start = 112
    _globals['_METRIC']._serialized_end = 215