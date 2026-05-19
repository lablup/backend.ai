"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.introspection.v1 import introspection_pb2 as containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/introspection/v1/introspection_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class IntrospectionStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Plugins = channel.unary_unary('/containerd.services.introspection.v1.Introspection/Plugins', request_serializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsResponse.FromString, _registered_method=True)
        self.Server = channel.unary_unary('/containerd.services.introspection.v1.Introspection/Server', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.ServerResponse.FromString, _registered_method=True)
        self.PluginInfo = channel.unary_unary('/containerd.services.introspection.v1.Introspection/PluginInfo', request_serializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoResponse.FromString, _registered_method=True)

class IntrospectionServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Plugins(self, request, context):
        """Plugins returns a list of plugins in containerd.

        Clients can use this to detect features and capabilities when using
        containerd.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Server(self, request, context):
        """Server returns information about the containerd server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PluginInfo(self, request, context):
        """PluginInfo returns information directly from a plugin if the plugin supports it
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_IntrospectionServicer_to_server(servicer, server):
    rpc_method_handlers = {'Plugins': grpc.unary_unary_rpc_method_handler(servicer.Plugins, request_deserializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsRequest.FromString, response_serializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsResponse.SerializeToString), 'Server': grpc.unary_unary_rpc_method_handler(servicer.Server, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.ServerResponse.SerializeToString), 'PluginInfo': grpc.unary_unary_rpc_method_handler(servicer.PluginInfo, request_deserializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoRequest.FromString, response_serializer=containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.introspection.v1.Introspection', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.introspection.v1.Introspection', rpc_method_handlers)

class Introspection(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Plugins(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.introspection.v1.Introspection/Plugins', containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsRequest.SerializeToString, containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Server(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.introspection.v1.Introspection/Server', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.ServerResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def PluginInfo(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.introspection.v1.Introspection/PluginInfo', containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoRequest.SerializeToString, containerd_dot_services_dot_introspection_dot_v1_dot_introspection__pb2.PluginInfoResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)