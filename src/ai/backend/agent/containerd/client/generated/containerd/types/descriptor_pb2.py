"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/descriptor.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n!containerd/types/descriptor.proto\x12\x10containerd.types"\xb6\x01\n\nDescriptor\x12\x12\n\nmedia_type\x18\x01 \x01(\t\x12\x0e\n\x06digest\x18\x02 \x01(\t\x12\x0c\n\x04size\x18\x03 \x01(\x03\x12B\n\x0bannotations\x18\x05 \x03(\x0b2-.containerd.types.Descriptor.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.descriptor_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_DESCRIPTOR_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_DESCRIPTOR_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_DESCRIPTOR']._serialized_start = 56
    _globals['_DESCRIPTOR']._serialized_end = 238
    _globals['_DESCRIPTOR_ANNOTATIONSENTRY']._serialized_start = 188
    _globals['_DESCRIPTOR_ANNOTATIONSENTRY']._serialized_end = 238