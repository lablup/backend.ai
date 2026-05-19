"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from google.protobuf import any_pb2 as google_dot_protobuf_dot_any__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/streaming/v1/streaming_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class StreamingStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Stream = channel.stream_stream('/containerd.services.streaming.v1.Streaming/Stream', request_serializer=google_dot_protobuf_dot_any__pb2.Any.SerializeToString, response_deserializer=google_dot_protobuf_dot_any__pb2.Any.FromString, _registered_method=True)

class StreamingServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Stream(self, request_iterator, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_StreamingServicer_to_server(servicer, server):
    rpc_method_handlers = {'Stream': grpc.stream_stream_rpc_method_handler(servicer.Stream, request_deserializer=google_dot_protobuf_dot_any__pb2.Any.FromString, response_serializer=google_dot_protobuf_dot_any__pb2.Any.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.streaming.v1.Streaming', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.streaming.v1.Streaming', rpc_method_handlers)

class Streaming(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Stream(request_iterator, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.stream_stream(request_iterator, target, '/containerd.services.streaming.v1.Streaming/Stream', google_dot_protobuf_dot_any__pb2.Any.SerializeToString, google_dot_protobuf_dot_any__pb2.Any.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)