"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/introspection/v1/introspection.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from .....containerd.types import introspection_pb2 as containerd_dot_types_dot_introspection__pb2
from .....containerd.types import platform_pb2 as containerd_dot_types_dot_platform__pb2
from google.rpc import status_pb2 as google_dot_rpc_dot_status__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n8containerd/services/introspection/v1/introspection.proto\x12$containerd.services.introspection.v1\x1a\x19google/protobuf/any.proto\x1a$containerd/types/introspection.proto\x1a\x1fcontainerd/types/platform.proto\x1a\x17google/rpc/status.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x9b\x02\n\x06Plugin\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\t\x12\x10\n\x08requires\x18\x03 \x03(\t\x12-\n\tplatforms\x18\x04 \x03(\x0b2\x1a.containerd.types.Platform\x12J\n\x07exports\x18\x05 \x03(\x0b29.containerd.services.introspection.v1.Plugin.ExportsEntry\x12\x14\n\x0ccapabilities\x18\x06 \x03(\t\x12$\n\x08init_err\x18\x07 \x01(\x0b2\x12.google.rpc.Status\x1a.\n\x0cExportsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"!\n\x0ePluginsRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"P\n\x0fPluginsResponse\x12=\n\x07plugins\x18\x01 \x03(\x0b2,.containerd.services.introspection.v1.Plugin"\x8a\x01\n\x0eServerResponse\x12\x0c\n\x04uuid\x18\x01 \x01(\t\x12\x0b\n\x03pid\x18\x02 \x01(\x04\x12\r\n\x05pidns\x18\x03 \x01(\x04\x12N\n\x0cdeprecations\x18\x04 \x03(\x0b28.containerd.services.introspection.v1.DeprecationWarning"f\n\x12DeprecationWarning\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\x123\n\x0flast_occurrence\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp"T\n\x11PluginInfoRequest\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\n\n\x02id\x18\x02 \x01(\t\x12%\n\x07options\x18\x03 \x01(\x0b2\x14.google.protobuf.Any"w\n\x12PluginInfoResponse\x12<\n\x06plugin\x18\x01 \x01(\x0b2,.containerd.services.introspection.v1.Plugin\x12#\n\x05extra\x18\x02 \x01(\x0b2\x14.google.protobuf.Any2\xe0\x02\n\rIntrospection\x12v\n\x07Plugins\x124.containerd.services.introspection.v1.PluginsRequest\x1a5.containerd.services.introspection.v1.PluginsResponse\x12V\n\x06Server\x12\x16.google.protobuf.Empty\x1a4.containerd.services.introspection.v1.ServerResponse\x12\x7f\n\nPluginInfo\x127.containerd.services.introspection.v1.PluginInfoRequest\x1a8.containerd.services.introspection.v1.PluginInfoResponseB4Z2containerd/services/introspection/v1;introspectionb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.introspection.v1.introspection_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z2containerd/services/introspection/v1;introspection'
    _globals['_PLUGIN_EXPORTSENTRY']._loaded_options = None
    _globals['_PLUGIN_EXPORTSENTRY']._serialized_options = b'8\x01'
    _globals['_PLUGIN']._serialized_start = 284
    _globals['_PLUGIN']._serialized_end = 567
    _globals['_PLUGIN_EXPORTSENTRY']._serialized_start = 521
    _globals['_PLUGIN_EXPORTSENTRY']._serialized_end = 567
    _globals['_PLUGINSREQUEST']._serialized_start = 569
    _globals['_PLUGINSREQUEST']._serialized_end = 602
    _globals['_PLUGINSRESPONSE']._serialized_start = 604
    _globals['_PLUGINSRESPONSE']._serialized_end = 684
    _globals['_SERVERRESPONSE']._serialized_start = 687
    _globals['_SERVERRESPONSE']._serialized_end = 825
    _globals['_DEPRECATIONWARNING']._serialized_start = 827
    _globals['_DEPRECATIONWARNING']._serialized_end = 929
    _globals['_PLUGININFOREQUEST']._serialized_start = 931
    _globals['_PLUGININFOREQUEST']._serialized_end = 1015
    _globals['_PLUGININFORESPONSE']._serialized_start = 1017
    _globals['_PLUGININFORESPONSE']._serialized_end = 1136
    _globals['_INTROSPECTION']._serialized_start = 1139
    _globals['_INTROSPECTION']._serialized_end = 1491