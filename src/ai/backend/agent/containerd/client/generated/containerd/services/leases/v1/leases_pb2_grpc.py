"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.leases.v1 import leases_pb2 as containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/leases/v1/leases_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class LeasesStub(object):
    """Leases service manages resources leases within the metadata store.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Create = channel.unary_unary('/containerd.services.leases.v1.Leases/Create', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.services.leases.v1.Leases/Delete', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.List = channel.unary_unary('/containerd.services.leases.v1.Leases/List', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResponse.FromString, _registered_method=True)
        self.AddResource = channel.unary_unary('/containerd.services.leases.v1.Leases/AddResource', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.AddResourceRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.DeleteResource = channel.unary_unary('/containerd.services.leases.v1.Leases/DeleteResource', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteResourceRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.ListResources = channel.unary_unary('/containerd.services.leases.v1.Leases/ListResources', request_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesResponse.FromString, _registered_method=True)

class LeasesServicer(object):
    """Leases service manages resources leases within the metadata store.
    """

    def Create(self, request, context):
        """Create creates a new lease for managing changes to metadata. A lease
        can be used to protect objects from being removed.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Delete(self, request, context):
        """Delete deletes the lease and makes any unreferenced objects created
        during the lease eligible for garbage collection if not referenced
        or retained by other resources during the lease.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """List lists all active leases, returning the full list of
        leases and optionally including the referenced resources.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def AddResource(self, request, context):
        """AddResource references the resource by the provided lease.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def DeleteResource(self, request, context):
        """DeleteResource dereferences the resource by the provided lease.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ListResources(self, request, context):
        """ListResources lists all the resources referenced by the lease.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_LeasesServicer_to_server(servicer, server):
    rpc_method_handlers = {'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateRequest.FromString, response_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListRequest.FromString, response_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResponse.SerializeToString), 'AddResource': grpc.unary_unary_rpc_method_handler(servicer.AddResource, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.AddResourceRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'DeleteResource': grpc.unary_unary_rpc_method_handler(servicer.DeleteResource, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteResourceRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'ListResources': grpc.unary_unary_rpc_method_handler(servicer.ListResources, request_deserializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesRequest.FromString, response_serializer=containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.leases.v1.Leases', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.leases.v1.Leases', rpc_method_handlers)

class Leases(object):
    """Leases service manages resources leases within the metadata store.
    """

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/Create', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateRequest.SerializeToString, containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.CreateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/Delete', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/List', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListRequest.SerializeToString, containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def AddResource(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/AddResource', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.AddResourceRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def DeleteResource(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/DeleteResource', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.DeleteResourceRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ListResources(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.leases.v1.Leases/ListResources', containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesRequest.SerializeToString, containerd_dot_services_dot_leases_dot_v1_dot_leases__pb2.ListResourcesResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)