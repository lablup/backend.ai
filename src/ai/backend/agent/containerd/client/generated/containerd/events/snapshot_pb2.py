"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/events/snapshot.proto')
_sym_db = _symbol_database.Default()
from ...containerd.types import fieldpath_pb2 as containerd_dot_types_dot_fieldpath__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n containerd/events/snapshot.proto\x12\x11containerd.events\x1a containerd/types/fieldpath.proto"C\n\x0fSnapshotPrepare\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0e\n\x06parent\x18\x02 \x01(\t\x12\x13\n\x0bsnapshotter\x18\x05 \x01(\t"@\n\x0eSnapshotCommit\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x13\n\x0bsnapshotter\x18\x05 \x01(\t"2\n\x0eSnapshotRemove\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x13\n\x0bsnapshotter\x18\x05 \x01(\tB\x1eZ\x18containerd/events;events\xa0\xf4\x1e\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.events.snapshot_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x18containerd/events;events\xa0\xf4\x1e\x01'
    _globals['_SNAPSHOTPREPARE']._serialized_start = 89
    _globals['_SNAPSHOTPREPARE']._serialized_end = 156
    _globals['_SNAPSHOTCOMMIT']._serialized_start = 158
    _globals['_SNAPSHOTCOMMIT']._serialized_end = 222
    _globals['_SNAPSHOTREMOVE']._serialized_start = 224
    _globals['_SNAPSHOTREMOVE']._serialized_end = 274