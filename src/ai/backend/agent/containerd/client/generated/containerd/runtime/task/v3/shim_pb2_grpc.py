"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from .....containerd.runtime.task.v3 import shim_pb2 as containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2
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
    raise RuntimeError(f'The grpc package installed is at version {GRPC_VERSION},' + ' but the generated code in containerd/runtime/task/v3/shim_pb2_grpc.py depends on' + f' grpcio>={GRPC_GENERATED_VERSION}.' + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}' + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.')

class TaskStub(object):
    """Shim service is launched for each container and is responsible for owning the IO
    for the container and its additional processes.  The shim is also the parent of
    each container and allows reattaching to the IO and receiving the exit status
    for the container processes.
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.State = channel.unary_unary('/containerd.task.v3.Task/State', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateResponse.FromString, _registered_method=True)
        self.Create = channel.unary_unary('/containerd.task.v3.Task/Create', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskResponse.FromString, _registered_method=True)
        self.Start = channel.unary_unary('/containerd.task.v3.Task/Start', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartResponse.FromString, _registered_method=True)
        self.Delete = channel.unary_unary('/containerd.task.v3.Task/Delete', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteResponse.FromString, _registered_method=True)
        self.Pids = channel.unary_unary('/containerd.task.v3.Task/Pids', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsResponse.FromString, _registered_method=True)
        self.Pause = channel.unary_unary('/containerd.task.v3.Task/Pause', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PauseRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Resume = channel.unary_unary('/containerd.task.v3.Task/Resume', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResumeRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Checkpoint = channel.unary_unary('/containerd.task.v3.Task/Checkpoint', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CheckpointTaskRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Kill = channel.unary_unary('/containerd.task.v3.Task/Kill', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.KillRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Exec = channel.unary_unary('/containerd.task.v3.Task/Exec', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ExecProcessRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.ResizePty = channel.unary_unary('/containerd.task.v3.Task/ResizePty', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResizePtyRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.CloseIO = channel.unary_unary('/containerd.task.v3.Task/CloseIO', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CloseIORequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Update = channel.unary_unary('/containerd.task.v3.Task/Update', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.UpdateTaskRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)
        self.Wait = channel.unary_unary('/containerd.task.v3.Task/Wait', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitResponse.FromString, _registered_method=True)
        self.Stats = channel.unary_unary('/containerd.task.v3.Task/Stats', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsResponse.FromString, _registered_method=True)
        self.Connect = channel.unary_unary('/containerd.task.v3.Task/Connect', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectRequest.SerializeToString, response_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectResponse.FromString, _registered_method=True)
        self.Shutdown = channel.unary_unary('/containerd.task.v3.Task/Shutdown', request_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ShutdownRequest.SerializeToString, response_deserializer=google_dot_protobuf_dot_empty__pb2.Empty.FromString, _registered_method=True)

class TaskServicer(object):
    """Shim service is launched for each container and is responsible for owning the IO
    for the container and its additional processes.  The shim is also the parent of
    each container and allows reattaching to the IO and receiving the exit status
    for the container processes.
    """

    def State(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

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

    def Delete(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Pids(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Pause(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Resume(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Checkpoint(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Kill(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Exec(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ResizePty(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CloseIO(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Update(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Wait(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Stats(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Connect(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Shutdown(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

def add_TaskServicer_to_server(servicer, server):
    rpc_method_handlers = {'State': grpc.unary_unary_rpc_method_handler(servicer.State, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateResponse.SerializeToString), 'Create': grpc.unary_unary_rpc_method_handler(servicer.Create, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskResponse.SerializeToString), 'Start': grpc.unary_unary_rpc_method_handler(servicer.Start, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartResponse.SerializeToString), 'Delete': grpc.unary_unary_rpc_method_handler(servicer.Delete, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteResponse.SerializeToString), 'Pids': grpc.unary_unary_rpc_method_handler(servicer.Pids, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsResponse.SerializeToString), 'Pause': grpc.unary_unary_rpc_method_handler(servicer.Pause, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PauseRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Resume': grpc.unary_unary_rpc_method_handler(servicer.Resume, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResumeRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Checkpoint': grpc.unary_unary_rpc_method_handler(servicer.Checkpoint, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CheckpointTaskRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Kill': grpc.unary_unary_rpc_method_handler(servicer.Kill, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.KillRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Exec': grpc.unary_unary_rpc_method_handler(servicer.Exec, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ExecProcessRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'ResizePty': grpc.unary_unary_rpc_method_handler(servicer.ResizePty, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResizePtyRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'CloseIO': grpc.unary_unary_rpc_method_handler(servicer.CloseIO, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CloseIORequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Update': grpc.unary_unary_rpc_method_handler(servicer.Update, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.UpdateTaskRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString), 'Wait': grpc.unary_unary_rpc_method_handler(servicer.Wait, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitResponse.SerializeToString), 'Stats': grpc.unary_unary_rpc_method_handler(servicer.Stats, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsResponse.SerializeToString), 'Connect': grpc.unary_unary_rpc_method_handler(servicer.Connect, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectRequest.FromString, response_serializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectResponse.SerializeToString), 'Shutdown': grpc.unary_unary_rpc_method_handler(servicer.Shutdown, request_deserializer=containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ShutdownRequest.FromString, response_serializer=google_dot_protobuf_dot_empty__pb2.Empty.SerializeToString)}
    generic_handler = grpc.method_handlers_generic_handler('containerd.task.v3.Task', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('containerd.task.v3.Task', rpc_method_handlers)

class Task(object):
    """Shim service is launched for each container and is responsible for owning the IO
    for the container and its additional processes.  The shim is also the parent of
    each container and allows reattaching to the IO and receiving the exit status
    for the container processes.
    """

    @staticmethod
    def State(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/State', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StateResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Create(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Create', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CreateTaskResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Start(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Start', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StartResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Delete(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Delete', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.DeleteResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Pids(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Pids', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PidsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Pause(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Pause', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.PauseRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Resume(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Resume', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResumeRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Checkpoint(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Checkpoint', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CheckpointTaskRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Kill(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Kill', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.KillRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Exec(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Exec', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ExecProcessRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def ResizePty(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/ResizePty', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ResizePtyRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def CloseIO(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/CloseIO', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.CloseIORequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Update(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Update', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.UpdateTaskRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Wait(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Wait', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.WaitResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Stats(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Stats', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.StatsResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Connect(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Connect', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectRequest.SerializeToString, containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ConnectResponse.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)

    @staticmethod
    def Shutdown(request, target, options=(), channel_credentials=None, call_credentials=None, insecure=False, compression=None, wait_for_ready=None, timeout=None, metadata=None):
        return grpc.experimental.unary_unary(request, target, '/containerd.task.v3.Task/Shutdown', containerd_dot_runtime_dot_task_dot_v3_dot_shim__pb2.ShutdownRequest.SerializeToString, google_dot_protobuf_dot_empty__pb2.Empty.FromString, options, channel_credentials, insecure, call_credentials, compression, wait_for_ready, timeout, metadata, _registered_method=True)