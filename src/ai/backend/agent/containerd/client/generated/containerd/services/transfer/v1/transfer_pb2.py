"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/transfer/v1/transfer.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n.containerd/services/transfer/v1/transfer.proto\x12\x1fcontainerd.services.transfer.v1\x1a\x19google/protobuf/any.proto\x1a\x1bgoogle/protobuf/empty.proto"\xa5\x01\n\x0fTransferRequest\x12$\n\x06source\x18\x01 \x01(\x0b2\x14.google.protobuf.Any\x12)\n\x0bdestination\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x12A\n\x07options\x18\x03 \x01(\x0b20.containerd.services.transfer.v1.TransferOptions"*\n\x0fTransferOptions\x12\x17\n\x0fprogress_stream\x18\x01 \x01(\t2`\n\x08Transfer\x12T\n\x08Transfer\x120.containerd.services.transfer.v1.TransferRequest\x1a\x16.google.protobuf.EmptyB*Z(containerd/services/transfer/v1;transferb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.transfer.v1.transfer_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z(containerd/services/transfer/v1;transfer'
    _globals['_TRANSFERREQUEST']._serialized_start = 140
    _globals['_TRANSFERREQUEST']._serialized_end = 305
    _globals['_TRANSFEROPTIONS']._serialized_start = 307
    _globals['_TRANSFEROPTIONS']._serialized_end = 349
    _globals['_TRANSFER']._serialized_start = 351
    _globals['_TRANSFER']._serialized_end = 447