"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/runtime/sandbox/v1/sandbox.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
from .....containerd.types import platform_pb2 as containerd_dot_types_dot_platform__pb2
from .....containerd.types import metrics_pb2 as containerd_dot_types_dot_metrics__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n+containerd/runtime/sandbox/v1/sandbox.proto\x12\x1dcontainerd.runtime.sandbox.v1\x1a\x19google/protobuf/any.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1ccontainerd/types/mount.proto\x1a\x1fcontainerd/types/platform.proto\x1a\x1econtainerd/types/metrics.proto"\xb2\x02\n\x14CreateSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x13\n\x0bbundle_path\x18\x02 \x01(\t\x12\'\n\x06rootfs\x18\x03 \x03(\x0b2\x17.containerd.types.Mount\x12%\n\x07options\x18\x04 \x01(\x0b2\x14.google.protobuf.Any\x12\x12\n\nnetns_path\x18\x05 \x01(\t\x12Y\n\x0bannotations\x18\x06 \x03(\x0b2D.containerd.runtime.sandbox.v1.CreateSandboxRequest.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x17\n\x15CreateSandboxResponse")\n\x13StartSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"S\n\x14StartSandboxResponse\x12\x0b\n\x03pid\x18\x01 \x01(\r\x12.\n\ncreated_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp"%\n\x0fPlatformRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"@\n\x10PlatformResponse\x12,\n\x08platform\x18\x01 \x01(\x0b2\x1a.containerd.types.Platform">\n\x12StopSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x14\n\x0ctimeout_secs\x18\x02 \x01(\r"\x15\n\x13StopSandboxResponse"\xe2\x01\n\x14UpdateSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\'\n\tresources\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x12Y\n\x0bannotations\x18\x03 \x03(\x0b2D.containerd.runtime.sandbox.v1.UpdateSandboxRequest.AnnotationsEntry\x1a2\n\x10AnnotationsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"(\n\x12WaitSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"Y\n\x13WaitSandboxResponse\x12\x13\n\x0bexit_status\x18\x01 \x01(\r\x12-\n\texited_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp"\x17\n\x15UpdateSandboxResponse";\n\x14SandboxStatusRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x0f\n\x07verbose\x18\x02 \x01(\x08"\xc6\x02\n\x15SandboxStatusResponse\x12\x12\n\nsandbox_id\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\r\x12\r\n\x05state\x18\x03 \x01(\t\x12L\n\x04info\x18\x04 \x03(\x0b2>.containerd.runtime.sandbox.v1.SandboxStatusResponse.InfoEntry\x12.\n\ncreated_at\x18\x05 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12-\n\texited_at\x18\x06 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12#\n\x05extra\x18\x07 \x01(\x0b2\x14.google.protobuf.Any\x1a+\n\tInfoEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"!\n\x0bPingRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"\x0e\n\x0cPingResponse",\n\x16ShutdownSandboxRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"\x19\n\x17ShutdownSandboxResponse"+\n\x15SandboxMetricsRequest\x12\x12\n\nsandbox_id\x18\x01 \x01(\t"C\n\x16SandboxMetricsResponse\x12)\n\x07metrics\x18\x01 \x01(\x0b2\x18.containerd.types.Metric2\xbd\x08\n\x07Sandbox\x12z\n\rCreateSandbox\x123.containerd.runtime.sandbox.v1.CreateSandboxRequest\x1a4.containerd.runtime.sandbox.v1.CreateSandboxResponse\x12w\n\x0cStartSandbox\x122.containerd.runtime.sandbox.v1.StartSandboxRequest\x1a3.containerd.runtime.sandbox.v1.StartSandboxResponse\x12k\n\x08Platform\x12..containerd.runtime.sandbox.v1.PlatformRequest\x1a/.containerd.runtime.sandbox.v1.PlatformResponse\x12t\n\x0bStopSandbox\x121.containerd.runtime.sandbox.v1.StopSandboxRequest\x1a2.containerd.runtime.sandbox.v1.StopSandboxResponse\x12t\n\x0bWaitSandbox\x121.containerd.runtime.sandbox.v1.WaitSandboxRequest\x1a2.containerd.runtime.sandbox.v1.WaitSandboxResponse\x12z\n\rSandboxStatus\x123.containerd.runtime.sandbox.v1.SandboxStatusRequest\x1a4.containerd.runtime.sandbox.v1.SandboxStatusResponse\x12f\n\x0bPingSandbox\x12*.containerd.runtime.sandbox.v1.PingRequest\x1a+.containerd.runtime.sandbox.v1.PingResponse\x12\x80\x01\n\x0fShutdownSandbox\x125.containerd.runtime.sandbox.v1.ShutdownSandboxRequest\x1a6.containerd.runtime.sandbox.v1.ShutdownSandboxResponse\x12}\n\x0eSandboxMetrics\x124.containerd.runtime.sandbox.v1.SandboxMetricsRequest\x1a5.containerd.runtime.sandbox.v1.SandboxMetricsResponseB\'Z%containerd/runtime/sandbox/v1;sandboxb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.runtime.sandbox.v1.sandbox_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z%containerd/runtime/sandbox/v1;sandbox'
    _globals['_CREATESANDBOXREQUEST_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_CREATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_UPDATESANDBOXREQUEST_ANNOTATIONSENTRY']._loaded_options = None
    _globals['_UPDATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_options = b'8\x01'
    _globals['_SANDBOXSTATUSRESPONSE_INFOENTRY']._loaded_options = None
    _globals['_SANDBOXSTATUSRESPONSE_INFOENTRY']._serialized_options = b'8\x01'
    _globals['_CREATESANDBOXREQUEST']._serialized_start = 234
    _globals['_CREATESANDBOXREQUEST']._serialized_end = 540
    _globals['_CREATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_start = 490
    _globals['_CREATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_end = 540
    _globals['_CREATESANDBOXRESPONSE']._serialized_start = 542
    _globals['_CREATESANDBOXRESPONSE']._serialized_end = 565
    _globals['_STARTSANDBOXREQUEST']._serialized_start = 567
    _globals['_STARTSANDBOXREQUEST']._serialized_end = 608
    _globals['_STARTSANDBOXRESPONSE']._serialized_start = 610
    _globals['_STARTSANDBOXRESPONSE']._serialized_end = 693
    _globals['_PLATFORMREQUEST']._serialized_start = 695
    _globals['_PLATFORMREQUEST']._serialized_end = 732
    _globals['_PLATFORMRESPONSE']._serialized_start = 734
    _globals['_PLATFORMRESPONSE']._serialized_end = 798
    _globals['_STOPSANDBOXREQUEST']._serialized_start = 800
    _globals['_STOPSANDBOXREQUEST']._serialized_end = 862
    _globals['_STOPSANDBOXRESPONSE']._serialized_start = 864
    _globals['_STOPSANDBOXRESPONSE']._serialized_end = 885
    _globals['_UPDATESANDBOXREQUEST']._serialized_start = 888
    _globals['_UPDATESANDBOXREQUEST']._serialized_end = 1114
    _globals['_UPDATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_start = 490
    _globals['_UPDATESANDBOXREQUEST_ANNOTATIONSENTRY']._serialized_end = 540
    _globals['_WAITSANDBOXREQUEST']._serialized_start = 1116
    _globals['_WAITSANDBOXREQUEST']._serialized_end = 1156
    _globals['_WAITSANDBOXRESPONSE']._serialized_start = 1158
    _globals['_WAITSANDBOXRESPONSE']._serialized_end = 1247
    _globals['_UPDATESANDBOXRESPONSE']._serialized_start = 1249
    _globals['_UPDATESANDBOXRESPONSE']._serialized_end = 1272
    _globals['_SANDBOXSTATUSREQUEST']._serialized_start = 1274
    _globals['_SANDBOXSTATUSREQUEST']._serialized_end = 1333
    _globals['_SANDBOXSTATUSRESPONSE']._serialized_start = 1336
    _globals['_SANDBOXSTATUSRESPONSE']._serialized_end = 1662
    _globals['_SANDBOXSTATUSRESPONSE_INFOENTRY']._serialized_start = 1619
    _globals['_SANDBOXSTATUSRESPONSE_INFOENTRY']._serialized_end = 1662
    _globals['_PINGREQUEST']._serialized_start = 1664
    _globals['_PINGREQUEST']._serialized_end = 1697
    _globals['_PINGRESPONSE']._serialized_start = 1699
    _globals['_PINGRESPONSE']._serialized_end = 1713
    _globals['_SHUTDOWNSANDBOXREQUEST']._serialized_start = 1715
    _globals['_SHUTDOWNSANDBOXREQUEST']._serialized_end = 1759
    _globals['_SHUTDOWNSANDBOXRESPONSE']._serialized_start = 1761
    _globals['_SHUTDOWNSANDBOXRESPONSE']._serialized_end = 1786
    _globals['_SANDBOXMETRICSREQUEST']._serialized_start = 1788
    _globals['_SANDBOXMETRICSREQUEST']._serialized_end = 1831
    _globals['_SANDBOXMETRICSRESPONSE']._serialized_start = 1833
    _globals['_SANDBOXMETRICSRESPONSE']._serialized_end = 1900
    _globals['_SANDBOX']._serialized_start = 1903
    _globals['_SANDBOX']._serialized_end = 2988