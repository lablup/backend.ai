"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.namespaces.v1 import namespace_pb2 as containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/namespaces/v1/namespace_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class NamespacesStub(object):
    """Namespaces provides the ability to manipulate containerd namespaces.

    All objects in the system are required to be a member of a namespace. If a
    namespace is deleted, all objects, including containers, images and
    snapshots, will be deleted, as well.

    Unless otherwise noted, operations in containerd apply only to the namespace
    supplied per request.

    I hope this goes without saying, but namespaces are themselves NOT
    namespaced.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Get = channel.unary_unary('/containerd.services.namespaces.v1.Namespaces/Get', request_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceResponse.FromString, _registered_method=True)
        self.List = channel.unary_unary('/containerd.services.namespaces.v1.Namespaces/List', request_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesResponse.FromString, _registered_method=True)
        self.Create = channel.unary_unary('/containerd.services.namespaces.v1.Namespaces/Create', request_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.namespaces.v1.Namespaces/Update', request_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.services.namespaces.v1.Namespaces/Delete', request_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.DeleteNamespaceRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)

class NamespacesServicer(object):
    """Namespaces provides the ability to manipulate containerd namespaces.

    All objects in the system are required to be a member of a namespace. If a
    namespace is deleted, all objects, including containers, images and
    snapshots, will be deleted, as well.

    Unless otherwise noted, operations in containerd apply only to the namespace
    supplied per request.

    I hope this goes without saying, but namespaces are themselves NOT
    namespaced.
    """

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_NamespacesServicer_to_server(servicer, server):
    rpc_method_handlers = {'Get': grpc.unary_unary_rpc_method_handler(servicer.Get, request_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceRequest.FromString, response_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceResponse.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesRequest.FromString, response_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesResponse.SerializeToString), 'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceRequest.FromString, response_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceRequest.FromString, response_serializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.DeleteNamespaceRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.namespaces.v1.Namespaces', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.namespaces.v1.Namespaces', rpc_method_handlers)

class Namespaces(object):
    """Namespaces provides the ability to manipulate containerd namespaces.

    All objects in the system are required to be a member of a namespace. If a
    namespace is deleted, all objects, including containers, images and
    snapshots, will be deleted, as well.

    Unless otherwise noted, operations in containerd apply only to the namespace
    supplied per request.

    I hope this goes without saying, but namespaces are themselves NOT
    namespaced.
    """

    @staticmethod
    def Get(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.namespaces.v1.Namespaces/Get', containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceRequest.SerializeToString, containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.GetNamespaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.namespaces.v1.Namespaces/List', containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesRequest.SerializeToString, containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.ListNamespacesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.namespaces.v1.Namespaces/Create', containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceRequest.SerializeToString, containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.CreateNamespaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.namespaces.v1.Namespaces/Update', containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceRequest.SerializeToString, containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.UpdateNamespaceResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.namespaces.v1.Namespaces/Delete', containerd_dot_services_dot_namespaces_dot_v1_dot_namespace__pb2.DeleteNamespaceRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)