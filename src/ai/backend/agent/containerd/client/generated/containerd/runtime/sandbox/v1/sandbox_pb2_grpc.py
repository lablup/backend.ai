"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.runtime.sandbox.v1 import sandbox_pb2 as containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2
GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False
try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True
if _version_not_supported:
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/runtime/sandbox/v1/sandbox_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class SandboxStub(object):
    """Sandbox is an optional interface that shim may implement to support sandboxes environments.
    A typical example of sandbox is microVM or pause container - an entity that groups containers and/or
    holds resources relevant for this group.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreateSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/CreateSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxResponse.FromString, _registered_method=True)
        self.StartSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/StartSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxResponse.FromString, _registered_method=True)
        self.Platform = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/Platform', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformResponse.FromString, _registered_method=True)
        self.StopSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/StopSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxResponse.FromString, _registered_method=True)
        self.WaitSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/WaitSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxResponse.FromString, _registered_method=True)
        self.SandboxStatus = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/SandboxStatus', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusResponse.FromString, _registered_method=True)
        self.PingSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/PingSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingResponse.FromString, _registered_method=True)
        self.ShutdownSandbox = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/ShutdownSandbox', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxResponse.FromString, _registered_method=True)
        self.SandboxMetrics = channel.unary_unary('/containerd.runtime.sandbox.v1.Sandbox/SandboxMetrics', request_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsResponse.FromString, _registered_method=True)

class SandboxServicer(object):
    """Sandbox is an optional interface that shim may implement to support sandboxes environments.
    A typical example of sandbox is microVM or pause container - an entity that groups containers and/or
    holds resources relevant for this group.
    """

    def CreateSandbox(self, request, context):
        """CreateSandbox will be called right after sandbox shim instance launched.
        It is a good place to initialize sandbox environment.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartSandbox(self, request, context):
        """StartSandbox will start a previously created sandbox.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Platform(self, request, context):
        """Platform queries the platform the sandbox is going to run containers on.
        containerd will use this to generate a proper OCI spec.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StopSandbox(self, request, context):
        """StopSandbox will stop existing sandbox instance
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def WaitSandbox(self, request, context):
        """WaitSandbox blocks until sandbox exits.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SandboxStatus(self, request, context):
        """SandboxStatus will return current status of the running sandbox instance
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def PingSandbox(self, request, context):
        """PingSandbox is a lightweight API call to check whether sandbox alive.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ShutdownSandbox(self, request, context):
        """ShutdownSandbox must shutdown shim instance.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SandboxMetrics(self, request, context):
        """SandboxMetrics retrieves metrics about a sandbox instance.
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_SandboxServicer_to_server(servicer, server):
    rpc_method_handlers = {'CreateSandbox': grpc.unary_unary_rpc_method_handler(servicer.CreateSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxResponse.SerializeToString), 'StartSandbox': grpc.unary_unary_rpc_method_handler(servicer.StartSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxResponse.SerializeToString), 'Platform': grpc.unary_unary_rpc_method_handler(servicer.Platform, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformResponse.SerializeToString), 'StopSandbox': grpc.unary_unary_rpc_method_handler(servicer.StopSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxResponse.SerializeToString), 'WaitSandbox': grpc.unary_unary_rpc_method_handler(servicer.WaitSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxResponse.SerializeToString), 'SandboxStatus': grpc.unary_unary_rpc_method_handler(servicer.SandboxStatus, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusResponse.SerializeToString), 'PingSandbox': grpc.unary_unary_rpc_method_handler(servicer.PingSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingResponse.SerializeToString), 'ShutdownSandbox': grpc.unary_unary_rpc_method_handler(servicer.ShutdownSandbox, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxResponse.SerializeToString), 'SandboxMetrics': grpc.unary_unary_rpc_method_handler(servicer.SandboxMetrics, request_deserializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsRequest.FromString, response_serializer=containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsResponse.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.runtime.sandbox.v1.Sandbox', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.runtime.sandbox.v1.Sandbox', rpc_method_handlers)

class Sandbox(object):
    """Sandbox is an optional interface that shim may implement to support sandboxes environments.
    A typical example of sandbox is microVM or pause container - an entity that groups containers and/or
    holds resources relevant for this group.
    """

    @staticmethod
    def CreateSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/CreateSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.CreateSandboxResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def StartSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/StartSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StartSandboxResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Platform(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/Platform', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PlatformResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def StopSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/StopSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.StopSandboxResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def WaitSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/WaitSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.WaitSandboxResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SandboxStatus(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/SandboxStatus', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxStatusResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def PingSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/PingSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.PingResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ShutdownSandbox(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/ShutdownSandbox', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.ShutdownSandboxResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def SandboxMetrics(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.runtime.sandbox.v1.Sandbox/SandboxMetrics', containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsRequest.SerializeToString, containerd_dot_runtime_dot_sandbox_dot_v1_dot_sandbox__pb2.SandboxMetricsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)