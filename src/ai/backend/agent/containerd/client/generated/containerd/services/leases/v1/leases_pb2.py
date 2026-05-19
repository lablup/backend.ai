"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/leases/v1/leases.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n*containerd/services/leases/v1/leases.proto\x12\x1dcontainerd.services.leases.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\xb4\x01\n\x05Lease\x12\n\n\x02id\x18\x01 \x01(\t\x12.\n\ncreated_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12@\n\x06labels\x18\x03 \x03(\x0b20.containerd.services.leases.v1.Lease.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x94\x01\n\rCreateRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12H\n\x06labels\x18\x03 \x03(\x0b28.containerd.services.leases.v1.CreateRequest.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"E\n\x0eCreateResponse\x123\n\x05lease\x18\x01 \x01(\x0b2$.containerd.services.leases.v1.Lease")\n\rDeleteRequest\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04sync\x18\x02 \x01(\x08"\x1e\n\x0bListRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"D\n\x0cListResponse\x124\n\x06leases\x18\x01 \x03(\x0b2$.containerd.services.leases.v1.Lease"$\n\x08Resource\x12\n\n\x02id\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t"[\n\x12AddResourceRequest\x12\n\n\x02id\x18\x01 \x01(\t\x129\n\x08resource\x18\x02 \x01(\x0b2\'.containerd.services.leases.v1.Resource"^\n\x15DeleteResourceRequest\x12\n\n\x02id\x18\x01 \x01(\t\x129\n\x08resource\x18\x02 \x01(\x0b2\'.containerd.services.leases.v1.Resource""\n\x14ListResourcesRequest\x12\n\n\x02id\x18\x01 \x01(\t"S\n\x15ListResourcesResponse\x12:\n\tresources\x18\x01 \x03(\x0b2\'.containerd.services.leases.v1.Resource2\xd6\x04\n\x06Leases\x12e\n\x06Create\x12,.containerd.services.leases.v1.CreateRequest\x1a-.containerd.services.leases.v1.CreateResponse\x12N\n\x06Delete\x12,.containerd.services.leases.v1.DeleteRequest\x1a\x16.google.protobuf.Empty\x12_\n\x04List\x12*.containerd.services.leases.v1.ListRequest\x1a+.containerd.services.leases.v1.ListResponse\x12X\n\x0bAddResource\x121.containerd.services.leases.v1.AddResourceRequest\x1a\x16.google.protobuf.Empty\x12^\n\x0eDeleteResource\x124.containerd.services.leases.v1.DeleteResourceRequest\x1a\x16.google.protobuf.Empty\x12z\n\rListResources\x123.containerd.services.leases.v1.ListResourcesRequest\x1a4.containerd.services.leases.v1.ListResourcesResponseB&Z$containerd/services/leases/v1;leasesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.leases.v1.leases_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z$containerd/services/leases/v1;leases'
    _globals['_LEASE_LABELSENTRY']._loaded_options = None
    _globals['_LEASE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_CREATEREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_CREATEREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_LEASE']._serialized_start = 140
    _globals['_LEASE']._serialized_end = 320
    _globals['_LEASE_LABELSENTRY']._serialized_start = 275
    _globals['_LEASE_LABELSENTRY']._serialized_end = 320
    _globals['_CREATEREQUEST']._serialized_start = 323
    _globals['_CREATEREQUEST']._serialized_end = 471
    _globals['_CREATEREQUEST_LABELSENTRY']._serialized_start = 275
    _globals['_CREATEREQUEST_LABELSENTRY']._serialized_end = 320
    _globals['_CREATERESPONSE']._serialized_start = 473
    _globals['_CREATERESPONSE']._serialized_end = 542
    _globals['_DELETEREQUEST']._serialized_start = 544
    _globals['_DELETEREQUEST']._serialized_end = 585
    _globals['_LISTREQUEST']._serialized_start = 587
    _globals['_LISTREQUEST']._serialized_end = 617
    _globals['_LISTRESPONSE']._serialized_start = 619
    _globals['_LISTRESPONSE']._serialized_end = 687
    _globals['_RESOURCE']._serialized_start = 689
    _globals['_RESOURCE']._serialized_end = 725
    _globals['_ADDRESOURCEREQUEST']._serialized_start = 727
    _globals['_ADDRESOURCEREQUEST']._serialized_end = 818
    _globals['_DELETERESOURCEREQUEST']._serialized_start = 820
    _globals['_DELETERESOURCEREQUEST']._serialized_end = 914
    _globals['_LISTRESOURCESREQUEST']._serialized_start = 916
    _globals['_LISTRESOURCESREQUEST']._serialized_end = 950
    _globals['_LISTRESOURCESRESPONSE']._serialized_start = 952
    _globals['_LISTRESOURCESRESPONSE']._serialized_end = 1035
    _globals['_LEASES']._serialized_start = 1038
    _globals['_LEASES']._serialized_end = 1636