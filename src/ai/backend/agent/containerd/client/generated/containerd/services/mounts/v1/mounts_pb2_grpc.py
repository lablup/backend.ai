"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.mounts.v1 import mounts_pb2 as containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/mounts/v1/mounts_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class MountsStub(object):
    """Mounts service manages mounts
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Activate = channel.unary_unary('/containerd.services.mounts.v1.Mounts/Activate', request_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateResponse.FromString, _registered_method=True)
        self.Deactivate = channel.unary_unary('/containerd.services.mounts.v1.Mounts/Deactivate', request_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.DeactivateRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Info = channel.unary_unary('/containerd.services.mounts.v1.Mounts/Info', request_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.mounts.v1.Mounts/Update', request_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateResponse.FromString, _registered_method=True)
        self.List = channel.unary_stream('/containerd.services.mounts.v1.Mounts/List', request_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListMessage.FromString, _registered_method=True)

class MountsServicer(object):
    """Mounts service manages mounts
    """

    def Activate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Deactivate(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Info(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_MountsServicer_to_server(servicer, server):
    rpc_method_handlers = {'Activate': grpc.unary_unary_rpc_method_handler(servicer.Activate, request_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateRequest.FromString, response_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateResponse.SerializeToString), 'Deactivate': grpc.unary_unary_rpc_method_handler(servicer.Deactivate, request_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.DeactivateRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Info': grpc.unary_unary_rpc_method_handler(servicer.Info, request_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoRequest.FromString, response_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateRequest.FromString, response_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateResponse.SerializeToString), 'List': grpc.unary_stream_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListRequest.FromString, response_serializer=containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListMessage.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.mounts.v1.Mounts', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.mounts.v1.Mounts', rpc_method_handlers)

class Mounts(object):
    """Mounts service manages mounts
    """

    @staticmethod
    def Activate(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.mounts.v1.Mounts/Activate', containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateRequest.SerializeToString, containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ActivateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Deactivate(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.mounts.v1.Mounts/Deactivate', containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.DeactivateRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Info(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.mounts.v1.Mounts/Info', containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoRequest.SerializeToString, containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.InfoResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.mounts.v1.Mounts/Update', containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateRequest.SerializeToString, containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.UpdateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_stream(request, target, '/containerd.services.mounts.v1.Mounts/List', containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListRequest.SerializeToString, containerd_dot_services_dot_mounts_dot_v1_dot_mounts__pb2.ListMessage.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)