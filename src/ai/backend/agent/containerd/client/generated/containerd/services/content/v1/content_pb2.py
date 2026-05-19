"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/content/v1/content.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n,containerd/services/content/v1/content.proto\x12\x1econtainerd.services.content.v1\x1a google/protobuf/field_mask.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1bgoogle/protobuf/empty.proto"\xf5\x01\n\x04Info\x12\x0e\n\x06digest\x18\x01 \x01(\t\x12\x0c\n\x04size\x18\x02 \x01(\x03\x12.\n\ncreated_at\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x04 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12@\n\x06labels\x18\x05 \x03(\x0b20.containerd.services.content.v1.Info.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\x1d\n\x0bInfoRequest\x12\x0e\n\x06digest\x18\x01 \x01(\t"B\n\x0cInfoResponse\x122\n\x04info\x18\x01 \x01(\x0b2$.containerd.services.content.v1.Info"t\n\rUpdateRequest\x122\n\x04info\x18\x01 \x01(\x0b2$.containerd.services.content.v1.Info\x12/\n\x0bupdate_mask\x18\x02 \x01(\x0b2\x1a.google.protobuf.FieldMask"D\n\x0eUpdateResponse\x122\n\x04info\x18\x01 \x01(\x0b2$.containerd.services.content.v1.Info"%\n\x12ListContentRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"I\n\x13ListContentResponse\x122\n\x04info\x18\x01 \x03(\x0b2$.containerd.services.content.v1.Info"&\n\x14DeleteContentRequest\x12\x0e\n\x06digest\x18\x01 \x01(\t"B\n\x12ReadContentRequest\x12\x0e\n\x06digest\x18\x01 \x01(\t\x12\x0e\n\x06offset\x18\x02 \x01(\x03\x12\x0c\n\x04size\x18\x03 \x01(\x03"3\n\x13ReadContentResponse\x12\x0e\n\x06offset\x18\x01 \x01(\x03\x12\x0c\n\x04data\x18\x02 \x01(\x0c"\xa6\x01\n\x06Status\x12.\n\nstarted_at\x18\x01 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\x0b\n\x03ref\x18\x03 \x01(\t\x12\x0e\n\x06offset\x18\x04 \x01(\x03\x12\r\n\x05total\x18\x05 \x01(\x03\x12\x10\n\x08expected\x18\x06 \x01(\t"\x1c\n\rStatusRequest\x12\x0b\n\x03ref\x18\x01 \x01(\t"H\n\x0eStatusResponse\x126\n\x06status\x18\x01 \x01(\x0b2&.containerd.services.content.v1.Status"&\n\x13ListStatusesRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"P\n\x14ListStatusesResponse\x128\n\x08statuses\x18\x01 \x03(\x0b2&.containerd.services.content.v1.Status"\x9e\x02\n\x13WriteContentRequest\x12;\n\x06action\x18\x01 \x01(\x0e2+.containerd.services.content.v1.WriteAction\x12\x0b\n\x03ref\x18\x02 \x01(\t\x12\r\n\x05total\x18\x03 \x01(\x03\x12\x10\n\x08expected\x18\x04 \x01(\t\x12\x0e\n\x06offset\x18\x05 \x01(\x03\x12\x0c\n\x04data\x18\x06 \x01(\x0c\x12O\n\x06labels\x18\x07 \x03(\x0b2?.containerd.services.content.v1.WriteContentRequest.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"\xe2\x01\n\x14WriteContentResponse\x12;\n\x06action\x18\x01 \x01(\x0e2+.containerd.services.content.v1.WriteAction\x12.\n\nstarted_at\x18\x02 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x03 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12\x0e\n\x06offset\x18\x04 \x01(\x03\x12\r\n\x05total\x18\x05 \x01(\x03\x12\x0e\n\x06digest\x18\x06 \x01(\t"\x1b\n\x0cAbortRequest\x12\x0b\n\x03ref\x18\x01 \x01(\t*.\n\x0bWriteAction\x12\x08\n\x04STAT\x10\x00\x12\t\n\x05WRITE\x10\x01\x12\n\n\x06COMMIT\x10\x022\xbe\x07\n\x07Content\x12a\n\x04Info\x12+.containerd.services.content.v1.InfoRequest\x1a,.containerd.services.content.v1.InfoResponse\x12g\n\x06Update\x12-.containerd.services.content.v1.UpdateRequest\x1a..containerd.services.content.v1.UpdateResponse\x12q\n\x04List\x122.containerd.services.content.v1.ListContentRequest\x1a3.containerd.services.content.v1.ListContentResponse0\x01\x12V\n\x06Delete\x124.containerd.services.content.v1.DeleteContentRequest\x1a\x16.google.protobuf.Empty\x12q\n\x04Read\x122.containerd.services.content.v1.ReadContentRequest\x1a3.containerd.services.content.v1.ReadContentResponse0\x01\x12g\n\x06Status\x12-.containerd.services.content.v1.StatusRequest\x1a..containerd.services.content.v1.StatusResponse\x12y\n\x0cListStatuses\x123.containerd.services.content.v1.ListStatusesRequest\x1a4.containerd.services.content.v1.ListStatusesResponse\x12v\n\x05Write\x123.containerd.services.content.v1.WriteContentRequest\x1a4.containerd.services.content.v1.WriteContentResponse(\x010\x01\x12M\n\x05Abort\x12,.containerd.services.content.v1.AbortRequest\x1a\x16.google.protobuf.EmptyB(Z&containerd/services/content/v1;contentb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.content.v1.content_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z&containerd/services/content/v1;content'
    _globals['_INFO_LABELSENTRY']._loaded_options = None
    _globals['_INFO_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_WRITECONTENTREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_WRITECONTENTREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_WRITEACTION']._serialized_start = 1928
    _globals['_WRITEACTION']._serialized_end = 1974
    _globals['_INFO']._serialized_start = 177
    _globals['_INFO']._serialized_end = 422
    _globals['_INFO_LABELSENTRY']._serialized_start = 377
    _globals['_INFO_LABELSENTRY']._serialized_end = 422
    _globals['_INFOREQUEST']._serialized_start = 424
    _globals['_INFOREQUEST']._serialized_end = 453
    _globals['_INFORESPONSE']._serialized_start = 455
    _globals['_INFORESPONSE']._serialized_end = 521
    _globals['_UPDATEREQUEST']._serialized_start = 523
    _globals['_UPDATEREQUEST']._serialized_end = 639
    _globals['_UPDATERESPONSE']._serialized_start = 641
    _globals['_UPDATERESPONSE']._serialized_end = 709
    _globals['_LISTCONTENTREQUEST']._serialized_start = 711
    _globals['_LISTCONTENTREQUEST']._serialized_end = 748
    _globals['_LISTCONTENTRESPONSE']._serialized_start = 750
    _globals['_LISTCONTENTRESPONSE']._serialized_end = 823
    _globals['_DELETECONTENTREQUEST']._serialized_start = 825
    _globals['_DELETECONTENTREQUEST']._serialized_end = 863
    _globals['_READCONTENTREQUEST']._serialized_start = 865
    _globals['_READCONTENTREQUEST']._serialized_end = 931
    _globals['_READCONTENTRESPONSE']._serialized_start = 933
    _globals['_READCONTENTRESPONSE']._serialized_end = 984
    _globals['_STATUS']._serialized_start = 987
    _globals['_STATUS']._serialized_end = 1153
    _globals['_STATUSREQUEST']._serialized_start = 1155
    _globals['_STATUSREQUEST']._serialized_end = 1183
    _globals['_STATUSRESPONSE']._serialized_start = 1185
    _globals['_STATUSRESPONSE']._serialized_end = 1257
    _globals['_LISTSTATUSESREQUEST']._serialized_start = 1259
    _globals['_LISTSTATUSESREQUEST']._serialized_end = 1297
    _globals['_LISTSTATUSESRESPONSE']._serialized_start = 1299
    _globals['_LISTSTATUSESRESPONSE']._serialized_end = 1379
    _globals['_WRITECONTENTREQUEST']._serialized_start = 1382
    _globals['_WRITECONTENTREQUEST']._serialized_end = 1668
    _globals['_WRITECONTENTREQUEST_LABELSENTRY']._serialized_start = 377
    _globals['_WRITECONTENTREQUEST_LABELSENTRY']._serialized_end = 422
    _globals['_WRITECONTENTRESPONSE']._serialized_start = 1671
    _globals['_WRITECONTENTRESPONSE']._serialized_end = 1897
    _globals['_ABORTREQUEST']._serialized_start = 1899
    _globals['_ABORTREQUEST']._serialized_end = 1926
    _globals['_CONTENT']._serialized_start = 1977
    _globals['_CONTENT']._serialized_end = 2935