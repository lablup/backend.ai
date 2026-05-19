"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.services.sandbox.v1 import sandbox_pb2 as containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/services/sandbox/v1/sandbox_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class StoreStub(object):
    """Store provides a metadata storage interface for sandboxes. Similarly to `Containers`,
    sandbox object includes info required to start a new instance, but no runtime state.
    When running a new sandbox instance, store objects are used as base type to create from.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Create = channel.unary_unary('/containerd.services.sandbox.v1.Store/Create', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.sandbox.v1.Store/Update', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.services.sandbox.v1.Store/Delete', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteResponse.FromString, _registered_method=True)
        self.List = channel.unary_unary('/containerd.services.sandbox.v1.Store/List', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListResponse.FromString, _registered_method=True)
        self.Get = channel.unary_unary('/containerd.services.sandbox.v1.Store/Get', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetResponse.FromString, _registered_method=True)

class StoreServicer(object):
    """Store provides a metadata storage interface for sandboxes. Similarly to `Containers`,
    sandbox object includes info required to start a new instance, but no runtime state.
    When running a new sandbox instance, store objects are used as base type to create from.
    """

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

    def List(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Get(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_StoreServicer_to_server(servicer, server):
    rpc_method_handlers = {'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteResponse.SerializeToString), 'List': grpc.unary_unary_rpc_method_handler(servicer.List, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListResponse.SerializeToString), 'Get': grpc.unary_unary_rpc_method_handler(servicer.Get, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.sandbox.v1.Store', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.sandbox.v1.Store', rpc_method_handlers)

class Store(object):
    """Store provides a metadata storage interface for sandboxes. Similarly to `Containers`,
    sandbox object includes info required to start a new instance, but no runtime state.
    When running a new sandbox instance, store objects are used as base type to create from.
    """

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Store/Create', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreCreateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Store/Update', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreUpdateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Store/Delete', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreDeleteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def List(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Store/List', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreListResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Get(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Store/Get', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.StoreGetResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

class ControllerStub(object):
    """Controller is an interface to manage runtime sandbox instances.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.Create = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Create', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateResponse.FromString, _registered_method=True)
        self.Start = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Start', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartResponse.FromString, _registered_method=True)
        self.Platform = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Platform', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformResponse.FromString, _registered_method=True)
        self.Stop = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Stop', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopResponse.FromString, _registered_method=True)
        self.Wait = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Wait', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitResponse.FromString, _registered_method=True)
        self.Status = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Status', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusResponse.FromString, _registered_method=True)
        self.Shutdown = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Shutdown', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownResponse.FromString, _registered_method=True)
        self.Metrics = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Metrics', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsResponse.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.services.sandbox.v1.Controller/Update', request_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateRequest.SerializeToString, response_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateResponse.FromString, _registered_method=True)

class ControllerServicer(object):
    """Controller is an interface to manage runtime sandbox instances.
    """

    def Create(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Start(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Platform(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Stop(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Wait(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Status(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shutdown(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Metrics(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_ControllerServicer_to_server(servicer, server):
    rpc_method_handlers = {'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateResponse.SerializeToString), 'Start': grpc.unary_unary_rpc_method_handler(servicer.Start, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartResponse.SerializeToString), 'Platform': grpc.unary_unary_rpc_method_handler(servicer.Platform, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformResponse.SerializeToString), 'Stop': grpc.unary_unary_rpc_method_handler(servicer.Stop, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopResponse.SerializeToString), 'Wait': grpc.unary_unary_rpc_method_handler(servicer.Wait, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitResponse.SerializeToString), 'Status': grpc.unary_unary_rpc_method_handler(servicer.Status, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusResponse.SerializeToString), 'Shutdown': grpc.unary_unary_rpc_method_handler(servicer.Shutdown, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownResponse.SerializeToString), 'Metrics': grpc.unary_unary_rpc_method_handler(servicer.Metrics, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsResponse.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateRequest.FromString, response_serializer=containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.services.sandbox.v1.Controller', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.services.sandbox.v1.Controller', rpc_method_handlers)

class Controller(object):
    """Controller is an interface to manage runtime sandbox instances.
    """

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Create', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerCreateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Start(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Start', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStartResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Platform(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Platform', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerPlatformResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Stop(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Stop', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStopResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Wait(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Wait', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerWaitResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Status(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Status', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerStatusResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Shutdown(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Shutdown', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerShutdownResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Metrics(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Metrics', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerMetricsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.services.sandbox.v1.Controller/Update', containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateRequest.SerializeToString, containerd_dot_services_dot_sandbox_dot_v1_dot_sandbox__pb2.ControllerUpdateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)