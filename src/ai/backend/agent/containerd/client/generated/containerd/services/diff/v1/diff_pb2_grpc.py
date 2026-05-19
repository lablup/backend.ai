"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.diff.v1 import diff_pb2 as containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/diff/v1/diff_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class DiffStub(object):
    """Diff service creates and applies diffs
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Apply = channel.unary_unary('/containerd.services.diff.v1.Diff/Apply', request_serializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyResponse.FromString, _registered_method=True)
        self.Diff = channel.unary_unary('/containerd.services.diff.v1.Diff/Diff', request_serializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffResponse.FromString, _registered_method=True)

class DiffServicer(object):
    """Diff service creates and applies diffs
    """

    def Apply(self, request, context):
        """Apply applies the content associated with the provided digests onto
        the provided mounts. Archive content will be extracted and
        decompressed if necessary.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Diff(self, request, context):
        """Diff creates a diff between the given mounts and uploads the result
        to the content store.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_DiffServicer_to_server(servicer, server):
    rpc_method_handlers = {'Apply': grpc.unary_unary_rpc_method_handler(servicer.Apply, request_deserializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyRequest.FromString, response_serializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyResponse.SerializeToString), 'Diff': grpc.unary_unary_rpc_method_handler(servicer.Diff, request_deserializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffRequest.FromString, response_serializer=containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.diff.v1.Diff', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.diff.v1.Diff', rpc_method_handlers)

class Diff(object):
    """Diff service creates and applies diffs
    """

    @staticmethod
    def Apply(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.diff.v1.Diff/Apply', containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyRequest.SerializeToString, containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.ApplyResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Diff(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.diff.v1.Diff/Diff', containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffRequest.SerializeToString, containerd_dot_services_dot_diff_dot_v1_dot_diff__pb2.DiffResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)