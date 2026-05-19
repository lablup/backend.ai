"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 6, 31, 1, '', 'containerd/services/namespaces/v1/namespace.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n1containerd/services/namespaces/v1/namespace.proto\x12!containerd.services.namespaces.v1\x1a\x1bgoogle/protobuf/empty.proto\x1a google/protobuf/field_mask.proto"\x92\x01\n\tNamespace\x12\x0c\n\x04name\x18\x01 \x01(\t\x12H\n\x06labels\x18\x02 \x03(\x0b28.containerd.services.namespaces.v1.Namespace.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01"#\n\x13GetNamespaceRequest\x12\x0c\n\x04name\x18\x01 \x01(\t"W\n\x14GetNamespaceResponse\x12?\n\tnamespace\x18\x01 \x01(\x0b2,.containerd.services.namespaces.v1.Namespace"\'\n\x15ListNamespacesRequest\x12\x0e\n\x06filter\x18\x01 \x01(\t"Z\n\x16ListNamespacesResponse\x12@\n\nnamespaces\x18\x01 \x03(\x0b2,.containerd.services.namespaces.v1.Namespace"Y\n\x16CreateNamespaceRequest\x12?\n\tnamespace\x18\x01 \x01(\x0b2,.containerd.services.namespaces.v1.Namespace"Z\n\x17CreateNamespaceResponse\x12?\n\tnamespace\x18\x01 \x01(\x0b2,.containerd.services.namespaces.v1.Namespace"\x8a\x01\n\x16UpdateNamespaceRequest\x12?\n\tnamespace\x18\x01 \x01(\x0b2,.containerd.services.namespaces.v1.Namespace\x12/\n\x0bupdate_mask\x18\x02 \x01(\x0b2\x1a.google.protobuf.FieldMask"Z\n\x17UpdateNamespaceResponse\x12?\n\tnamespace\x18\x01 \x01(\x0b2,.containerd.services.namespaces.v1.Namespace"&\n\x16DeleteNamespaceRequest\x12\x0c\n\x04name\x18\x01 \x01(\t2\xe0\x04\n\nNamespaces\x12v\n\x03Get\x126.containerd.services.namespaces.v1.GetNamespaceRequest\x1a7.containerd.services.namespaces.v1.GetNamespaceResponse\x12{\n\x04List\x128.containerd.services.namespaces.v1.ListNamespacesRequest\x1a9.containerd.services.namespaces.v1.ListNamespacesResponse\x12\x7f\n\x06Create\x129.containerd.services.namespaces.v1.CreateNamespaceRequest\x1a:.containerd.services.namespaces.v1.CreateNamespaceResponse\x12\x7f\n\x06Update\x129.containerd.services.namespaces.v1.UpdateNamespaceRequest\x1a:.containerd.services.namespaces.v1.UpdateNamespaceResponse\x12[\n\x06Delete\x129.containerd.services.namespaces.v1.DeleteNamespaceRequest\x1a\x16.google.protobuf.EmptyB.Z,containerd/services/namespaces/v1;namespacesb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'containerd.services.namespaces.v1.namespace_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    _globals['DESCRIPTOR']._loaded_options = None
    _globals['DESCRIPTOR']._serialized_options = b'Z,containerd/services/namespaces/v1;namespaces'
    _globals['_NAMESPACE_LABELSENTRY']._loaded_options = None
    _globals['_NAMESPACE_LABELSENTRY']._serialized_options = b'8\x01'
    _globals['_NAMESPACE']._serialized_start = 152
    _globals['_NAMESPACE']._serialized_end = 298
    _globals['_NAMESPACE_LABELSENTRY']._serialized_start = 253
    _globals['_NAMESPACE_LABELSENTRY']._serialized_end = 298
    _globals['_GETNAMESPACEREQUEST']._serialized_start = 300
    _globals['_GETNAMESPACEREQUEST']._serialized_end = 335
    _globals['_GETNAMESPACERESPONSE']._serialized_start = 337
    _globals['_GETNAMESPACERESPONSE']._serialized_end = 424
    _globals['_LISTNAMESPACESREQUEST']._serialized_start = 426
    _globals['_LISTNAMESPACESREQUEST']._serialized_end = 465
    _globals['_LISTNAMESPACESRESPONSE']._serialized_start = 467
    _globals['_LISTNAMESPACESRESPONSE']._serialized_end = 557
    _globals['_CREATENAMESPACEREQUEST']._serialized_start = 559
    _globals['_CREATENAMESPACEREQUEST']._serialized_end = 648
    _globals['_CREATENAMESPACERESPONSE']._serialized_start = 650
    _globals['_CREATENAMESPACERESPONSE']._serialized_end = 740
    _globals['_UPDATENAMESPACEREQUEST']._serialized_start = 743
    _globals['_UPDATENAMESPACEREQUEST']._serialized_end = 881
    _globals['_UPDATENAMESPACERESPONSE']._serialized_start = 883
    _globals['_UPDATENAMESPACERESPONSE']._serialized_end = 973
    _globals['_DELETENAMESPACEREQUEST']._serialized_start = 975
    _globals['_DELETENAMESPACEREQUEST']._serialized_end = 1013
    _globals['_NAMESPACES']._serialized_start = 1016
    _globals['_NAMESPACES']._serialized_end = 1624