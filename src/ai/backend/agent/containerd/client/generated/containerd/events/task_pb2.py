"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/events/task.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from ...containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from ...containerd.types import fieldpath_pb2 as containerd_dot_types_dot_fieldpath__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x1ccontainerd/events/task.proto\x12\x11containerd.events\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1ccontainerd/types/mount.proto\x1a containerd/types/fieldpath.proto"\xa3\x01\n\nTaskCreate\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0e\n\x06bundle\x18\x02 \x01(\t\x12\'\n\x06rootfs\x18\x03 \x03(\x0b2\x17.containerd.types.Mount\x12%\n\x02io\x18\x04 \x01(\x0b2\x19.containerd.events.TaskIO\x12\x12\n\ncheckpoint\x18\x05 \x01(\t\x12\x0b\n\x03pid\x18\x06 \x01(\r".\n\tTaskStart\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r"\x7f\n\nTaskDelete\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r\x12\x13\n\x0bexit_status\x18\x03 \x01(\r\x12-\n\texited_at\x18\x04 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\n\n\x02id\x18\x05 \x01(\t"I\n\x06TaskIO\x12\r\n\x05stdin\x18\x01 \x01(\t\x12\x0e\n\x06stdout\x18\x02 \x01(\t\x12\x0e\n\x06stderr\x18\x03 \x01(\t\x12\x10\n\x08terminal\x18\x04 \x01(\x08"}\n\x08TaskExit\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\t\x12\x0b\n\x03pid\x18\x03 \x01(\r\x12\x13\n\x0bexit_status\x18\x04 \x01(\r\x12-\n\texited_at\x18\x05 \x01(\x0b2\x1a.google.protobuf.Timestamp"\x1f\n\x07TaskOOM\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"6\n\rTaskExecAdded\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"E\n\x0fTaskExecStarted\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\x0b\n\x03pid\x18\x03 \x01(\r""\n\nTaskPaused\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"#\n\x0bTaskResumed\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"<\n\x10TaskCheckpointed\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x12\n\ncheckpoint\x18\x02 \x01(\tB\x1eZ\x18containerd/events;events\xa0\xf4\x1e\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.events.task_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x18containerd/events;events\xa0\xf4\x1e\x01'
    _globals['_TASKCREATE']._serialized_start = 149
    _globals['_TASKCREATE']._serialized_end = 312
    _globals['_TASKSTART']._serialized_start = 314
    _globals['_TASKSTART']._serialized_end = 360
    _globals['_TASKDELETE']._serialized_start = 362
    _globals['_TASKDELETE']._serialized_end = 489
    _globals['_TASKIO']._serialized_start = 491
    _globals['_TASKIO']._serialized_end = 564
    _globals['_TASKEXIT']._serialized_start = 566
    _globals['_TASKEXIT']._serialized_end = 691
    _globals['_TASKOOM']._serialized_start = 693
    _globals['_TASKOOM']._serialized_end = 724
    _globals['_TASKEXECADDED']._serialized_start = 726
    _globals['_TASKEXECADDED']._serialized_end = 780
    _globals['_TASKEXECSTARTED']._serialized_start = 782
    _globals['_TASKEXECSTARTED']._serialized_end = 851
    _globals['_TASKPAUSED']._serialized_start = 853
    _globals['_TASKPAUSED']._serialized_end = 887
    _globals['_TASKRESUMED']._serialized_start = 889
    _globals['_TASKRESUMED']._serialized_end = 924
    _globals['_TASKCHECKPOINTED']._serialized_start = 926
    _globals['_TASKCHECKPOINTED']._serialized_end = 986