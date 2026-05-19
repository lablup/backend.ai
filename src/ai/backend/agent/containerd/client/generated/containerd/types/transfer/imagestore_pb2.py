"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/transfer/imagestore.proto')
_sym_db = _symbol_database.Default()
from ....containerd.types import platform_pb2 as containerd_dot_types_dot_platform__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*containerd/types/transfer/imagestore.proto\x12\x19containerd.types.transfer\x1a\x1fcontainerd/types/platform.proto"\xef\x02\n\nImageStore\x12\x0c\n\x04name\x18\x01 \x01(\t\x12A\n\x06labels\x18\x02 \x03(\x0b21.containerd.types.transfer.ImageStore.LabelsEntry\x12-\n\tplatforms\x18\x03 \x03(\x0b2\x1a.containerd.types.Platform\x12\x14\n\x0call_metadata\x18\x04 \x01(\x08\x12\x16\n\x0emanifest_limit\x18\x05 \x01(\r\x12C\n\x10extra_references\x18\x06 \x03(\x0b2).containerd.types.transfer.ImageReference\x12?\n\x07unpacks\x18\n \x03(\x0b2..containerd.types.transfer.UnpackConfiguration\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"X\n\x13UnpackConfiguration\x12,\n\x08platform\x18\x01 \x01(\x0b2\x1a.containerd.types.Platform\x12\x13\n\x0bsnapshotter\x18\x02 \x01(\t"y\n\x0eImageReference\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\tis_prefix\x18\x02 \x01(\x08\x12\x17\n\x0fallow_overwrite\x18\x03 \x01(\x08\x12\x12\n\nadd_digest\x18\x04 \x01(\x08\x12\x19\n\x11skip_named_digest\x18\x05 \x01(\x08B\x1bZ\x19containerd/types/transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.transfer.imagestore_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x19containerd/types/transfer'
    _globals['_IMAGESTORE_LABELSENTRY']._loaded_options = None
    _globals['_IMAGESTORE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_IMAGESTORE']._serialized_start = 107
    _globals['_IMAGESTORE']._serialized_end = 474
    _globals['_IMAGESTORE_LABELSENTRY']._serialized_start = 429
    _globals['_IMAGESTORE_LABELSENTRY']._serialized_end = 474
    _globals['_UNPACKCONFIGURATION']._serialized_start = 476
    _globals['_UNPACKCONFIGURATION']._serialized_end = 564
    _globals['_IMAGEREFERENCE']._serialized_start = 566
    _globals['_IMAGEREFERENCE']._serialized_end = 687