"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/mounts/v1/mounts.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*containerd/services/mounts/v1/mounts.proto\x12\x1dcontainerd.services.mounts.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a google/protobuf/field_mask.proto\x1a\x1ccontainerd/types/mount.proto"\xd6\x01\n\x0fActivateRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\'\n\x06mounts\x18\x02 \x03(\x0b2\x17.containerd.types.Mount\x12J\n\x06labels\x18\x03 \x03(\x0b2:.containerd.services.mounts.v1.ActivateRequest.LabelsEntry\x12\x11\n\ttemporary\x18\x04 \x01(\x08\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"B\n\x10ActivateResponse\x12.\n\x04info\x18\x01 \x01(\x0b2 .containerd.types.ActivationInfo"!\n\x11DeactivateRequest\x12\x0c\n\x04name\x18\x01 \x01(\t"\x1b\n\x0bInfoRequest\x12\x0c\n\x04name\x18\x01 \x01(\t">\n\x0cInfoResponse\x12.\n\x04info\x18\x01 \x01(\x0b2 .containerd.types.ActivationInfo"p\n\rUpdateRequest\x12.\n\x04info\x18\x01 \x01(\x0b2 .containerd.types.ActivationInfo\x12/\n\x0bupdate_mask\x18\x02 \x01(\x0b2\x1a.google.protobuf.FieldMask"@\n\x0eUpdateResponse\x12.\n\x04info\x18\x01 \x01(\x0b2 .containerd.types.ActivationInfo"\x1e\n\x0bListRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"=\n\x0bListMessage\x12.\n\x04info\x18\x01 \x01(\x0b2 .containerd.types.ActivationInfo2\xf7\x03\n\x06Mounts\x12k\n\x08Activate\x12..containerd.services.mounts.v1.ActivateRequest\x1a/.containerd.services.mounts.v1.ActivateResponse\x12V\n\nDeactivate\x120.containerd.services.mounts.v1.DeactivateRequest\x1a\x16.google.protobuf.Empty\x12_\n\x04Info\x12*.containerd.services.mounts.v1.InfoRequest\x1a+.containerd.services.mounts.v1.InfoResponse\x12e\n\x06Update\x12,.containerd.services.mounts.v1.UpdateRequest\x1a-.containerd.services.mounts.v1.UpdateResponse\x12`\n\x04List\x12*.containerd.services.mounts.v1.ListRequest\x1a*.containerd.services.mounts.v1.ListMessage0\x01B&Z$containerd/services/mounts/v1;mountsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.mounts.v1.mounts_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z$containerd/services/mounts/v1;mounts'
    _globals['_ACTIVATEREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_ACTIVATEREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_ACTIVATEREQUEST']._serialized_start = 171
    _globals['_ACTIVATEREQUEST']._serialized_end = 385
    _globals['_ACTIVATEREQUEST_LABELSENTRY']._serialized_start = 340
    _globals['_ACTIVATEREQUEST_LABELSENTRY']._serialized_end = 385
    _globals['_ACTIVATERESPONSE']._serialized_start = 387
    _globals['_ACTIVATERESPONSE']._serialized_end = 453
    _globals['_DEACTIVATEREQUEST']._serialized_start = 455
    _globals['_DEACTIVATEREQUEST']._serialized_end = 488
    _globals['_INFOREQUEST']._serialized_start = 490
    _globals['_INFOREQUEST']._serialized_end = 517
    _globals['_INFORESPONSE']._serialized_start = 519
    _globals['_INFORESPONSE']._serialized_end = 581
    _globals['_UPDATEREQUEST']._serialized_start = 583
    _globals['_UPDATEREQUEST']._serialized_end = 695
    _globals['_UPDATERESPONSE']._serialized_start = 697
    _globals['_UPDATERESPONSE']._serialized_end = 761
    _globals['_LISTREQUEST']._serialized_start = 763
    _globals['_LISTREQUEST']._serialized_end = 793
    _globals['_LISTMESSAGE']._serialized_start = 795
    _globals['_LISTMESSAGE']._serialized_end = 856
    _globals['_MOUNTS']._serialized_start = 859
    _globals['_MOUNTS']._serialized_end = 1362