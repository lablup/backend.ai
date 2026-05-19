"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/mount.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1ccontainerd/types/mount.proto\x12\x10containerd.types\x1a\x1fgoogle/protobuf/timestamp.proto"F\n\x05Mount\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x0e\n\x06source\x18\x02 \x01(\t\x12\x0e\n\x06target\x18\x03 \x01(\t\x12\x0f\n\x07options\x18\x04 \x03(\t"\xde\x01\n\x0bActiveMount\x12&\n\x05mount\x18\x01 \x01(\x0b2\x17.containerd.types.Mount\x12.\n\nmounted_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\x13\n\x0bmount_point\x18\x03 \x01(\t\x125\n\x04data\x18\x04 \x03(\x0b2\'.containerd.types.ActiveMount.DataEntry\x1a+\n\tDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\xe3\x01\n\x0eActivationInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12-\n\x06active\x18\x02 \x03(\x0b2\x1d.containerd.types.ActiveMount\x12\'\n\x06system\x18\x03 \x03(\x0b2\x17.containerd.types.Mount\x12<\n\x06labels\x18\x04 \x03(\x0b2,.containerd.types.ActivationInfo.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01B\x18Z\x16containerd/types;typesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.mount_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x16containerd/types;types'
    _globals['_ACTIVEMOUNT_DATAENTRY']._loaded_options = None
    _globals['_ACTIVEMOUNT_DATAENTRY']._serialized_options = b'8\x01'
    _globals['_ACTIVATIONINFO_LABELSENTRY']._loaded_options = None
    _globals['_ACTIVATIONINFO_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_MOUNT']._serialized_start = 83
    _globals['_MOUNT']._serialized_end = 153
    _globals['_ACTIVEMOUNT']._serialized_start = 156
    _globals['_ACTIVEMOUNT']._serialized_end = 378
    _globals['_ACTIVEMOUNT_DATAENTRY']._serialized_start = 335
    _globals['_ACTIVEMOUNT_DATAENTRY']._serialized_end = 378
    _globals['_ACTIVATIONINFO']._serialized_start = 381
    _globals['_ACTIVATIONINFO']._serialized_end = 608
    _globals['_ACTIVATIONINFO_LABELSENTRY']._serialized_start = 563
    _globals['_ACTIVATIONINFO_LABELSENTRY']._serialized_end = 608