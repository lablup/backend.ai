"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/task/task.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n containerd/types/task/task.proto\x12\x13containerd.v1.types\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x19google/protobuf/any.proto"\xea\x01\n\x07Process\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\t\x12\x0b\n\x03pid\x18\x03 \x01(\r\x12+\n\x06status\x18\x04 \x01(\x0e2\x1b.containerd.v1.types.Status\x12\r\n\x05stdin\x18\x05 \x01(\t\x12\x0e\n\x06stdout\x18\x06 \x01(\t\x12\x0e\n\x06stderr\x18\x07 \x01(\t\x12\x10\n\x08terminal\x18\x08 \x01(\x08\x12\x13\n\x0bexit_status\x18\t \x01(\r\x12-\n\texited_at\x18\n \x01(\x0b2\x1a.google.protobuf.Timestamp">\n\x0bProcessInfo\x12\x0b\n\x03pid\x18\x01 \x01(\r\x12"\n\x04info\x18\x02 \x01(\x0b2\x14.google.protobuf.Any*U\n\x06Status\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x0b\n\x07CREATED\x10\x01\x12\x0b\n\x07RUNNING\x10\x02\x12\x0b\n\x07STOPPED\x10\x03\x12\n\n\x06PAUSED\x10\x04\x12\x0b\n\x07PAUSING\x10\x05B\x17Z\x15containerd/types/taskb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.task.task_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x15containerd/types/task'
    _globals['_STATUS']._serialized_start = 418
    _globals['_STATUS']._serialized_end = 503
    _globals['_PROCESS']._serialized_start = 118
    _globals['_PROCESS']._serialized_end = 352
    _globals['_PROCESSINFO']._serialized_start = 354
    _globals['_PROCESSINFO']._serialized_end = 416