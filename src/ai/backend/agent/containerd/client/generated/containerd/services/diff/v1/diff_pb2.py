"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/diff/v1/diff.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from .....containerd.types import descriptor_pb2 as containerd_dot_types_dot_descriptor__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n&containerd/services/diff/v1/diff.proto\x12\x1bcontainerd.services.diff.v1\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1ccontainerd/types/mount.proto\x1a!containerd/types/descriptor.proto"\x86\x02\n\x0cApplyRequest\x12*\n\x04diff\x18\x01 \x01(\x0b2\x1c.containerd.types.Descriptor\x12\'\n\x06mounts\x18\x02 \x03(\x0b2\x17.containerd.types.Mount\x12I\n\x08payloads\x18\x03 \x03(\x0b27.containerd.services.diff.v1.ApplyRequest.PayloadsEntry\x12\x0f\n\x07sync_fs\x18\x04 \x01(\x08\x1aE\n\rPayloadsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b2\x14.google.protobuf.Any:\x028\x01">\n\rApplyResponse\x12-\n\x07applied\x18\x01 \x01(\x0b2\x1c.containerd.types.Descriptor"\xa9\x02\n\x0bDiffRequest\x12%\n\x04left\x18\x01 \x03(\x0b2\x17.containerd.types.Mount\x12&\n\x05right\x18\x02 \x03(\x0b2\x17.containerd.types.Mount\x12\x12\n\nmedia_type\x18\x03 \x01(\t\x12\x0b\n\x03ref\x18\x04 \x01(\t\x12D\n\x06labels\x18\x05 \x03(\x0b24.containerd.services.diff.v1.DiffRequest.LabelsEntry\x125\n\x11source_date_epoch\x18\x06 \x01(\x0b2\x1a.google.protobuf.Timestamp\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01":\n\x0cDiffResponse\x12*\n\x04diff\x18\x03 \x01(\x0b2\x1c.containerd.types.Descriptor2\xc3\x01\n\x04Diff\x12^\n\x05Apply\x12).containerd.services.diff.v1.ApplyRequest\x1a*.containerd.services.diff.v1.ApplyResponse\x12[\n\x04Diff\x12(.containerd.services.diff.v1.DiffRequest\x1a).containerd.services.diff.v1.DiffResponseB"Z containerd/services/diff/v1;diffb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.diff.v1.diff_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z containerd/services/diff/v1;diff'
    _globals['_APPLYREQUEST_PAYLOADSENTRY']._loaded_options = None
    _globals['_APPLYREQUEST_PAYLOADSENTRY']._serialized_options = b'8\x01'
    _globals['_DIFFREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_DIFFREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_APPLYREQUEST']._serialized_start = 197
    _globals['_APPLYREQUEST']._serialized_end = 459
    _globals['_APPLYREQUEST_PAYLOADSENTRY']._serialized_start = 390
    _globals['_APPLYREQUEST_PAYLOADSENTRY']._serialized_end = 459
    _globals['_APPLYRESPONSE']._serialized_start = 461
    _globals['_APPLYRESPONSE']._serialized_end = 523
    _globals['_DIFFREQUEST']._serialized_start = 526
    _globals['_DIFFREQUEST']._serialized_end = 823
    _globals['_DIFFREQUEST_LABELSENTRY']._serialized_start = 778
    _globals['_DIFFREQUEST_LABELSENTRY']._serialized_end = 823
    _globals['_DIFFRESPONSE']._serialized_start = 825
    _globals['_DIFFRESPONSE']._serialized_end = 883
    _globals['_DIFF']._serialized_start = 886
    _globals['_DIFF']._serialized_end = 1081