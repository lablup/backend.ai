"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/events/v1/events.proto')
_sym_db = _symbol_database.Default()
from .....containerd.types import event_pb2 as containerd_dot_types_dot_event__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*containerd/services/events/v1/events.proto\x12\x1dcontainerd.services.events.v1\x1a\x1ccontainerd/types/event.proto\x1a\x19google/protobuf/any.proto\x1a\x1bgoogle/protobuf/empty.proto"D\n\x0ePublishRequest\x12\r\n\x05topic\x18\x01 \x01(\t\x12#\n\x05event\x18\x02 \x01(\x0b2\x14.google.protobuf.Any">\n\x0eForwardRequest\x12,\n\x08envelope\x18\x01 \x01(\x0b2\x1a.containerd.types.Envelope"#\n\x10SubscribeRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t2\x88\x02\n\x06Events\x12P\n\x07Publish\x12-.containerd.services.events.v1.PublishRequest\x1a\x16.google.protobuf.Empty\x12P\n\x07Forward\x12-.containerd.services.events.v1.ForwardRequest\x1a\x16.google.protobuf.Empty\x12Z\n\tSubscribe\x12/.containerd.services.events.v1.SubscribeRequest\x1a\x1a.containerd.types.Envelope0\x01B&Z$containerd/services/events/v1;eventsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.events.v1.events_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z$containerd/services/events/v1;events'
    _globals['_PUBLISHREQUEST']._serialized_start = 163
    _globals['_PUBLISHREQUEST']._serialized_end = 231
    _globals['_FORWARDREQUEST']._serialized_start = 233
    _globals['_FORWARDREQUEST']._serialized_end = 295
    _globals['_SUBSCRIBEREQUEST']._serialized_start = 297
    _globals['_SUBSCRIBEREQUEST']._serialized_end = 332
    _globals['_EVENTS']._serialized_start = 335
    _globals['_EVENTS']._serialized_end = 599