"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/ttrpc/events/v1/events.proto')
_sym_db = _symbol_database.Default()
from ......containerd.types import event_pb2 as containerd_dot_types_dot_event__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n0containerd/services/ttrpc/events/v1/events.proto\x12#containerd.services.events.ttrpc.v1\x1a\x1ccontainerd/types/event.proto\x1a\x1bgoogle/protobuf/empty.proto">\n\x0eForwardRequest\x12,\n\x08envelope\x18\x01 \x01(\x0b2\x1a.containerd.types.Envelope2`\n\x06Events\x12V\n\x07Forward\x123.containerd.services.events.ttrpc.v1.ForwardRequest\x1a\x16.google.protobuf.EmptyB,Z*containerd/services/ttrpc/events/v1;eventsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.ttrpc.events.v1.events_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z*containerd/services/ttrpc/events/v1;events'
    _globals['_FORWARDREQUEST']._serialized_start = 148
    _globals['_FORWARDREQUEST']._serialized_end = 210
    _globals['_EVENTS']._serialized_start = 212
    _globals['_EVENTS']._serialized_end = 308