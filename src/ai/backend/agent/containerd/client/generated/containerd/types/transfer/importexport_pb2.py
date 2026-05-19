"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/transfer/importexport.proto')
_sym_db = _symbol_database.Default()
from ....containerd.types import platform_pb2 as containerd_dot_types_dot_platform__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,containerd/types/transfer/importexport.proto\x12\x19containerd.types.transfer\x1a\x1fcontainerd/types/platform.proto"O\n\x11ImageImportStream\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12\x12\n\nmedia_type\x18\x02 \x01(\t\x12\x16\n\x0eforce_compress\x18\x03 \x01(\x08"\xc2\x01\n\x11ImageExportStream\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12\x12\n\nmedia_type\x18\x02 \x01(\t\x12-\n\tplatforms\x18\x03 \x03(\x0b2\x1a.containerd.types.Platform\x12\x15\n\rall_platforms\x18\x04 \x01(\x08\x12#\n\x1bskip_compatibility_manifest\x18\x05 \x01(\x08\x12\x1e\n\x16skip_non_distributable\x18\x06 \x01(\x08B\x1bZ\x19containerd/types/transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.transfer.importexport_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x19containerd/types/transfer'
    _globals['_IMAGEIMPORTSTREAM']._serialized_start = 108
    _globals['_IMAGEIMPORTSTREAM']._serialized_end = 187
    _globals['_IMAGEEXPORTSTREAM']._serialized_start = 190
    _globals['_IMAGEEXPORTSTREAM']._serialized_end = 384