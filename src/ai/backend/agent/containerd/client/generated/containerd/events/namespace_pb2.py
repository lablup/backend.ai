"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/events/namespace.proto')
_sym_db = _symbol_database.Default()
from ...containerd.types import fieldpath_pb2 as containerd_dot_types_dot_fieldpath__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!containerd/events/namespace.proto\x12\x11containerd.events\x1a containerd/types/fieldpath.proto"\x8e\x01\n\x0fNamespaceCreate\x12\x0c\n\x04name\x18\x01 \x01(\t\x12>\n\x06labels\x18\x02 \x03(\x0b2..containerd.events.NamespaceCreate.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x8e\x01\n\x0fNamespaceUpdate\x12\x0c\n\x04name\x18\x01 \x01(\t\x12>\n\x06labels\x18\x02 \x03(\x0b2..containerd.events.NamespaceUpdate.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x1f\n\x0fNamespaceDelete\x12\x0c\n\x04name\x18\x01 \x01(\tB\x1eZ\x18containerd/events;events\xa0\xf4\x1e\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.events.namespace_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x18containerd/events;events\xa0\xf4\x1e\x01'
    _globals['_NAMESPACECREATE_LABELSENTRY']._loaded_options = None
    _globals['_NAMESPACECREATE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_NAMESPACEUPDATE_LABELSENTRY']._loaded_options = None
    _globals['_NAMESPACEUPDATE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_NAMESPACECREATE']._serialized_start = 91
    _globals['_NAMESPACECREATE']._serialized_end = 233
    _globals['_NAMESPACECREATE_LABELSENTRY']._serialized_start = 188
    _globals['_NAMESPACECREATE_LABELSENTRY']._serialized_end = 233
    _globals['_NAMESPACEUPDATE']._serialized_start = 236
    _globals['_NAMESPACEUPDATE']._serialized_end = 378
    _globals['_NAMESPACEUPDATE_LABELSENTRY']._serialized_start = 188
    _globals['_NAMESPACEUPDATE_LABELSENTRY']._serialized_end = 233
    _globals['_NAMESPACEDELETE']._serialized_start = 380
    _globals['_NAMESPACEDELETE']._serialized_end = 411