"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.events.v1 import events_pb2 as containerd_dot_services_dot_events_dot_v1_dot_events__pb2
from .....containerd.types import event_pb2 as containerd_dot_types_dot_event__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/events/v1/events_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class EventsStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Publish = channel.unary_unary('/containerd.services.events.v1.Events/Publish', request_serializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.PublishRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Forward = channel.unary_unary('/containerd.services.events.v1.Events/Forward', request_serializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.ForwardRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Subscribe = channel.unary_stream('/containerd.services.events.v1.Events/Subscribe', request_serializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.SubscribeRequest.SerializeToString, response_deserializer=containerd_dot_types_dot_event__pb2.Envelope.FromString, _registered_method=True)

class EventsServicer(object):
    """Missing associated documentation comment in .proto file."""

    def Publish(self, request, context):
        """Publish an event to a topic.

        The event will be packed into a timestamp envelope with the namespace
        introspected from the context. The envelope will then be dispatched.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Forward(self, request, context):
        """Forward sends an event that has already been packaged into an envelope
        with a timestamp and namespace.

        This is useful if earlier timestamping is required or when forwarding on
        behalf of another component, namespace or publisher.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Subscribe(self, request, context):
        """Subscribe to a stream of events, possibly returning only that match any
        of the provided filters.

        Unlike many other methods in containerd, subscribers will get messages
        from all namespaces unless otherwise specified. If this is not desired,
        a filter can be provided in the format 'namespace==<namespace>' to
        restrict the received events.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_EventsServicer_to_server(servicer, server):
    rpc_method_handlers = {'Publish': grpc.unary_unary_rpc_method_handler(servicer.Publish, request_deserializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.PublishRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Forward': grpc.unary_unary_rpc_method_handler(servicer.Forward, request_deserializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.ForwardRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Subscribe': grpc.unary_stream_rpc_method_handler(servicer.Subscribe, request_deserializer=containerd_dot_services_dot_events_dot_v1_dot_events__pb2.SubscribeRequest.FromString, response_serializer=containerd_dot_types_dot_event__pb2.Envelope.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.events.v1.Events', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.events.v1.Events', rpc_method_handlers)

class Events(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def Publish(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.events.v1.Events/Publish', containerd_dot_services_dot_events_dot_v1_dot_events__pb2.PublishRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Forward(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.events.v1.Events/Forward', containerd_dot_services_dot_events_dot_v1_dot_events__pb2.ForwardRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Subscribe(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/containerd.services.events.v1.Events/Subscribe', containerd_dot_services_dot_events_dot_v1_dot_events__pb2.SubscribeRequest.SerializeToString, containerd_dot_types_dot_event__pb2.Envelope.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)