"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/runc/options/oci.proto')
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\'containerd/types/runc/options/oci.proto\x12\x12containerd.runc.v1"\x93\x02\n\x07Options\x12\x15\n\rno_pivot_root\x18\x01 \x01(\x08\x12\x16\n\x0eno_new_keyring\x18\x02 \x01(\x08\x12\x13\n\x0bshim_cgroup\x18\x03 \x01(\t\x12\x0e\n\x06io_uid\x18\x04 \x01(\r\x12\x0e\n\x06io_gid\x18\x05 \x01(\r\x12\x13\n\x0bbinary_name\x18\x06 \x01(\t\x12\x0c\n\x04root\x18\x07 \x01(\t\x12\x16\n\x0esystemd_cgroup\x18\t \x01(\x08\x12\x17\n\x0fcriu_image_path\x18\n \x01(\t\x12\x16\n\x0ecriu_work_path\x18\x0b \x01(\t\x12\x18\n\x10task_api_address\x18\x0c \x01(\t\x12\x18\n\x10task_api_version\x18\r \x01(\rJ\x04\x08\x08\x10\t"\xcf\x01\n\x11CheckpointOptions\x12\x0c\n\x04exit\x18\x01 \x01(\x08\x12\x10\n\x08open_tcp\x18\x02 \x01(\x08\x12\x1d\n\x15external_unix_sockets\x18\x03 \x01(\x08\x12\x10\n\x08terminal\x18\x04 \x01(\x08\x12\x12\n\nfile_locks\x18\x05 \x01(\x08\x12\x18\n\x10empty_namespaces\x18\x06 \x03(\t\x12\x14\n\x0ccgroups_mode\x18\x07 \x01(\t\x12\x12\n\nimage_path\x18\x08 \x01(\t\x12\x11\n\twork_path\x18\t \x01(\t"!\n\x0eProcessDetails\x12\x0f\n\x07exec_id\x18\x01 \x01(\tB\'Z%containerd/types/runc/options;optionsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.runc.options.oci_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z%containerd/types/runc/options;options'
    _globals['_OPTIONS']._serialized_start = 64
    _globals['_OPTIONS']._serialized_end = 339
    _globals['_CHECKPOINTOPTIONS']._serialized_start = 342
    _globals['_CHECKPOINTOPTIONS']._serialized_end = 549
    _globals['_PROCESSDETAILS']._serialized_start = 551
    _globals['_PROCESSDETAILS']._serialized_end = 584