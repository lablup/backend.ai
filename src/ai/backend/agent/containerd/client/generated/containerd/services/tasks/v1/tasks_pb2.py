"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/tasks/v1/tasks.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from .....containerd.types import metrics_pb2 as containerd_dot_types_dot_metrics__pb2
from .....containerd.types import descriptor_pb2 as containerd_dot_types_dot_descriptor__pb2
from .....containerd.types.task import task_pb2 as containerd_dot_types_dot_task_dot_task__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(containerd/services/tasks/v1/tasks.proto\x12\x1ccontainerd.services.tasks.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a\x19google/protobuf/any.proto\x1a\x1ccontainerd/types/mount.proto\x1a\x1econtainerd/types/metrics.proto\x1a!containerd/types/descriptor.proto\x1a containerd/types/task/task.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x82\x02\n\x11CreateTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\'\n\x06rootfs\x18\x03 \x03(\x0b2\x17.containerd.types.Mount\x12\r\n\x05stdin\x18\x04 \x01(\t\x12\x0e\n\x06stdout\x18\x05 \x01(\t\x12\x0e\n\x06stderr\x18\x06 \x01(\t\x12\x10\n\x08terminal\x18\x07 \x01(\x08\x120\n\ncheckpoint\x18\x08 \x01(\x0b2\x1c.containerd.types.Descriptor\x12%\n\x07options\x18\t \x01(\x0b2\x14.google.protobuf.Any\x12\x14\n\x0cruntime_path\x18\n \x01(\t"7\n\x12CreateTaskResponse\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r"5\n\x0cStartRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"\x1c\n\rStartResponse\x12\x0b\n\x03pid\x18\x01 \x01(\r")\n\x11DeleteTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"m\n\x0eDeleteResponse\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r\x12\x13\n\x0bexit_status\x18\x03 \x01(\r\x12-\n\texited_at\x18\x04 \x01(\x0b2\x1a.google.protobuf.Timestamp"=\n\x14DeleteProcessRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"3\n\nGetRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"<\n\x0bGetResponse\x12-\n\x07process\x18\x01 \x01(\x0b2\x1c.containerd.v1.types.Process""\n\x10ListTasksRequest\x12\x0e\n\x06filter\x18\x01 \x01(\t"@\n\x11ListTasksResponse\x12+\n\x05tasks\x18\x01 \x03(\x0b2\x1c.containerd.v1.types.Process"Q\n\x0bKillRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\x0e\n\x06signal\x18\x03 \x01(\r\x12\x0b\n\x03all\x18\x04 \x01(\x08"\xa0\x01\n\x12ExecProcessRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\r\n\x05stdin\x18\x02 \x01(\t\x12\x0e\n\x06stdout\x18\x03 \x01(\t\x12\x0e\n\x06stderr\x18\x04 \x01(\t\x12\x10\n\x08terminal\x18\x05 \x01(\x08\x12"\n\x04spec\x18\x06 \x01(\x0b2\x14.google.protobuf.Any\x12\x0f\n\x07exec_id\x18\x07 \x01(\t"\x15\n\x13ExecProcessResponse"X\n\x10ResizePtyRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\r\n\x05width\x18\x03 \x01(\r\x12\x0e\n\x06height\x18\x04 \x01(\r"F\n\x0eCloseIORequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t\x12\r\n\x05stdin\x18\x03 \x01(\x08"(\n\x10PauseTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t")\n\x11ResumeTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"\'\n\x0fListPidsRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t"G\n\x10ListPidsResponse\x123\n\tprocesses\x18\x01 \x03(\x0b2 .containerd.v1.types.ProcessInfo"o\n\x15CheckpointTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x19\n\x11parent_checkpoint\x18\x02 \x01(\t\x12%\n\x07options\x18\x03 \x01(\x0b2\x14.google.protobuf.Any"K\n\x16CheckpointTaskResponse\x121\n\x0bdescriptors\x18\x01 \x03(\x0b2\x1c.containerd.types.Descriptor"\xdd\x01\n\x11UpdateTaskRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\'\n\tresources\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x12U\n\x0bannotations\x18\x03 \x03(\x0b2@.containerd.services.tasks.v1.UpdateTaskRequest.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"!\n\x0eMetricsRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"<\n\x0fMetricsResponse\x12)\n\x07metrics\x18\x01 \x03(\x0b2\x18.containerd.types.Metric"4\n\x0bWaitRequest\x12\x14\n\x0ccontainer_id\x18\x01 \x01(\t\x12\x0f\n\x07exec_id\x18\x02 \x01(\t"R\n\x0cWaitResponse\x12\x13\n\x0bexit_status\x18\x01 \x01(\r\x12-\n\texited_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp2\xdc\x0c\n\x05Tasks\x12k\n\x06Create\x12/.containerd.services.tasks.v1.CreateTaskRequest\x1a0.containerd.services.tasks.v1.CreateTaskResponse\x12`\n\x05Start\x12*.containerd.services.tasks.v1.StartRequest\x1a+.containerd.services.tasks.v1.StartResponse\x12g\n\x06Delete\x12/.containerd.services.tasks.v1.DeleteTaskRequest\x1a,.containerd.services.tasks.v1.DeleteResponse\x12q\n\rDeleteProcess\x122.containerd.services.tasks.v1.DeleteProcessRequest\x1a,.containerd.services.tasks.v1.DeleteResponse\x12Z\n\x03Get\x12(.containerd.services.tasks.v1.GetRequest\x1a).containerd.services.tasks.v1.GetResponse\x12g\n\x04List\x12..containerd.services.tasks.v1.ListTasksRequest\x1a/.containerd.services.tasks.v1.ListTasksResponse\x12I\n\x04Kill\x12).containerd.services.tasks.v1.KillRequest\x1a\x16.google.protobuf.Empty\x12P\n\x04Exec\x120.containerd.services.tasks.v1.ExecProcessRequest\x1a\x16.google.protobuf.Empty\x12S\n\tResizePty\x12..containerd.services.tasks.v1.ResizePtyRequest\x1a\x16.google.protobuf.Empty\x12O\n\x07CloseIO\x12,.containerd.services.tasks.v1.CloseIORequest\x1a\x16.google.protobuf.Empty\x12O\n\x05Pause\x12..containerd.services.tasks.v1.PauseTaskRequest\x1a\x16.google.protobuf.Empty\x12Q\n\x06Resume\x12/.containerd.services.tasks.v1.ResumeTaskRequest\x1a\x16.google.protobuf.Empty\x12i\n\x08ListPids\x12-.containerd.services.tasks.v1.ListPidsRequest\x1a..containerd.services.tasks.v1.ListPidsResponse\x12w\n\nCheckpoint\x123.containerd.services.tasks.v1.CheckpointTaskRequest\x1a4.containerd.services.tasks.v1.CheckpointTaskResponse\x12Q\n\x06Update\x12/.containerd.services.tasks.v1.UpdateTaskRequest\x1a\x16.google.protobuf.Empty\x12f\n\x07Metrics\x12,.containerd.services.tasks.v1.MetricsRequest\x1a-.containerd.services.tasks.v1.MetricsResponse\x12]\n\x04Wait\x12).containerd.services.tasks.v1.WaitRequest\x1a*.containerd.services.tasks.v1.WaitResponseB$Z"containerd/services/tasks/v1;tasksb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.tasks.v1.tasks_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z"containerd/services/tasks/v1;tasks'
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_CREATETASKREQUEST']._serialized_start = 295
    _globals['_CREATETASKREQUEST']._serialized_end = 553
    _globals['_CREATETASKRESPONSE']._serialized_start = 555
    _globals['_CREATETASKRESPONSE']._serialized_end = 610
    _globals['_STARTREQUEST']._serialized_start = 612
    _globals['_STARTREQUEST']._serialized_end = 665
    _globals['_STARTRESPONSE']._serialized_start = 667
    _globals['_STARTRESPONSE']._serialized_end = 695
    _globals['_DELETETASKREQUEST']._serialized_start = 697
    _globals['_DELETETASKREQUEST']._serialized_end = 738
    _globals['_DELETERESPONSE']._serialized_start = 740
    _globals['_DELETERESPONSE']._serialized_end = 849
    _globals['_DELETEPROCESSREQUEST']._serialized_start = 851
    _globals['_DELETEPROCESSREQUEST']._serialized_end = 912
    _globals['_GETREQUEST']._serialized_start = 914
    _globals['_GETREQUEST']._serialized_end = 965
    _globals['_GETRESPONSE']._serialized_start = 967
    _globals['_GETRESPONSE']._serialized_end = 1027
    _globals['_LISTTASKSREQUEST']._serialized_start = 1029
    _globals['_LISTTASKSREQUEST']._serialized_end = 1063
    _globals['_LISTTASKSRESPONSE']._serialized_start = 1065
    _globals['_LISTTASKSRESPONSE']._serialized_end = 1129
    _globals['_KILLREQUEST']._serialized_start = 1131
    _globals['_KILLREQUEST']._serialized_end = 1212
    _globals['_EXECPROCESSREQUEST']._serialized_start = 1215
    _globals['_EXECPROCESSREQUEST']._serialized_end = 1375
    _globals['_EXECPROCESSRESPONSE']._serialized_start = 1377
    _globals['_EXECPROCESSRESPONSE']._serialized_end = 1398
    _globals['_RESIZEPTYREQUEST']._serialized_start = 1400
    _globals['_RESIZEPTYREQUEST']._serialized_end = 1488
    _globals['_CLOSEIOREQUEST']._serialized_start = 1490
    _globals['_CLOSEIOREQUEST']._serialized_end = 1560
    _globals['_PAUSETASKREQUEST']._serialized_start = 1562
    _globals['_PAUSETASKREQUEST']._serialized_end = 1602
    _globals['_RESUMETASKREQUEST']._serialized_start = 1604
    _globals['_RESUMETASKREQUEST']._serialized_end = 1645
    _globals['_LISTPIDSREQUEST']._serialized_start = 1647
    _globals['_LISTPIDSREQUEST']._serialized_end = 1686
    _globals['_LISTPIDSRESPONSE']._serialized_start = 1688
    _globals['_LISTPIDSRESPONSE']._serialized_end = 1759
    _globals['_CHECKPOINTTASKREQUEST']._serialized_start = 1761
    _globals['_CHECKPOINTTASKREQUEST']._serialized_end = 1872
    _globals['_CHECKPOINTTASKRESPONSE']._serialized_start = 1874
    _globals['_CHECKPOINTTASKRESPONSE']._serialized_end = 1949
    _globals['_UPDATETASKREQUEST']._serialized_start = 1952
    _globals['_UPDATETASKREQUEST']._serialized_end = 2173
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_start = 2123
    _globals['_UPDATETASKREQUEST_ANNOTATIONSENTRY']._serialized_end = 2173
    _globals['_METRICSREQUEST']._serialized_start = 2175
    _globals['_METRICSREQUEST']._serialized_end = 2208
    _globals['_METRICSRESPONSE']._serialized_start = 2210
    _globals['_METRICSRESPONSE']._serialized_end = 2270
    _globals['_WAITREQUEST']._serialized_start = 2272
    _globals['_WAITREQUEST']._serialized_end = 2324
    _globals['_WAITRESPONSE']._serialized_start = 2326
    _globals['_WAITRESPONSE']._serialized_end = 2408
    _globals['_TASKS']._serialized_start = 2411
    _globals['_TASKS']._serialized_end = 4039