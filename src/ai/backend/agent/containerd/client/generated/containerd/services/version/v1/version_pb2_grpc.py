"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.version.v1 import version_pb2 as containerd_dot_services_dot_version_dot_v1_dot_version__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/version/v1/version_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class VersionStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Version = channel.unary_unary('/containerd.services.version.v1.Version/Version', request_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, response_deserializer=containerd_dot_services_dot_version_dot_v1_dot_version__pb2.VersionResponse.FromString, _registered_method=True)

class VersionServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Version(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_VersionServicer_to_server(servicer, server):
    rpc_method_handlers = {'Version': grpc.unary_unary_rpc_method_handler(servicer.Version, request_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, response_serializer=containerd_dot_services_dot_version_dot_v1_dot_version__pb2.VersionResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.version.v1.Version', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.version.v1.Version', rpc_method_handlers)

class Version(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Version(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.version.v1.Version/Version', google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString, containerd_dot_services_dot_version_dot_v1_dot_version__pb2.VersionResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)