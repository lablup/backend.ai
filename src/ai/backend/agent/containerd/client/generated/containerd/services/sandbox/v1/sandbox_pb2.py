"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/sandbox/v1/sandbox.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import sandbox_pb2 as containerd_dot_types_dot_sandbox__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from .....containerd.types import platform_pb2 as containerd_dot_types_dot_platform__pb2
from .....containerd.types import metrics_pb2 as containerd_dot_types_dot_metrics__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,containerd/services/sandbox/v1/sandbox.proto\x12\x1econtainerd.services.sandbox.v1\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1econtainerd/types/sandbox.proto\x1a\x1ccontainerd/types/mount.proto\x1a\x1fcontainerd/types/platform.proto\x1a\x1econtainerd/types/metrics.proto"@\n\x12StoreCreateRequest\x12*\n\x07sandbox\x18\x01 \x01(\x0b2\x19.containerd.types.Sandbox"A\n\x13StoreCreateResponse\x12*\n\x07sandbox\x18\x01 \x01(\x0b2\x19.containerd.types.Sandbox"P\n\x12StoreUpdateRequest\x12*\n\x07sandbox\x18\x01 \x01(\x0b2\x19.containerd.types.Sandbox\x12\x0e\n\x06fields\x18\x02 \x03(\t"A\n\x13StoreUpdateResponse\x12*\n\x07sandbox\x18\x01 \x01(\x0b2\x19.containerd.types.Sandbox"(\n\x12StoreDeleteRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"\x15\n\x13StoreDeleteResponse"#\n\x10StoreListRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"<\n\x11StoreListResponse\x12\'\n\x04list\x18\x01 \x03(\x0b2\x19.containerd.types.Sandbox"%\n\x0fStoreGetRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t">\n\x10StoreGetResponse\x12*\n\x07sandbox\x18\x01 \x01(\x0b2\x19.containerd.types.Sandbox"\xe3\x02\n\x17ControllerCreateRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\'\n\x06rootfs\x18\x02 \x03(\x0b2\x17.containerd.types.Mount\x12%\n\x07options\x18\x03 \x01(\x0b2\x14.google.protobuf.Any\x12\x12\n\nnetns_path\x18\x04 \x01(\t\x12]\n\x0bannotations\x18\x05 \x03(\x0b2H.containerd.services.sandbox.v1.ControllerCreateRequest.AnnotationsEntry\x12*\n\x07sandbox\x18\x06 \x01(\x0b2\x19.containerd.types.Sandbox\x12\x11\n\tsandboxer\x18\n \x01(\t\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01".\n\x18ControllerCreateResponse\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"?\n\x16ControllerStartRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\n \x01(\t"\x90\x02\n\x17ControllerStartResponse\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r\x12.\n\ncreated_at\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12S\n\x06labels\x18\x04 \x03(\x0b2C.containerd.services.sandbox.v1.ControllerStartResponse.LabelsEntry\x12\x0f\n\x07address\x18\x05 \x01(\t\x12\x0f\n\x07version\x18\x06 \x01(\r\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"B\n\x19ControllerPlatformRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\n \x01(\t"J\n\x1aControllerPlatformResponse\x12,\n\x08platform\x18\x01 \x01(\x0b2\x1a.containerd.types.Platform"T\n\x15ControllerStopRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x14\n\x0ctimeout_secs\x18\x02 \x01(\r\x12\x11\n\tsandboxer\x18\n \x01(\t"\x18\n\x16ControllerStopResponse">\n\x15ControllerWaitRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\n \x01(\t"\\\n\x16ControllerWaitResponse\x12\x13\n\x0bexit_status\x18\x01 \x01(\r\x12-\n\texited_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp"Q\n\x17ControllerStatusRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x0f\n\x07verbose\x18\x02 \x01(\x08\x12\x11\n\tsandboxer\x18\n \x01(\t"\xef\x02\n\x18ControllerStatusResponse\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r\x12\r\n\x05state\x18\x03 \x01(\t\x12P\n\x04info\x18\x04 \x03(\x0b2B.containerd.services.sandbox.v1.ControllerStatusResponse.InfoEntry\x12.\n\ncreated_at\x18\x05 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12-\n\texited_at\x18\x06 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12#\n\x05extra\x18\x07 \x01(\x0b2\x14.google.protobuf.Any\x12\x0f\n\x07address\x18\x08 \x01(\t\x12\x0f\n\x07version\x18\t \x01(\r\x1a+\n\tInfoEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"B\n\x19ControllerShutdownRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\n \x01(\t"\x1c\n\x1aControllerShutdownResponse"A\n\x18ControllerMetricsRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\n \x01(\t"F\n\x19ControllerMetricsResponse\x12)\n\x07metrics\x18\x01 \x01(\x0b2\x18.containerd.types.Metric"|\n\x17ControllerUpdateRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x11\n\tsandboxer\x18\x02 \x01(\t\x12*\n\x07sandbox\x18\x03 \x01(\x0b2\x19.containerd.types.Sandbox\x12\x0e\n\x06fields\x18\x04 \x03(\t"\x1a\n\x18ControllerUpdateResponse2\xb7\x04\n\x05Store\x12q\n\x06Create\x122.containerd.services.sandbox.v1.StoreCreateRequest\x1a3.containerd.services.sandbox.v1.StoreCreateResponse\x12q\n\x06Update\x122.containerd.services.sandbox.v1.StoreUpdateRequest\x1a3.containerd.services.sandbox.v1.StoreUpdateResponse\x12q\n\x06Delete\x122.containerd.services.sandbox.v1.StoreDeleteRequest\x1a3.containerd.services.sandbox.v1.StoreDeleteResponse\x12k\n\x04List\x120.containerd.services.sandbox.v1.StoreListRequest\x1a1.containerd.services.sandbox.v1.StoreListResponse\x12h\n\x03Get\x12/.containerd.services.sandbox.v1.StoreGetRequest\x1a0.containerd.services.sandbox.v1.StoreGetResponse2\xf3\x08\n\nController\x12{\n\x06Create\x127.containerd.services.sandbox.v1.ControllerCreateRequest\x1a8.containerd.services.sandbox.v1.ControllerCreateResponse\x12x\n\x05Start\x126.containerd.services.sandbox.v1.ControllerStartRequest\x1a7.containerd.services.sandbox.v1.ControllerStartResponse\x12\x81\x01\n\x08Platform\x129.containerd.services.sandbox.v1.ControllerPlatformRequest\x1a:.containerd.services.sandbox.v1.ControllerPlatformResponse\x12u\n\x04Stop\x125.containerd.services.sandbox.v1.ControllerStopRequest\x1a6.containerd.services.sandbox.v1.ControllerStopResponse\x12u\n\x04Wait\x125.containerd.services.sandbox.v1.ControllerWaitRequest\x1a6.containerd.services.sandbox.v1.ControllerWaitResponse\x12{\n\x06Status\x127.containerd.services.sandbox.v1.ControllerStatusRequest\x1a8.containerd.services.sandbox.v1.ControllerStatusResponse\x12\x81\x01\n\x08Shutdown\x129.containerd.services.sandbox.v1.ControllerShutdownRequest\x1a:.containerd.services.sandbox.v1.ControllerShutdownResponse\x12~\n\x07Metrics\x128.containerd.services.sandbox.v1.ControllerMetricsRequest\x1a9.containerd.services.sandbox.v1.ControllerMetricsResponse\x12{\n\x06Update\x127.containerd.services.sandbox.v1.ControllerUpdateRequest\x1a8.containerd.services.sandbox.v1.ControllerUpdateResponseB(Z&containerd/services/sandbox/v1;sandboxb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.sandbox.v1.sandbox_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z&containerd/services/sandbox/v1;sandbox'
    _globals['_CONTROLLERCREATEREQUEST_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_CONTROLLERCREATEREQUEST_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_CONTROLLERSTARTRESPONSE_LABELSENTRY']._loaded_options = None
    _globals['_CONTROLLERSTARTRESPONSE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_CONTROLLERSTATUSRESPONSE_INFOENTRY']._loaded_options = None
    _globals['_CONTROLLERSTATUSRESPONSE_INFOENTRY']._serialized_options = b'8\x01'
    _globals['_STORECREATEREQUEST']._serialized_start = 267
    _globals['_STORECREATEREQUEST']._serialized_end = 331
    _globals['_STORECREATERESPONSE']._serialized_start = 333
    _globals['_STORECREATERESPONSE']._serialized_end = 398
    _globals['_STOREUPDATEREQUEST']._serialized_start = 400
    _globals['_STOREUPDATEREQUEST']._serialized_end = 480
    _globals['_STOREUPDATERESPONSE']._serialized_start = 482
    _globals['_STOREUPDATERESPONSE']._serialized_end = 547
    _globals['_STOREDELETEREQUEST']._serialized_start = 549
    _globals['_STOREDELETEREQUEST']._serialized_end = 589
    _globals['_STOREDELETERESPONSE']._serialized_start = 591
    _globals['_STOREDELETERESPONSE']._serialized_end = 612
    _globals['_STORELISTREQUEST']._serialized_start = 614
    _globals['_STORELISTREQUEST']._serialized_end = 649
    _globals['_STORELISTRESPONSE']._serialized_start = 651
    _globals['_STORELISTRESPONSE']._serialized_end = 711
    _globals['_STOREGETREQUEST']._serialized_start = 713
    _globals['_STOREGETREQUEST']._serialized_end = 750
    _globals['_STOREGETRESPONSE']._serialized_start = 752
    _globals['_STOREGETRESPONSE']._serialized_end = 814
    _globals['_CONTROLLERCREATEREQUEST']._serialized_start = 817
    _globals['_CONTROLLERCREATEREQUEST']._serialized_end = 1172
    _globals['_CONTROLLERCREATEREQUEST_ANNOTATIONSENTRY']._serialized_start = 1122
    _globals['_CONTROLLERCREATEREQUEST_ANNOTATIONSENTRY']._serialized_end = 1172
    _globals['_CONTROLLERCREATERESPONSE']._serialized_start = 1174
    _globals['_CONTROLLERCREATERESPONSE']._serialized_end = 1220
    _globals['_CONTROLLERSTARTREQUEST']._serialized_start = 1222
    _globals['_CONTROLLERSTARTREQUEST']._serialized_end = 1285
    _globals['_CONTROLLERSTARTRESPONSE']._serialized_start = 1288
    _globals['_CONTROLLERSTARTRESPONSE']._serialized_end = 1560
    _globals['_CONTROLLERSTARTRESPONSE_LABELSENTRY']._serialized_start = 1515
    _globals['_CONTROLLERSTARTRESPONSE_LABELSENTRY']._serialized_end = 1560
    _globals['_CONTROLLERPLATFORMREQUEST']._serialized_start = 1562
    _globals['_CONTROLLERPLATFORMREQUEST']._serialized_end = 1628
    _globals['_CONTROLLERPLATFORMRESPONSE']._serialized_start = 1630
    _globals['_CONTROLLERPLATFORMRESPONSE']._serialized_end = 1704
    _globals['_CONTROLLERSTOPREQUEST']._serialized_start = 1706
    _globals['_CONTROLLERSTOPREQUEST']._serialized_end = 1790
    _globals['_CONTROLLERSTOPRESPONSE']._serialized_start = 1792
    _globals['_CONTROLLERSTOPRESPONSE']._serialized_end = 1816
    _globals['_CONTROLLERWAITREQUEST']._serialized_start = 1818
    _globals['_CONTROLLERWAITREQUEST']._serialized_end = 1880
    _globals['_CONTROLLERWAITRESPONSE']._serialized_start = 1882
    _globals['_CONTROLLERWAITRESPONSE']._serialized_end = 1974
    _globals['_CONTROLLERSTATUSREQUEST']._serialized_start = 1976
    _globals['_CONTROLLERSTATUSREQUEST']._serialized_end = 2057
    _globals['_CONTROLLERSTATUSRESPONSE']._serialized_start = 2060
    _globals['_CONTROLLERSTATUSRESPONSE']._serialized_end = 2427
    _globals['_CONTROLLERSTATUSRESPONSE_INFOENTRY']._serialized_start = 2384
    _globals['_CONTROLLERSTATUSRESPONSE_INFOENTRY']._serialized_end = 2427
    _globals['_CONTROLLERSHUTDOWNREQUEST']._serialized_start = 2429
    _globals['_CONTROLLERSHUTDOWNREQUEST']._serialized_end = 2495
    _globals['_CONTROLLERSHUTDOWNRESPONSE']._serialized_start = 2497
    _globals['_CONTROLLERSHUTDOWNRESPONSE']._serialized_end = 2525
    _globals['_CONTROLLERMETRICSREQUEST']._serialized_start = 2527
    _globals['_CONTROLLERMETRICSREQUEST']._serialized_end = 2592
    _globals['_CONTROLLERMETRICSRESPONSE']._serialized_start = 2594
    _globals['_CONTROLLERMETRICSRESPONSE']._serialized_end = 2664
    _globals['_CONTROLLERUPDATEREQUEST']._serialized_start = 2666
    _globals['_CONTROLLERUPDATEREQUEST']._serialized_end = 2790
    _globals['_CONTROLLERUPDATERESPONSE']._serialized_start = 2792
    _globals['_CONTROLLERUPDATERESPONSE']._serialized_end = 2818
    _globals['_STORE']._serialized_start = 2821
    _globals['_STORE']._serialized_end = 3388
    _globals['_CONTROLLER']._serialized_start = 3391
    _globals['_CONTROLLER']._serialized_end = 4530