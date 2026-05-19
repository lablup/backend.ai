"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/events/sandbox.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1fcontainerd/events/sandbox.proto\x12\x11containerd.events\x1a\x1fgoogle/protobuf/timestamp.proto"#\n\rSandboxCreate\x12\x12\n\nsandbox_id\x18\x01 \x01(\t""\n\x0cSandboxStart\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"e\n\x0bSandboxExit\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x13\n\x0bexit_status\x18\x02 \x01(\r\x12-\n\texited_at\x18\x03 \x01(\x0b2\x1a.google.protobuf.TimestampB\x1aZ\x18containerd/events;eventsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.events.sandbox_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x18containerd/events;events'
    _globals['_SANDBOXCREATE']._serialized_start = 87
    _globals['_SANDBOXCREATE']._serialized_end = 122
    _globals['_SANDBOXSTART']._serialized_start = 124
    _globals['_SANDBOXSTART']._serialized_end = 158
    _globals['_SANDBOXEXIT']._serialized_start = 160
    _globals['_SANDBOXEXIT']._serialized_end = 261