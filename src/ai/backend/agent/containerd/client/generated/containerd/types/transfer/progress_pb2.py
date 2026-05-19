"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/transfer/progress.proto')
_sym_db = _symbol_database.Default()
from ....containerd.types import descriptor_pb2 as containerd_dot_types_dot_descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(containerd/types/transfer/progress.proto\x12\x19containerd.types.transfer\x1a!containerd/types/descriptor.proto"\x85\x01\n\x08Progress\x12\r\n\x05event\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0f\n\x07parents\x18\x03 \x03(\t\x12\x10\n\x08progress\x18\x04 \x01(\x03\x12\r\n\x05total\x18\x05 \x01(\x03\x12*\n\x04desc\x18\x06 \x01(\x0b2\x1c.containerd.types.DescriptorB\x1bZ\x19containerd/types/transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.transfer.progress_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x19containerd/types/transfer'
    _globals['_PROGRESS']._serialized_start = 107
    _globals['_PROGRESS']._serialized_end = 240