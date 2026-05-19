"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/types/transfer/registry.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n(containerd/types/transfer/registry.proto\x12\x19containerd.types.transfer\x1a\x1fgoogle/protobuf/timestamp.proto"_\n\x0bOCIRegistry\x12\x11\n\treference\x18\x01 \x01(\t\x12=\n\x08resolver\x18\x02 \x01(\x0b2+.containerd.types.transfer.RegistryResolver"\x9b\x02\n\x10RegistryResolver\x12\x13\n\x0bauth_stream\x18\x01 \x01(\t\x12I\n\x07headers\x18\x02 \x03(\x0b28.containerd.types.transfer.RegistryResolver.HeadersEntry\x12\x10\n\x08host_dir\x18\x03 \x01(\t\x12\x16\n\x0edefault_scheme\x18\x04 \x01(\t\x128\n\nhttp_debug\x18\x05 \x01(\x0e2$.containerd.types.transfer.HTTPDebug\x12\x13\n\x0blogs_stream\x18\x06 \x01(\t\x1a.\n\x0cHeadersEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"G\n\x0bAuthRequest\x12\x0c\n\x04host\x18\x01 \x01(\t\x12\x11\n\treference\x18\x02 \x01(\t\x12\x17\n\x0fwwwauthenticate\x18\x03 \x03(\t"\x96\x01\n\x0cAuthResponse\x125\n\x08authType\x18\x01 \x01(\x0e2#.containerd.types.transfer.AuthType\x12\x0e\n\x06secret\x18\x02 \x01(\t\x12\x10\n\x08username\x18\x03 \x01(\t\x12-\n\texpire_at\x18\x04 \x01(\x0b2\x1a.google.protobuf.Timestamp*9\n\tHTTPDebug\x12\x0c\n\x08DISABLED\x10\x00\x12\t\n\x05DEBUG\x10\x01\x12\t\n\x05TRACE\x10\x02\x12\x08\n\x04BOTH\x10\x03*>\n\x08AuthType\x12\x08\n\x04NONE\x10\x00\x12\x0f\n\x0bCREDENTIALS\x10\x01\x12\x0b\n\x07REFRESH\x10\x02\x12\n\n\x06HEADER\x10\x03B\x1bZ\x19containerd/types/transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.types.transfer.registry_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z\x19containerd/types/transfer'
    _globals['_REGISTRYRESOLVER_HEADERSENTRY']._loaded_options = None
    _globals['_REGISTRYRESOLVER_HEADERSENTRY']._serialized_options = b'8\x01'
    _globals['_HTTPDEBUG']._serialized_start = 713
    _globals['_HTTPDEBUG']._serialized_end = 770
    _globals['_AUTHTYPE']._serialized_start = 772
    _globals['_AUTHTYPE']._serialized_end = 834
    _globals['_OCIREGISTRY']._serialized_start = 104
    _globals['_OCIREGISTRY']._serialized_end = 199
    _globals['_REGISTRYRESOLVER']._serialized_start = 202
    _globals['_REGISTRYRESOLVER']._serialized_end = 485
    _globals['_REGISTRYRESOLVER_HEADERSENTRY']._serialized_start = 439
    _globals['_REGISTRYRESOLVER_HEADERSENTRY']._serialized_end = 485
    _globals['_AUTHREQUEST']._serialized_start = 487
    _globals['_AUTHREQUEST']._serialized_end = 558
    _globals['_AUTHRESPONSE']._serialized_start = 561
    _globals['_AUTHRESPONSE']._serialized_end = 711