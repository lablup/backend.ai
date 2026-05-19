"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/containers/v1/containers.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n2containerd/services/containers/v1/containers.proto\x12!containerd.services.containers.v1\x1a\x19google/protobuf/any.proto\x1a\x1bgoogle/protobuf/empty.proto\x1a google/protobuf/field_mask.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\x81\x05\n\tContainer\x12\n\n\x02id\x18\x01 \x01(\t\x12H\n\x06labels\x18\x02 \x03(\x0b28.containerd.services.containers.v1.Container.LabelsEntry\x12\r\n\x05image\x18\x03 \x01(\t\x12E\n\x07runtime\x18\x04 \x01(\x0b24.containerd.services.containers.v1.Container.Runtime\x12"\n\x04spec\x18\x05 \x01(\x0b2\x14.google.protobuf.Any\x12\x13\n\x0bsnapshotter\x18\x06 \x01(\t\x12\x14\n\x0csnapshot_key\x18\x07 \x01(\t\x12.\n\ncreated_at\x18\x08 \x01(\x0b2\x1a.google.protobuf.Timestamp\x12.\n\nupdated_at\x18\t \x01(\x0b2\x1a.google.protobuf.Timestamp\x12P\n\nextensions\x18\n \x03(\x0b2<.containerd.services.containers.v1.Container.ExtensionsEntry\x12\x0f\n\x07sandbox\x18\x0b \x01(\t\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01\x1a>\n\x07Runtime\x12\x0c\n\x04name\x18\x01 \x01(\t\x12%\n\x07options\x18\x02 \x01(\x0b2\x14.google.protobuf.Any\x1aG\n\x0fExtensionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12#\n\x05value\x18\x02 \x01(\x0b2\x14.google.protobuf.Any:\x028\x01"!\n\x13GetContainerRequest\x12\n\n\x02id\x18\x01 \x01(\t"W\n\x14GetContainerResponse\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container"(\n\x15ListContainersRequest\x12\x0f\n\x07filters\x18\x01 \x03(\t"Z\n\x16ListContainersResponse\x12@\n\ncontainers\x18\x01 \x03(\x0b2,.containerd.services.containers.v1.Container"Y\n\x16CreateContainerRequest\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container"Z\n\x17CreateContainerResponse\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container"\x8a\x01\n\x16UpdateContainerRequest\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container\x12/\n\x0bupdate_mask\x18\x02 \x01(\x0b2\x1a.google.protobuf.FieldMask"Z\n\x17UpdateContainerResponse\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container"$\n\x16DeleteContainerRequest\x12\n\n\x02id\x18\x01 \x01(\t"W\n\x14ListContainerMessage\x12?\n\tcontainer\x18\x01 \x01(\x0b2,.containerd.services.containers.v1.Container2\xe4\x05\n\nContainers\x12v\n\x03Get\x126.containerd.services.containers.v1.GetContainerRequest\x1a7.containerd.services.containers.v1.GetContainerResponse\x12{\n\x04List\x128.containerd.services.containers.v1.ListContainersRequest\x1a9.containerd.services.containers.v1.ListContainersResponse\x12\x81\x01\n\nListStream\x128.containerd.services.containers.v1.ListContainersRequest\x1a7.containerd.services.containers.v1.ListContainerMessage0\x01\x12\x7f\n\x06Create\x129.containerd.services.containers.v1.CreateContainerRequest\x1a:.containerd.services.containers.v1.CreateContainerResponse\x12\x7f\n\x06Update\x129.containerd.services.containers.v1.UpdateContainerRequest\x1a:.containerd.services.containers.v1.UpdateContainerResponse\x12[\n\x06Delete\x129.containerd.services.containers.v1.DeleteContainerRequest\x1a\x16.google.protobuf.EmptyB.Z,containerd/services/containers/v1;containersb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.containers.v1.containers_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z,containerd/services/containers/v1;containers'
    _globals['_CONTAINER_LABELSENTRY']._loaded_options = None
    _globals['_CONTAINER_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_CONTAINER_EXTENSIONSENTRY']._loaded_options = None
    _globals['_CONTAINER_EXTENSIONSENTRY']._serialized_options = b'8\x01'
    _globals['_CONTAINER']._serialized_start = 213
    _globals['_CONTAINER']._serialized_end = 854
    _globals['_CONTAINER_LABELSENTRY']._serialized_start = 672
    _globals['_CONTAINER_LABELSENTRY']._serialized_end = 717
    _globals['_CONTAINER_RUNTIME']._serialized_start = 719
    _globals['_CONTAINER_RUNTIME']._serialized_end = 781
    _globals['_CONTAINER_EXTENSIONSENTRY']._serialized_start = 783
    _globals['_CONTAINER_EXTENSIONSENTRY']._serialized_end = 854
    _globals['_GETCONTAINERREQUEST']._serialized_start = 856
    _globals['_GETCONTAINERREQUEST']._serialized_end = 889
    _globals['_GETCONTAINERRESPONSE']._serialized_start = 891
    _globals['_GETCONTAINERRESPONSE']._serialized_end = 978
    _globals['_LISTCONTAINERSREQUEST']._serialized_start = 980
    _globals['_LISTCONTAINERSREQUEST']._serialized_end = 1020
    _globals['_LISTCONTAINERSRESPONSE']._serialized_start = 1022
    _globals['_LISTCONTAINERSRESPONSE']._serialized_end = 1112
    _globals['_CREATECONTAINERREQUEST']._serialized_start = 1114
    _globals['_CREATECONTAINERREQUEST']._serialized_end = 1203
    _globals['_CREATECONTAINERRESPONSE']._serialized_start = 1205
    _globals['_CREATECONTAINERRESPONSE']._serialized_end = 1295
    _globals['_UPDATECONTAINERREQUEST']._serialized_start = 1298
    _globals['_UPDATECONTAINERREQUEST']._serialized_end = 1436
    _globals['_UPDATECONTAINERRESPONSE']._serialized_start = 1438
    _globals['_UPDATECONTAINERRESPONSE']._serialized_end = 1528
    _globals['_DELETECONTAINERREQUEST']._serialized_start = 1530
    _globals['_DELETECONTAINERREQUEST']._serialized_end = 1566
    _globals['_LISTCONTAINERMESSAGE']._serialized_start = 1568
    _globals['_LISTCONTAINERMESSAGE']._serialized_end = 1655
    _globals['_CONTAINERS']._serialized_start = 1658
    _globals['_CONTAINERS']._serialized_end = 2398