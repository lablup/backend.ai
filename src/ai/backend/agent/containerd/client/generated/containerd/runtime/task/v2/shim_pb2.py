"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/runtime/task/v2/shim.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from .....containerd.types.task import task_pb2 as containerd_dot_types_dot_task_dot_task__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n%containerd/runtime/task/v2/shim.proto\x12\x12containerd.task.v2\x1a\x19google/protobuf/any.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1ccontainerd/types/mount.proto\x1a containerd/types/task/task.proto"\xef\x01\n\x11CreateTaskRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0e\n\x06bundle\x18\x02 \x01(\t\x12\'\n\x06rootfs\x18\x03 \x03(\x0b2\x17.containerd.types.Mount\x12\x10\n\x08terminal\x18\x04 \x01(\x08\x12\r\n\x05stdin\x18\x05 \x01(\t\x12\x0e\n\x06stdout\x18\x06 \x01(\t\x12\x0e\n\x06stderr\x18\x07 \x01(\t\x12\x12\n\ncheckpoint\x18\x08 \x01(\t\x12\x19\n\x11parent_checkpoint\x18\t \x01(\t\x12%\n\x07options\x18\n \x01(\x0b2\x14.google.protobuf.Any"!\n\x12CreateTaskResponse\x12\x0b\n\x03pid\x18\x01 \x01(\r",\n\rDeleteRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"a\n\x0eDeleteResponse\x12\x0b\n\x03pid\x18\x01 \x01(\r\x12\x13\n\x0bexit_status\x18\x02 \x01(\r\x12-\n\texited_at\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp"\x96\x01\n\x12ExecProcessRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\x10\n\x08terminal\x18\x03 \x01(\x08\x12\r\n\x05stdin\x18\x04 \x01(\t\x12\x0e\n\x06stdout\x18\x05 \x01(\t\x12\x0e\n\x06stderr\x18\x06 \x01(\t\x12"\n\x04spec\x18\x07 \x01(\x0b2\x14.google.protobuf.Any"\x15\n\x13ExecProcessResponse"N\n\x10ResizePtyRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\r\n\x05width\x18\x03 \x01(\r\x12\x0e\n\x06height\x18\x04 \x01(\r"+\n\x0cStateRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"\xfb\x01\n\rStateResponse\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0e\n\x06bundle\x18\x02 \x01(\t\x12\x0b\n\x03pid\x18\x03 \x01(\r\x12+\n\x06status\x18\x04 \x01(\x0e2\x1b.containerd.v1.types.Status\x12\r\n\x05stdin\x18\x05 \x01(\t\x12\x0e\n\x06stdout\x18\x06 \x01(\t\x12\x0e\n\x06stderr\x18\x07 \x01(\t\x12\x10\n\x08terminal\x18\x08 \x01(\x08\x12\x13\n\x0bexit_status\x18\t \x01(\r\x12-\n\texited_at\x18\n \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\x0f\n\x07exec_id\x18\x0b \x01(\t"G\n\x0bKillRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\x0e\n\x06signal\x18\x03 \x01(\r\x12\x0b\n\x03all\x18\x04 \x01(\x08"<\n\x0eCloseIORequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\r\n\x05stdin\x18\x03 \x01(\x08"\x19\n\x0bPidsRequest\x12\n\n\x02id\x18\x01 \x01(\t"C\n\x0cPidsResponse\x123\n\tprocesses\x18\x01 \x03(\x0b2 .containerd.v1.types.ProcessInfo"X\n\x15CheckpointTaskRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04path\x18\x02 \x01(\t\x12%\n\x07options\x18\x03 \x01(\x0b2\x14.google.protobuf.Any"\xc9\x01\n\x11UpdateTaskRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\'\n\tresources\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x12K\n\x0bannotations\x18\x03 \x03(\x0b26.containerd.task.v2.UpdateTaskRequest.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"+\n\x0cStartRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"\x1c\n\rStartResponse\x12\x0b\n\x03pid\x18\x01 \x01(\r"*\n\x0bWaitRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"R\n\x0cWaitResponse\x12\x13\n\x0bexit_status\x18\x01 \x01(\r\x12-\n\texited_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp"\x1a\n\x0cStatsRequest\x12\n\n\x02id\x18\x01 \x01(\t"4\n\rStatsResponse\x12#\n\x05stats\x18\x01 \x01(\x0b2\x14.google.protobuf.Any"\x1c\n\x0eConnectRequest\x12\n\n\x02id\x18\x01 \x01(\t"F\n\x0fConnectResponse\x12\x10\n\x08shim_pid\x18\x01 \x01(\r\x12\x10\n\x08task_pid\x18\x02 \x01(\r\x12\x0f\n\x07version\x18\x03 \x01(\t"*\n\x0fShutdownRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0b\n\x03now\x18\x02 \x01(\x08"\x1a\n\x0cPauseRequest\x12\n\n\x02id\x18\x01 \x01(\t"\x1b\n\rResumeRequest\x12\n\n\x02id\x18\x01 \x01(\t2\x8a\n\n\x04Task\x12L\n\x05State\x12 .containerd.task.v2.StateRequest\x1a!.containerd.task.v2.StateResponse\x12W\n\x06Create\x12%.containerd.task.v2.CreateTaskRequest\x1a&.containerd.task.v2.CreateTaskResponse\x12L\n\x05Start\x12 .containerd.task.v2.StartRequest\x1a!.containerd.task.v2.StartResponse\x12O\n\x06Delete\x12!.containerd.task.v2.DeleteRequest\x1a".containerd.task.v2.DeleteResponse\x12I\n\x04Pids\x12\x1f.containerd.task.v2.PidsRequest\x1a .containerd.task.v2.PidsResponse\x12A\n\x05Pause\x12 .containerd.task.v2.PauseRequest\x1a\x16.google.protobuf.Empty\x12C\n\x06Resume\x12!.containerd.task.v2.ResumeRequest\x1a\x16.google.protobuf.Empty\x12O\n\nCheckpoint\x12).containerd.task.v2.CheckpointTaskRequest\x1a\x16.google.protobuf.Empty\x12?\n\x04Kill\x12\x1f.containerd.task.v2.KillRequest\x1a\x16.google.protobuf.Empty\x12F\n\x04Exec\x12&.containerd.task.v2.ExecProcessRequest\x1a\x16.google.protobuf.Empty\x12I\n\tResizePty\x12$.containerd.task.v2.ResizePtyRequest\x1a\x16.google.protobuf.Empty\x12E\n\x07CloseIO\x12".containerd.task.v2.CloseIORequest\x1a\x16.google.protobuf.Empty\x12G\n\x06Update\x12%.containerd.task.v2.UpdateTaskRequest\x1a\x16.google.protobuf.Empty\x12I\n\x04Wait\x12\x1f.containerd.task.v2.WaitRequest\x1a .containerd.task.v2.WaitResponse\x12L\n\x05Stats\x12 .containerd.task.v2.StatsRequest\x1a!.containerd.task.v2.StatsResponse\x12R\n\x07Connect\x12".containerd.task.v2.ConnectRequest\x1a#.containerd.task.v2.ConnectResponse\x12G\n\x08Shutdown\x12#.containerd.task.v2.ShutdownRequest\x1a\x16.google.protobuf.EmptyB!Z\x1fcontainerd/runtime/task/v2;taskb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.runtime.task.v2.shim_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x1fcontainerd/runtime/task/v2;task'
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_CREATETASKREQUEST']._serialized_start = 215
    _globals['_CREATETASKREQUEST']._serialized_end = 454
    _globals['_CREATETASKRESPONSE']._serialized_start = 456
    _globals['_CREATETASKRESPONSE']._serialized_end = 489
    _globals['_DELETEREQUEST']._serialized_start = 491
    _globals['_DELETEREQUEST']._serialized_end = 535
    _globals['_DELETERESPONSE']._serialized_start = 537
    _globals['_DELETERESPONSE']._serialized_end = 634
    _globals['_EXECPROCESSREQUEST']._serialized_start = 637
    _globals['_EXECPROCESSREQUEST']._serialized_end = 787
    _globals['_EXECPROCESSRESPONSE']._serialized_start = 789
    _globals['_EXECPROCESSRESPONSE']._serialized_end = 810
    _globals['_RESIZEPTYREQUEST']._serialized_start = 812
    _globals['_RESIZEPTYREQUEST']._serialized_end = 890
    _globals['_STATEREQUEST']._serialized_start = 892
    _globals['_STATEREQUEST']._serialized_end = 935
    _globals['_STATERESPONSE']._serialized_start = 938
    _globals['_STATERESPONSE']._serialized_end = 1189
    _globals['_KILLREQUEST']._serialized_start = 1191
    _globals['_KILLREQUEST']._serialized_end = 1262
    _globals['_CLOSEIOREQUEST']._serialized_start = 1264
    _globals['_CLOSEIOREQUEST']._serialized_end = 1324
    _globals['_PIDSREQUEST']._serialized_start = 1326
    _globals['_PIDSREQUEST']._serialized_end = 1351
    _globals['_PIDSRESPONSE']._serialized_start = 1353
    _globals['_PIDSRESPONSE']._serialized_end = 1420
    _globals['_CHECKPOINTTASKREQUEST']._serialized_start = 1422
    _globals['_CHECKPOINTTASKREQUEST']._serialized_end = 1510
    _globals['_UPDATETASKREQUEST']._serialized_start = 1513
    _globals['_UPDATETASKREQUEST']._serialized_end = 1714
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_start = 1664
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_end = 1714
    _globals['_STARTREQUEST']._serialized_start = 1716
    _globals['_STARTREQUEST']._serialized_end = 1759
    _globals['_STARTRESPONSE']._serialized_start = 1761
    _globals['_STARTRESPONSE']._serialized_end = 1789
    _globals['_WAITREQUEST']._serialized_start = 1791
    _globals['_WAITREQUEST']._serialized_end = 1833
    _globals['_WAITRESPONSE']._serialized_start = 1835
    _globals['_WAITRESPONSE']._serialized_end = 1917
    _globals['_STATSREQUEST']._serialized_start = 1919
    _globals['_STATSREQUEST']._serialized_end = 1945
    _globals['_STATSRESPONSE']._serialized_start = 1947
    _globals['_STATSRESPONSE']._serialized_end = 1999
    _globals['_CONNECTREQUEST']._serialized_start = 2001
    _globals['_CONNECTREQUEST']._serialized_end = 2029
    _globals['_CONNECTRESPONSE']._serialized_start = 2031
    _globals['_CONNECTRESPONSE']._serialized_end = 2101
    _globals['_SHUTDOWNREQUEST']._serialized_start = 2103
    _globals['_SHUTDOWNREQUEST']._serialized_end = 2145
    _globals['_PAUSEREQUEST']._serialized_start = 2147
    _globals['_PAUSEREQUEST']._serialized_end = 2173
    _globals['_RESUMEREQUEST']._serialized_start = 2175
    _globals['_RESUMEREQUEST']._serialized_end = 2202
    _globals['_TASK']._serialized_start = 2205
    _globals['_TASK']._serialized_end = 3495