"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/snapshots/v1/snapshots.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
from .....containerd.types import mount_pb2 as containerd_dot_types_dot_mount__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n0containerd/services/snapshots/v1/snapshots.proto\x12 containerd.services.snapshots.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a google/protobuf/field_mask.proto\x1a\x1fgoogle/protobuf/timestamp.proto\x1a\x1ccontainerd/types/mount.proto"\xcf\x01\n\x16PrepareSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\x0e\n\x06parent\x18\x03 \x01(\t\x12T\n\x06labels\x18\x04 \x03(\x0b2D.containerd.services.snapshots.v1.PrepareSnapshotRequest.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"B\n\x17PrepareSnapshotResponse\x12\'\n\x06mounts\x18\x01 \x03(\x0b2\x17.containerd.types.Mount"\xc9\x01\n\x13ViewSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t\x12\x0e\n\x06parent\x18\x03 \x01(\t\x12Q\n\x06labels\x18\x04 \x03(\x0b2A.containerd.services.snapshots.v1.ViewSnapshotRequest.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"?\n\x14ViewSnapshotResponse\x12\'\n\x06mounts\x18\x01 \x03(\x0b2\x17.containerd.types.Mount"1\n\rMountsRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t"9\n\x0eMountsResponse\x12\'\n\x06mounts\x18\x01 \x03(\x0b2\x17.containerd.types.Mount"9\n\x15RemoveSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t"\xdb\x01\n\x15CommitSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0c\n\x04name\x18\x02 \x01(\t\x12\x0b\n\x03key\x18\x03 \x01(\t\x12S\n\x06labels\x18\x04 \x03(\x0b2C.containerd.services.snapshots.v1.CommitSnapshotRequest.LabelsEntry\x12\x0e\n\x06parent\x18\x05 \x01(\t\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"7\n\x13StatSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t"\xad\x02\n\x04Info\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0e\n\x06parent\x18\x02 \x01(\t\x124\n\x04kind\x18\x03 \x01(\x0e2&.containerd.services.snapshots.v1.Kind\x12.\n\ncreated_at\x18\x04 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\x05 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12B\n\x06labels\x18\x06 \x03(\x0b22.containerd.services.snapshots.v1.Info.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"L\n\x14StatSnapshotResponse\x124\n\x04info\x18\x01 \x01(\x0b2&.containerd.services.snapshots.v1.Info"\x93\x01\n\x15UpdateSnapshotRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x124\n\x04info\x18\x02 \x01(\x0b2&.containerd.services.snapshots.v1.Info\x12/\n\x0bupdate_mask\x18\x03 \x01(\x0b2\x1a.google.protobuf.FieldMask"N\n\x16UpdateSnapshotResponse\x124\n\x04info\x18\x01 \x01(\x0b2&.containerd.services.snapshots.v1.Info"<\n\x14ListSnapshotsRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0f\n\x07filters\x18\x02 \x03(\t"M\n\x15ListSnapshotsResponse\x124\n\x04info\x18\x01 \x03(\x0b2&.containerd.services.snapshots.v1.Info"0\n\x0cUsageRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t\x12\x0b\n\x03key\x18\x02 \x01(\t"-\n\rUsageResponse\x12\x0c\n\x04size\x18\x01 \x01(\x03\x12\x0e\n\x06inodes\x18\x02 \x01(\x03"%\n\x0eCleanupRequest\x12\x13\n\x0bsnapshotter\x18\x01 \x01(\t*8\n\x04Kind\x12\x0b\n\x07UNKNOWN\x10\x00\x12\x08\n\x04VIEW\x10\x01\x12\n\n\x06ACTIVE\x10\x02\x12\r\n\tCOMMITTED\x10\x032\xd3\x08\n\tSnapshots\x12~\n\x07Prepare\x128.containerd.services.snapshots.v1.PrepareSnapshotRequest\x1a9.containerd.services.snapshots.v1.PrepareSnapshotResponse\x12u\n\x04View\x125.containerd.services.snapshots.v1.ViewSnapshotRequest\x1a6.containerd.services.snapshots.v1.ViewSnapshotResponse\x12k\n\x06Mounts\x12/.containerd.services.snapshots.v1.MountsRequest\x1a0.containerd.services.snapshots.v1.MountsResponse\x12Y\n\x06Commit\x127.containerd.services.snapshots.v1.CommitSnapshotRequest\x1a\x16.google.protobuf.Empty\x12Y\n\x06Remove\x127.containerd.services.snapshots.v1.RemoveSnapshotRequest\x1a\x16.google.protobuf.Empty\x12u\n\x04Stat\x125.containerd.services.snapshots.v1.StatSnapshotRequest\x1a6.containerd.services.snapshots.v1.StatSnapshotResponse\x12{\n\x06Update\x127.containerd.services.snapshots.v1.UpdateSnapshotRequest\x1a8.containerd.services.snapshots.v1.UpdateSnapshotResponse\x12y\n\x04List\x126.containerd.services.snapshots.v1.ListSnapshotsRequest\x1a7.containerd.services.snapshots.v1.ListSnapshotsResponse0\x01\x12h\n\x05Usage\x12..containerd.services.snapshots.v1.UsageRequest\x1a/.containerd.services.snapshots.v1.UsageResponse\x12S\n\x07Cleanup\x120.containerd.services.snapshots.v1.CleanupRequest\x1a\x16.google.protobuf.EmptyB,Z*containerd/services/snapshots/v1;snapshotsb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.snapshots.v1.snapshots_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z*containerd/services/snapshots/v1;snapshots'
    _globals['_PREPARESNAPSHOTREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_PREPARESNAPSHOTREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_VIEWSNAPSHOTREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_VIEWSNAPSHOTREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_COMMITSNAPSHOTREQUEST_LABELSENTRY']._loaded_options = None
    _globals['_COMMITSNAPSHOTREQUEST_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_INFO_LABELSENTRY']._loaded_options = None
    _globals['_INFO_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_KIND']._serialized_start = 2096
    _globals['_KIND']._serialized_end = 2152
    _globals['_PREPARESNAPSHOTREQUEST']._serialized_start = 213
    _globals['_PREPARESNAPSHOTREQUEST']._serialized_end = 420
    _globals['_PREPARESNAPSHOTREQUEST_LABELSENTRY']._serialized_start = 375
    _globals['_PREPARESNAPSHOTREQUEST_LABELSENTRY']._serialized_end = 420
    _globals['_PREPARESNAPSHOTRESPONSE']._serialized_start = 422
    _globals['_PREPARESNAPSHOTRESPONSE']._serialized_end = 488
    _globals['_VIEWSNAPSHOTREQUEST']._serialized_start = 491
    _globals['_VIEWSNAPSHOTREQUEST']._serialized_end = 692
    _globals['_VIEWSNAPSHOTREQUEST_LABELSENTRY']._serialized_start = 375
    _globals['_VIEWSNAPSHOTREQUEST_LABELSENTRY']._serialized_end = 420
    _globals['_VIEWSNAPSHOTRESPONSE']._serialized_start = 694
    _globals['_VIEWSNAPSHOTRESPONSE']._serialized_end = 757
    _globals['_MOUNTSREQUEST']._serialized_start = 759
    _globals['_MOUNTSREQUEST']._serialized_end = 808
    _globals['_MOUNTSRESPONSE']._serialized_start = 810
    _globals['_MOUNTSRESPONSE']._serialized_end = 867
    _globals['_REMOVESNAPSHOTREQUEST']._serialized_start = 869
    _globals['_REMOVESNAPSHOTREQUEST']._serialized_end = 926
    _globals['_COMMITSNAPSHOTREQUEST']._serialized_start = 929
    _globals['_COMMITSNAPSHOTREQUEST']._serialized_end = 1148
    _globals['_COMMITSNAPSHOTREQUEST_LABELSENTRY']._serialized_start = 375
    _globals['_COMMITSNAPSHOTREQUEST_LABELSENTRY']._serialized_end = 420
    _globals['_STATSNAPSHOTREQUEST']._serialized_start = 1150
    _globals['_STATSNAPSHOTREQUEST']._serialized_end = 1205
    _globals['_INFO']._serialized_start = 1208
    _globals['_INFO']._serialized_end = 1509
    _globals['_INFO_LABELSENTRY']._serialized_start = 375
    _globals['_INFO_LABELSENTRY']._serialized_end = 420
    _globals['_STATSNAPSHOTRESPONSE']._serialized_start = 1511
    _globals['_STATSNAPSHOTRESPONSE']._serialized_end = 1587
    _globals['_UPDATESNAPSHOTREQUEST']._serialized_start = 1590
    _globals['_UPDATESNAPSHOTREQUEST']._serialized_end = 1737
    _globals['_UPDATESNAPSHOTRESPONSE']._serialized_start = 1739
    _globals['_UPDATESNAPSHOTRESPONSE']._serialized_end = 1817
    _globals['_LISTSNAPSHOTSREQUEST']._serialized_start = 1819
    _globals['_LISTSNAPSHOTSREQUEST']._serialized_end = 1879
    _globals['_LISTSNAPSHOTSRESPONSE']._serialized_start = 1881
    _globals['_LISTSNAPSHOTSRESPONSE']._serialized_end = 1958
    _globals['_USAGEREQUEST']._serialized_start = 1960
    _globals['_USAGEREQUEST']._serialized_end = 2008
    _globals['_USAGERESPONSE']._serialized_start = 2010
    _globals['_USAGERESPONSE']._serialized_end = 2055
    _globals['_CLEANUPREQUEST']._serialized_start = 2057
    _globals['_CLEANUPREQUEST']._serialized_end = 2094
    _globals['_SNAPSHOTS']._serialized_start = 2155
    _globals['_SNAPSHOTS']._serialized_end = 3262